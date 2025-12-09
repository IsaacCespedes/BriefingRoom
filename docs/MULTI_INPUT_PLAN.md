# Plan: Multiple Input Formats for Job Descriptions and Resumes

## Executive Summary

This document outlines the plan to extend the application's input capabilities from plain text only to supporting multiple formats:
- **Document Formats:** PDF, DOC, DOCX
- **Web Links:** Job posting URLs, LinkedIn profile URLs
- **Plain Text:** Existing textarea input (maintained)

## Current State Analysis

### Existing Implementation
- **Input Method:** Two `<textarea>` elements (job description and resume)
- **Storage:** Raw text stored in Supabase `interviews` table (`job_description`, `resume_text` columns)
- **Processing:** CrewAI agents analyze plain text to generate interview briefings
- **Validation:** Basic presence validation only (Pydantic + HTML5 required)
- **Files:**
  - Frontend form: `frontend/src/routes/+page.svelte` (lines 96-133)
  - Backend API: `backend/app/api/interviews.py` (POST `/api/interviews`)
  - Database operations: `backend/app/db.py`
  - Models: `backend/app/models/interview.py`

### Limitations
1. Users must manually copy/paste resume text (tedious for long documents)
2. No support for formatted documents (PDF, Word)
3. Cannot automatically extract data from job posting URLs
4. Cannot scrape LinkedIn profiles
5. No file upload UI/infrastructure
6. No document parsing libraries integrated

---

## Proposed Architecture

### 1. Frontend Changes

#### 1.1 Enhanced Input Component
Create a flexible input component that supports multiple modes:

**File:** `frontend/src/lib/components/MultiInput.svelte`

**Features:**
- **Tab/Toggle Interface:**
  - "Plain Text" tab (default, existing behavior)
  - "Upload File" tab (PDF, DOC, DOCX)
  - "From URL" tab (job posting links, LinkedIn)

- **File Upload:**
  - Drag-and-drop zone
  - File type validation (client-side)
  - File size limits (e.g., 10MB max)
  - Visual feedback (filename, file size, upload progress)
  - Multiple file formats: `.pdf`, `.doc`, `.docx`

- **URL Input:**
  - Text input for URLs
  - URL validation (regex for valid HTTP/HTTPS)
  - Special handling for LinkedIn URLs
  - Domain whitelist/blacklist (optional security feature)
  - Link preview (optional enhancement)

**Component Props:**
```typescript
{
  fieldName: string;        // "job_description" or "resume_text"
  label: string;            // Display label
  required: boolean;        // Required field
  onContentReady: (content: string, metadata: object) => void;
}
```

#### 1.2 Update Main Form
**File:** `frontend/src/routes/+page.svelte`

- Replace existing textareas with `<MultiInput>` components
- Handle file uploads and URL submissions
- Display loading states during file parsing/URL scraping
- Show extracted text preview before submission
- Error handling for failed uploads/parsing

#### 1.3 File Upload API Client
**File:** `frontend/src/lib/api/upload.ts`

**Functions:**
- `uploadDocument(file: File): Promise<{text: string, metadata: object}>`
- `extractFromUrl(url: string): Promise<{text: string, metadata: object}>`
- Handle multipart/form-data requests
- Progress tracking callbacks

---

### 2. Backend Changes

#### 2.1 Document Parsing Service
**File:** `backend/app/services/document_parser.py`

**Responsibilities:**
- Parse PDF files → extract text
- Parse DOC/DOCX files → extract text
- Handle malformed/encrypted documents
- Return structured data (text + metadata)

**Libraries to Integrate:**
- **PDF:** `PyPDF2` or `pdfplumber` (better for complex layouts)
- **Word:** `python-docx` (DOCX) and `python-docx2txt` (DOC)
- **Alternative:** `apache-tika` (unified parser, requires Java)

**API:**
```python
def parse_pdf(file: UploadFile) -> DocumentParseResult:
    """Extract text from PDF file."""

def parse_docx(file: UploadFile) -> DocumentParseResult:
    """Extract text from DOCX file."""

def parse_doc(file: UploadFile) -> DocumentParseResult:
    """Extract text from legacy DOC file."""

@dataclass
class DocumentParseResult:
    text: str
    metadata: dict  # filename, page_count, file_size, parse_method
    warnings: list  # parsing issues, encrypted sections, etc.
```

#### 2.2 Web Scraping Service
**File:** `backend/app/services/web_scraper.py`

**Responsibilities:**
- Fetch and parse job posting URLs
- Extract LinkedIn profile data (with limitations - see questions below)
- Clean HTML → extract meaningful text
- Handle rate limiting, timeouts, redirects
- Respect robots.txt

**Libraries to Integrate:**
- **HTTP Client:** `httpx` (async support)
- **HTML Parsing:** `beautifulsoup4` or `lxml`
- **LinkedIn:** Special consideration (see Outstanding Questions)
- **Readability:** `readability-lxml` (extract main content from web pages)

**API:**
```python
async def scrape_job_posting(url: str) -> WebScrapeResult:
    """Scrape job description from URL."""

async def scrape_linkedin_profile(url: str) -> WebScrapeResult:
    """Scrape LinkedIn profile (with limitations)."""

@dataclass
class WebScrapeResult:
    text: str
    metadata: dict  # url, title, source, scrape_timestamp
    warnings: list  # access denied, incomplete data, etc.
```

**Challenges:**
- Dynamic content (JavaScript-rendered pages) → may need Playwright/Selenium
- Anti-scraping measures (Cloudflare, captchas)
- LinkedIn specifically blocks scraping (see questions)
- Privacy concerns with scraping personal profiles

#### 2.3 File Upload Endpoint
**File:** `backend/app/api/upload.py`

**Endpoints:**
```python
@router.post("/api/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    field_type: str = Form(...)  # "job_description" or "resume"
) -> UploadResponse:
    """
    Accept file upload, parse it, return extracted text.

    Validations:
    - File size limit (10MB)
    - File type whitelist (.pdf, .doc, .docx)
    - Virus scanning (optional, see questions)

    Returns:
    - extracted_text: str
    - metadata: dict
    - warnings: list
    """

@router.post("/api/upload/from-url")
async def extract_from_url(
    url: HttpUrl,
    field_type: str
) -> UploadResponse:
    """
    Fetch and parse content from URL.

    Validations:
    - URL format
    - Domain whitelist (optional)
    - Timeout limits (30 seconds)

    Returns:
    - extracted_text: str
    - metadata: dict
    - warnings: list
    """
```

**Security Considerations:**
- File size limits to prevent DoS
- File type validation (magic bytes, not just extension)
- Sandboxed parsing (prevent code execution)
- Rate limiting on URL scraping
- Input sanitization (XSS prevention)

#### 2.4 Update Interview Models
**File:** `backend/app/models/interview.py`

**Add Optional Metadata Fields:**
```python
class InterviewCreate(InterviewBase):
    job_description: str
    resume_text: str
    job_description_metadata: Optional[dict] = None  # source, filename, url, etc.
    resume_metadata: Optional[dict] = None           # source, filename, url, etc.
```

**Database Schema Update:**
Consider adding metadata columns to `interviews` table:
```sql
ALTER TABLE interviews
ADD COLUMN job_description_source VARCHAR(50),  -- "text", "pdf", "docx", "url"
ADD COLUMN job_description_metadata JSONB,
ADD COLUMN resume_source VARCHAR(50),
ADD COLUMN resume_metadata JSONB;
```

---

### 3. Database Changes

#### 3.1 Migration
**File:** `backend/migrations/003_add_input_metadata.sql`

```sql
-- Add source tracking and metadata
ALTER TABLE interviews
ADD COLUMN job_description_source VARCHAR(50) DEFAULT 'text',
ADD COLUMN job_description_metadata JSONB,
ADD COLUMN resume_source VARCHAR(50) DEFAULT 'text',
ADD COLUMN resume_metadata JSONB;

-- Add indexes for querying by source type
CREATE INDEX idx_interviews_jd_source ON interviews(job_description_source);
CREATE INDEX idx_interviews_resume_source ON interviews(resume_source);
```

#### 3.2 File Storage (Optional)
**Question:** Should we store original uploaded files?

**Options:**
1. **Store text only** (current approach, simpler)
   - Pros: No file storage needed, smaller database
   - Cons: Cannot regenerate text if parsing improves

2. **Store original files in Supabase Storage**
   - Pros: Can reprocess files, audit trail, download originals
   - Cons: Storage costs, complexity, security concerns

**If storing files:**
- Use Supabase Storage buckets
- Bucket structure: `uploads/{interview_id}/{field_type}/{filename}`
- File retention policy (e.g., delete after 30 days)
- Access control (private buckets, signed URLs)

---

### 4. Testing Requirements

#### 4.1 Backend Tests

**File:** `backend/tests/test_document_parser.py`
- Test PDF parsing (various PDF versions)
- Test DOCX parsing
- Test DOC parsing (legacy format)
- Test encrypted/password-protected files (should fail gracefully)
- Test corrupted files (error handling)
- Test multi-page documents
- Test documents with images/tables (text extraction quality)
- Test file size limits

**File:** `backend/tests/test_web_scraper.py`
- Test job posting URL scraping (Indeed, LinkedIn Jobs, Glassdoor, etc.)
- Test LinkedIn profile URLs (or mock if blocked)
- Test malformed URLs
- Test timeout handling
- Test rate limiting
- Test robots.txt compliance
- Mock HTTP responses for deterministic tests

**File:** `backend/tests/test_upload_api.py`
- Test file upload endpoint (multipart/form-data)
- Test file type validation
- Test file size limits
- Test URL extraction endpoint
- Test authentication/authorization
- Test error responses (422, 413, 500)

#### 4.2 Frontend Tests

**File:** `frontend/src/lib/components/MultiInput.test.ts`
- Test tab switching
- Test file selection/drag-and-drop
- Test file type validation
- Test URL input validation
- Test loading states
- Test error display
- Test content preview

#### 4.3 Integration Tests

**File:** `backend/tests/integration/test_interview_creation_with_uploads.py`
- End-to-end test: upload PDF → create interview → verify data
- End-to-end test: provide URL → create interview → verify data
- Test mixed inputs (PDF job description + plain text resume)

#### 4.4 Manual Testing Checklist
- [ ] Upload small PDF resume (< 1MB)
- [ ] Upload large PDF resume (5-10MB)
- [ ] Upload DOCX with formatting (bold, lists, tables)
- [ ] Upload legacy DOC file
- [ ] Paste Indeed job posting URL
- [ ] Paste LinkedIn job posting URL
- [ ] Paste LinkedIn profile URL (if supported)
- [ ] Paste generic company career page URL
- [ ] Test with slow network (loading states)
- [ ] Test with invalid file types (.exe, .jpg)
- [ ] Test with oversized files (>10MB)
- [ ] Test with malformed URLs
- [ ] Test with inaccessible URLs (404, 403)

---

### 5. Error Handling & User Experience

#### 5.1 Error Scenarios

| Scenario | User-Facing Message | Technical Action |
|----------|---------------------|------------------|
| Invalid file type | "Please upload a PDF or Word document (.pdf, .doc, .docx)" | Client-side validation, reject upload |
| File too large | "File size must be under 10MB" | Client-side check, backend validation |
| Corrupted file | "Could not read file. Please try a different format." | Log error, suggest alternatives |
| Encrypted PDF | "This PDF is password-protected. Please provide an unlocked version." | Detect encryption, return 422 |
| URL timeout | "Could not load the page. Please check the URL or try plain text." | 30s timeout, fallback suggestion |
| LinkedIn blocked | "LinkedIn profiles cannot be automatically imported. Please copy/paste." | Detect domain, show helpful message |
| Parsing failed | "Could not extract text. You can paste the text manually instead." | Fallback to plain text input |

#### 5.2 Loading States
- File upload progress bar
- "Parsing document..." spinner
- "Loading page..." for URL extraction
- Estimated time remaining (for large files)

#### 5.3 Preview & Confirmation
- Show extracted text in expandable preview
- Allow user to edit extracted text before submission
- Display metadata (filename, page count, source URL)
- "Use this text" vs "Cancel" buttons

---

## Outstanding Questions

### Technical Questions

1. **LinkedIn Scraping:**
   - **Question:** LinkedIn actively blocks scraping and requires authentication. Should we:
     - A) Remove LinkedIn profile support from scope?
     - B) Use LinkedIn API (requires partnership, complex OAuth)?
     - C) Instruct users to copy/paste from LinkedIn (manual process)?
   - **Recommendation:** Option C (manual copy/paste) with clear instructions. LinkedIn API is overkill for this use case.

2. **Dynamic Content:**
   - **Question:** Many modern job boards render content with JavaScript. Should we:
     - A) Use headless browser (Playwright) for scraping (slower, resource-intensive)?
     - B) Use static HTML parsing (faster, but misses dynamic content)?
     - C) Start with static, add Playwright for specific domains if needed?
   - **Recommendation:** Option C. Start simple, iterate based on user feedback.

3. **File Storage:**
   - **Question:** Should we store original uploaded files or just extracted text?
   - **Trade-offs:**
     - Store files: Audit trail, reprocessing, but costs money and adds complexity
     - Text only: Simpler, cheaper, but cannot regenerate if parsing improves
   - **Recommendation:** Start with text only. Add file storage later if needed for compliance/audit.

4. **File Size Limits:**
   - **Question:** What's the maximum file size?
   - **Considerations:**
     - 10MB should cover most resumes/job descriptions
     - Larger files slow down parsing and increase server load
     - Backend timeout limits (default 30s for FastAPI)
   - **Recommendation:** 10MB limit, with option to adjust based on actual usage.

5. **Virus Scanning:**
   - **Question:** Should we scan uploaded files for malware?
   - **Options:**
     - A) Use ClamAV (open-source, requires installation/maintenance)
     - B) Use cloud service (VirusTotal API, AWS Macie)
     - C) Skip virus scanning (rely on file type validation + sandboxing)
   - **Recommendation:** Option C for MVP. Add scanning if handling sensitive enterprise data.

6. **Document Parsing Library:**
   - **Question:** Which library for document parsing?
   - **Options:**
     - A) Individual libraries (PyPDF2, python-docx) - lightweight, Python-native
     - B) Apache Tika (unified parser) - comprehensive, but requires Java runtime
     - C) Cloud services (AWS Textract, Google Document AI) - best quality, but costs money
   - **Recommendation:** Option A for MVP (PyPDF2, python-docx). Evaluate Tika if text extraction quality is poor.

7. **Rate Limiting:**
   - **Question:** How to prevent abuse of URL scraping?
   - **Options:**
     - Per-IP rate limiting (e.g., 10 URLs per hour)
     - Per-user rate limiting (requires authentication)
     - No rate limiting (trust users, monitor for abuse)
   - **Recommendation:** Per-IP rate limiting using FastAPI middleware. Start with 20 URLs/hour.

### UX/Product Questions

8. **Input Switching:**
   - **Question:** Can users switch between input methods (e.g., upload PDF, then switch to plain text)?
   - **Recommendation:** Yes, allow switching with a warning: "This will discard your current input. Continue?"

9. **Mixed Inputs:**
   - **Question:** Can users upload a PDF for resume but paste text for job description?
   - **Recommendation:** Yes, each field supports all input methods independently.

10. **Edit After Upload:**
    - **Question:** Can users edit extracted text before submitting?
    - **Recommendation:** Yes, show extracted text in editable preview. Critical for correcting parsing errors.

11. **Failed Parsing Fallback:**
    - **Question:** What if document parsing fails completely?
    - **Recommendation:** Show error message with option to switch to plain text input. Don't block the user.

12. **Privacy Notice:**
    - **Question:** Should we display a privacy notice for URL scraping (data leaves the server)?
    - **Recommendation:** Yes, brief notice: "We'll fetch this page to extract text. Public pages only."

13. **Supported Job Boards:**
    - **Question:** Which job board domains should we explicitly support/test?
    - **Recommendation:** Start with common ones:
      - Indeed (indeed.com)
      - LinkedIn Jobs (linkedin.com/jobs)
      - Glassdoor (glassdoor.com)
      - Company career pages (various)
    - Display warning for unknown domains: "We'll try to extract text from this page."

### Deployment Questions

14. **Dependency Installation:**
    - **Question:** How to handle new Python dependencies in Docker?
    - **Action Required:** Update `backend/requirements.txt` and rebuild Docker image.

15. **Storage Configuration:**
    - **Question:** If storing files, do we need to configure Supabase Storage buckets?
    - **Action Required:** (If storing files) Create `interview-uploads` bucket with private access.

16. **Environment Variables:**
    - **Question:** Any new env vars needed?
    - **Possibilities:**
      - `MAX_UPLOAD_SIZE_MB=10`
      - `URL_SCRAPING_TIMEOUT_SECONDS=30`
      - `RATE_LIMIT_URLS_PER_HOUR=20`
      - `ENABLE_VIRUS_SCANNING=false`

---

## Implementation Phases

### Phase 1: PDF Upload Support (MVP)
**Goal:** Users can upload PDF resumes instead of copy/paste.

**Scope:**
- Frontend: File upload UI for resume field only
- Backend: PDF parsing endpoint (PyPDF2 or pdfplumber)
- API: POST `/api/upload/document` endpoint
- Testing: Basic PDF parsing tests
- **Duration Estimate:** ~1-2 weeks (design, implement, test)

**Deliverables:**
- [ ] `MultiInput.svelte` component with file upload tab
- [ ] `document_parser.py` with PDF support
- [ ] Upload API endpoint
- [ ] Integration with interview creation flow
- [ ] Unit tests and integration tests
- [ ] User documentation

### Phase 2: Word Document Support
**Goal:** Support DOC/DOCX files for resumes.

**Scope:**
- Backend: Add DOCX parser (python-docx)
- Backend: Add legacy DOC parser (if needed)
- Testing: Word document parsing tests
- **Duration Estimate:** ~3-5 days

**Deliverables:**
- [ ] DOCX parsing in `document_parser.py`
- [ ] DOC parsing (if feasible)
- [ ] Updated tests
- [ ] Updated UI (accept .docx/.doc file types)

### Phase 3: Job Posting URL Support
**Goal:** Users can paste job posting URLs.

**Scope:**
- Frontend: URL input tab
- Backend: Web scraping service (httpx + BeautifulSoup)
- Backend: POST `/api/upload/from-url` endpoint
- Rate limiting middleware
- Testing: URL scraping tests (mocked HTTP responses)
- **Duration Estimate:** ~1-2 weeks

**Deliverables:**
- [ ] URL input UI in `MultiInput.svelte`
- [ ] `web_scraper.py` service
- [ ] URL extraction endpoint
- [ ] Rate limiting implementation
- [ ] Tests for various job board formats
- [ ] Documentation for supported domains

### Phase 4: Both Fields + Polish
**Goal:** Support all input methods for both job description and resume.

**Scope:**
- Extend upload/URL support to job description field
- Enhanced UX: previews, edit before submit, loading states
- Error handling improvements
- Database metadata tracking
- Documentation updates
- **Duration Estimate:** ~1 week

**Deliverables:**
- [ ] Both fields support all input methods
- [ ] Text preview and editing UI
- [ ] Database migration for metadata columns
- [ ] Comprehensive error messages
- [ ] User guide with screenshots
- [ ] Admin documentation

### Phase 5: Advanced Features (Optional)
**Goal:** Enhancements based on user feedback.

**Scope (pick based on priority):**
- LinkedIn profile manual import guide (not automated)
- Dynamic content scraping (Playwright for JavaScript-heavy pages)
- File storage in Supabase Storage (audit trail)
- Virus scanning (ClamAV integration)
- Advanced parsing (Apache Tika for better quality)
- Structured data extraction (skills, experience years, etc.)
- **Duration Estimate:** TBD based on selected features

---

## Security Checklist

- [ ] File type validation (magic bytes check, not just extension)
- [ ] File size limits enforced on both frontend and backend
- [ ] Sandboxed document parsing (no code execution)
- [ ] Input sanitization for extracted text (prevent XSS)
- [ ] Rate limiting for URL scraping
- [ ] Timeout limits for web requests (prevent hanging)
- [ ] Robots.txt compliance for web scraping
- [ ] HTTPS-only URLs for scraping (no HTTP to prevent MITM)
- [ ] Error messages don't leak system internals
- [ ] Logging for security events (large files, unusual URLs, parsing failures)
- [ ] Content Security Policy (CSP) headers
- [ ] CORS configuration (restrict file upload origins)

---

## Dependencies to Add

### Python (Backend)
```
# Document parsing
PyPDF2>=3.0.0           # PDF parsing
pdfplumber>=0.10.0      # Alternative PDF parser (better text extraction)
python-docx>=1.0.0      # DOCX parsing

# Web scraping
httpx>=0.25.0           # Async HTTP client
beautifulsoup4>=4.12.0  # HTML parsing
lxml>=4.9.0             # XML/HTML parser (BeautifulSoup backend)
readability-lxml>=0.8.0 # Extract main content from web pages

# File handling
python-multipart>=0.0.6 # Required for FastAPI file uploads (if not already present)

# Optional (future enhancements)
# apache-tika>=2.9.0    # Unified document parser (requires Java)
# playwright>=1.40.0     # Headless browser for dynamic content
```

### JavaScript (Frontend)
```json
// File upload UI
"@uppy/core": "^3.0.0",         // File upload library (optional, if using Uppy)
"@uppy/drag-drop": "^3.0.0",
"@uppy/progress-bar": "^3.0.0",

// Or use native file input with these utilities:
"file-type": "^18.0.0",         // Client-side file type detection
"pretty-bytes": "^6.0.0"        // Display file sizes nicely
```

**Note:** SvelteKit has built-in form handling, so external upload libraries may be unnecessary. Evaluate based on desired UX.

---

## Documentation to Create/Update

1. **User Guide:**
   - `docs/USER_GUIDE.md` (update with new input methods)
   - Screenshots of file upload UI
   - Instructions for each input method
   - Supported file formats and size limits
   - Troubleshooting common errors

2. **API Documentation:**
   - `docs/API.md` (add upload endpoints)
   - Request/response examples for file uploads
   - URL extraction endpoint documentation
   - Error codes and meanings

3. **Developer Guide:**
   - `docs/DEVELOPER_GUIDE.md` (update with new services)
   - Document parser architecture
   - Web scraper implementation notes
   - How to add support for new file types
   - How to add support for new job boards

4. **Architecture Diagrams:**
   - `docs/diagrams/component-diagram.md` (add upload flow)
   - `docs/diagrams/sequence-diagram.md` (add upload/parse sequence)
   - `docs/diagrams/erd.md` (update with metadata columns)

5. **Testing Guide:**
   - `docs/TESTING.md` (add manual test cases for uploads)
   - Sample test files (PDF, DOCX) in `backend/tests/fixtures/`

---

## Success Metrics

### Functional Metrics
- [ ] PDF upload success rate > 95%
- [ ] DOCX upload success rate > 95%
- [ ] URL scraping success rate > 80% (varies by domain)
- [ ] Average file parsing time < 5 seconds
- [ ] Average URL scraping time < 10 seconds

### User Experience Metrics
- [ ] Reduced time to create interview (less copy/paste)
- [ ] User error rate (file upload errors, parsing failures)
- [ ] Feature adoption rate (% using uploads vs plain text)

### Technical Metrics
- [ ] Test coverage > 80% for new code
- [ ] No security vulnerabilities introduced
- [ ] API response time < 3 seconds (95th percentile)
- [ ] Server CPU/memory within acceptable limits

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Poor PDF text extraction quality | High | Medium | Use pdfplumber (better extraction), allow manual editing |
| LinkedIn blocks scraping | Medium | High | Remove LinkedIn scraping from scope, provide manual instructions |
| File upload DoS attack | High | Low | File size limits, rate limiting, monitoring |
| XSS via extracted text | High | Low | Sanitize all extracted text, use CSP headers |
| Slow parsing for large files | Medium | Medium | Timeout limits, background processing (future enhancement) |
| Dynamic content not scraped | Medium | Medium | Start with static parsing, add Playwright if needed |
| Users upload wrong files | Low | High | Clear UI labels, file type validation, preview before submit |
| Parsing errors cause confusion | Medium | Medium | Clear error messages, fallback to plain text |

---

## Summary

This plan transforms the application from a plain-text-only interface to a flexible multi-format input system. The phased approach allows for incremental development and testing, starting with the highest-value feature (PDF resumes) and expanding to other formats and URL scraping.

**Key Design Principles:**
1. **User-friendly:** Simple interface with clear feedback
2. **Flexible:** Support multiple input methods per field
3. **Resilient:** Graceful error handling, fallback to plain text
4. **Secure:** Validation, rate limiting, sandboxing
5. **Maintainable:** Modular services, comprehensive tests

**Next Steps:**
1. Review and approve this plan
2. Clarify outstanding questions (see section above)
3. Set up development environment with new dependencies
4. Begin Phase 1 implementation (PDF uploads)
5. Iterate based on user feedback

---

## Appendix: Technology Alternatives Considered

### Document Parsing
- **PyPDF2:** Simple, pure Python, good for basic PDFs
- **pdfplumber:** Better text extraction for complex layouts, tables
- **Apache Tika:** Comprehensive (supports 100+ formats), but requires Java
- **AWS Textract:** Best quality, but costs $1.50 per 1000 pages
- **Decision:** Start with PyPDF2/pdfplumber, evaluate Tika if quality issues arise

### Web Scraping
- **requests + BeautifulSoup:** Simple, good for static HTML
- **httpx + BeautifulSoup:** Async support, better for performance
- **Scrapy:** Full framework, overkill for this use case
- **Playwright/Selenium:** Handles JavaScript, but slow and resource-intensive
- **Decision:** httpx + BeautifulSoup, add Playwright for specific domains if needed

### Frontend File Upload
- **Native HTML input:** Simple, built-in, no dependencies
- **Uppy:** Feature-rich (drag-drop, progress, thumbnails), but adds 100KB+
- **react-dropzone:** Popular, but we're using Svelte
- **Decision:** Start with native HTML5, enhance with custom Svelte component

### Backend Framework
- **FastAPI:** Already in use, excellent for file uploads (multipart/form-data)
- **No change needed**

---

**Document Version:** 1.0
**Date:** 2025-12-09
**Author:** AI Planning Agent
**Status:** Draft - Awaiting Review
