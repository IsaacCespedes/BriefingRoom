# Manual Testing Guide: Multi-Input Feature

This guide provides step-by-step instructions for manually testing the multi-input feature for job descriptions and resumes.

## Prerequisites

1. **Start the services:**
   ```bash
   # From project root
   docker-compose up -d
   ```

2. **Verify services are running:**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - Check backend health: http://localhost:8000/api/health

3. **Environment variables:**
   - Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
   - Ensure `OPENAI_API_KEY` is set (for CrewAI)

4. **Test files ready:**
   - Create a test PDF resume (or use an existing one)
   - Create a test DOCX resume (or use an existing one)
   - Have a job posting URL ready (e.g., from Indeed, Glassdoor)

---

## Test Scenarios

### 1. Plain Text Input (Backward Compatibility)

**Goal:** Verify existing text-based functionality still works.

**Steps:**
1. Navigate to http://localhost:5173
2. Ensure you're on the "Plain Text" tab for both fields
3. Enter job description in the textarea
4. Enter resume text in the textarea
5. Click "Create Interview"
6. Verify interview is created successfully
7. Verify tokens are generated

**Expected Result:**
- Interview created with `job_description_source: "text"` and `resume_source: "text"`
- Both fields stored as plain text in database
- Tokens generated and displayed

---

### 2. PDF File Upload - Resume

**Goal:** Test PDF file upload for resume field.

**Steps:**
1. Navigate to http://localhost:5173
2. For "Candidate Resume":
   - Click "Upload File" tab
   - Drag and drop a PDF file OR click "Select File" and choose a PDF
3. For "Job Description":
   - Keep on "Plain Text" tab
   - Enter job description text
4. Verify file is displayed with filename and size
5. Click "Create Interview"
6. Check browser network tab for multipart/form-data request
7. Verify interview is created

**Expected Result:**
- File appears in UI with filename and size
- Interview created with `resume_source: "file"`
- File uploaded to Supabase Storage bucket `interview-files`
- File path stored in `resume_path` column
- Metadata stored in `resume_metadata` JSONB column

**Verify in Database:**
```sql
SELECT 
  id,
  resume_source,
  resume_path,
  resume_metadata
FROM interviews
ORDER BY created_at DESC
LIMIT 1;
```

**Verify in Supabase Storage:**
- Go to Supabase Dashboard → Storage → `interview-files` bucket
- Check that file exists at path: `{interview_id}/resume/{filename}`

---

### 3. DOCX File Upload - Resume

**Goal:** Test DOCX file upload for resume field.

**Steps:**
1. Navigate to http://localhost:5173
2. For "Candidate Resume":
   - Click "Upload File" tab
   - Upload a `.docx` file
3. For "Job Description":
   - Keep on "Plain Text" tab
   - Enter job description text
4. Click "Create Interview"
5. Verify interview is created

**Expected Result:**
- DOCX file accepted and uploaded
- Interview created with `resume_source: "file"`
- File stored in Supabase Storage

---

### 4. PDF File Upload - Job Description

**Goal:** Test PDF file upload for job description field.

**Steps:**
1. Navigate to http://localhost:5173
2. For "Job Description":
   - Click "Upload File" tab
   - Upload a PDF file
3. For "Candidate Resume":
   - Keep on "Plain Text" tab
   - Enter resume text
4. Click "Create Interview"
5. Verify interview is created

**Expected Result:**
- PDF file uploaded for job description
- Interview created with `job_description_source: "file"`

---

### 5. URL Input - Job Description

**Goal:** Test URL input for job posting.

**Steps:**
1. Navigate to http://localhost:5173
2. For "Job Description":
   - Click "From URL" tab
   - Enter a job posting URL (e.g., from Indeed, Glassdoor)
   - Example: `https://www.indeed.com/viewjob?jk=...`
3. For "Candidate Resume":
   - Keep on "Plain Text" tab
   - Enter resume text
4. Click "Create Interview"
5. Verify interview is created

**Expected Result:**
- URL accepted
- Interview created with `job_description_source: "url"`
- URL stored in `job_description_path` column
- Metadata stored with domain information

**Verify in Database:**
```sql
SELECT 
  id,
  job_description_source,
  job_description_path,
  job_description_metadata
FROM interviews
ORDER BY created_at DESC
LIMIT 1;
```

---

### 6. LinkedIn URL Warning

**Goal:** Verify LinkedIn URLs show warning message.

**Steps:**
1. Navigate to http://localhost:5173
2. For "Job Description" or "Candidate Resume":
   - Click "From URL" tab
   - Enter a LinkedIn URL: `https://www.linkedin.com/jobs/view/...`
3. Verify warning message appears
4. (Optional) Try to submit - should still work but with warning

**Expected Result:**
- Yellow warning box appears: "Note: LinkedIn profiles cannot be automatically imported..."
- URL is still accepted (backend will store it)
- Metadata includes `is_linkedin: true`

---

### 7. Mixed Input Types

**Goal:** Test different input types for each field.

**Steps:**
1. Navigate to http://localhost:5173
2. For "Job Description":
   - Upload a PDF file
3. For "Candidate Resume":
   - Enter a URL
4. Click "Create Interview"
5. Verify interview is created

**Expected Result:**
- Both fields accept different input types
- Interview created with mixed sources

---

### 8. File Validation - Invalid File Type

**Goal:** Test file type validation.

**Steps:**
1. Navigate to http://localhost:5173
2. Click "Upload File" tab
3. Try to upload an invalid file (e.g., `.jpg`, `.exe`, `.txt`)
4. Verify error message appears

**Expected Result:**
- Error message: "Please upload a PDF or Word document (.pdf, .doc, .docx)"
- File is rejected
- Interview cannot be created

---

### 9. File Validation - File Size Limit

**Goal:** Test file size validation (10MB limit).

**Steps:**
1. Create or find a file larger than 10MB
2. Navigate to http://localhost:5173
3. Try to upload the large file
4. Verify error message appears

**Expected Result:**
- Error message: "File size must be under 10MB"
- File is rejected

---

### 10. URL Validation - Invalid URL

**Goal:** Test URL format validation.

**Steps:**
1. Navigate to http://localhost:5173
2. Click "From URL" tab
3. Enter invalid URL (e.g., "not-a-url", "ftp://example.com")
4. Try to submit

**Expected Result:**
- Backend should validate and reject invalid URLs
- Error message displayed

---

### 11. Tab Switching with Content

**Goal:** Test tab switching behavior.

**Steps:**
1. Navigate to http://localhost:5173
2. Enter text in "Plain Text" tab
3. Try to switch to "Upload File" tab
4. Verify confirmation dialog appears
5. Confirm switch
6. Verify previous content is cleared

**Expected Result:**
- Confirmation dialog: "Switching tabs will discard your current input. Continue?"
- Content cleared after confirmation

---

### 12. Drag and Drop

**Goal:** Test drag-and-drop file upload.

**Steps:**
1. Navigate to http://localhost:5173
2. Click "Upload File" tab
3. Drag a PDF file from your file system into the drop zone
4. Verify file is accepted and displayed

**Expected Result:**
- Drop zone highlights when dragging over
- File is accepted on drop
- File information displayed

---

### 13. Remove Uploaded File

**Goal:** Test removing an uploaded file.

**Steps:**
1. Upload a file
2. Click the "X" button to remove the file
3. Verify file is removed
4. Verify you can upload a different file

**Expected Result:**
- File removed from UI
- Can upload new file

---

### 14. Backend API - JSON Request (Backward Compatibility)

**Goal:** Test JSON API endpoint still works.

**Steps:**
```bash
curl -X POST http://localhost:8000/api/interviews \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Test job description",
    "resume_text": "Test resume text",
    "status": "pending"
  }'
```

**Expected Result:**
- Interview created successfully
- Returns `interview_id`, `host_token`, `candidate_token`

---

### 15. Backend API - Multipart Request (File Upload)

**Goal:** Test multipart/form-data endpoint.

**Steps:**
```bash
curl -X POST http://localhost:8000/api/interviews \
  -F "job_description_text=Test job description" \
  -F "job_description_type=text" \
  -F "resume_text=@/path/to/resume.pdf" \
  -F "resume_type=file" \
  -F "status=pending"
```

**Expected Result:**
- File uploaded successfully
- Interview created with file path

---

### 16. CrewAI Integration - File Processing

**Goal:** Verify CrewAI agents can process uploaded files.

**Steps:**
1. Create an interview with a PDF resume
2. Wait for briefing generation (if automatic) OR trigger manually
3. Check CrewAI logs for tool usage
4. Verify briefing is generated with content from PDF

**Expected Result:**
- CrewAI agents use PDFSearchTool to extract text
- Briefing contains information from the PDF

**Check Logs:**
- Look for CrewAI verbose output showing tool usage
- Verify agents are calling PDFSearchTool or DOCXSearchTool

---

### 17. Database Verification

**Goal:** Verify all data is stored correctly.

**Steps:**
```sql
-- Check latest interview
SELECT 
  id,
  job_description_source,
  resume_source,
  job_description_path,
  resume_path,
  job_description_metadata,
  resume_metadata,
  created_at
FROM interviews
ORDER BY created_at DESC
LIMIT 5;
```

**Expected Result:**
- All source types correctly stored
- File paths/URLs stored in path columns
- Metadata JSONB contains file information

---

### 18. Supabase Storage Verification

**Goal:** Verify files are stored in Supabase Storage.

**Steps:**
1. Go to Supabase Dashboard
2. Navigate to Storage → `interview-files` bucket
3. Check file structure: `{interview_id}/{field_type}/{filename}`
4. Verify files are accessible

**Expected Result:**
- Files organized by interview ID
- Files accessible via signed URLs

---

## Error Scenarios to Test

### 1. Empty Fields
- Try to submit without any input
- Should show validation error

### 2. Network Issues
- Disconnect network during file upload
- Should show error message

### 3. Corrupted File
- Try to upload a corrupted PDF
- Should handle gracefully

### 4. Very Long URLs
- Enter extremely long URL
- Should validate and handle appropriately

---

## Checklist

- [ ] Plain text input works
- [ ] PDF upload works (resume)
- [ ] PDF upload works (job description)
- [ ] DOCX upload works
- [ ] URL input works
- [ ] LinkedIn URL shows warning
- [ ] Mixed input types work
- [ ] File validation (type) works
- [ ] File validation (size) works
- [ ] URL validation works
- [ ] Tab switching works
- [ ] Drag and drop works
- [ ] Remove file works
- [ ] JSON API works (backward compatibility)
- [ ] Multipart API works
- [ ] Database stores correctly
- [ ] Supabase Storage stores files
- [ ] CrewAI processes files correctly

---

## Troubleshooting

### Files not uploading
- Check Supabase Storage bucket exists: `interview-files`
- Check bucket permissions (should be private)
- Check file size limits
- Check network connectivity

### CrewAI not processing files
- Verify `OPENAI_API_KEY` is set
- Check CrewAI logs for errors
- Verify tools are imported correctly
- Check file paths are accessible to CrewAI

### Database errors
- Verify migration was applied: `20240103000000_add_input_metadata.sql`
- Check column types match
- Verify JSONB columns accept metadata

---

## Next Steps After Testing

1. **If all tests pass:** Feature is ready for production
2. **If issues found:** Document issues and fix before deployment
3. **Performance testing:** Test with large files (close to 10MB limit)
4. **Load testing:** Test multiple concurrent uploads

---

## Notes

- All file uploads are stored in Supabase Storage
- Signed URLs are generated with 24-hour expiration
- CrewAI agents extract text asynchronously during briefing generation
- No pre-extraction step needed - agents handle it
