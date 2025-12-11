# Emotion Detection Integration - Feasibility Analysis
**Date**: December 9, 2025
**Author**: Technical Analysis
**Status**: Research & Recommendation
---
## Executive Summary
This document analyzes the feasibility of integrating emotion detection capabilities similar to the [EmoVision Chrome Extension](https://github.com/Jordan-Townsend/emovision-chrome-extension) into the Bionic Interviewer application. The analysis covers technical approaches, implementation complexity, and recommendations.
**Recommendation**: ✅ **FEASIBLE** - Emotion detection integration is technically viable with moderate complexity. A custom implementation using face-api.js or similar libraries is recommended over direct integration of the Chrome extension.
---
## Table of Contents
1. [EmoVision Analysis](#emovision-analysis)
2. [Current System Context](#current-system-context)
3. [Integration Approaches](#integration-approaches)
4. [Technical Implementation Details](#technical-implementation-details)
5. [Complexity Assessment](#complexity-assessment)
6. [Recommendations](#recommendations)
7. [Outstanding Questions](#outstanding-questions)
8. [Next Steps](#next-steps)
---
## EmoVision Analysis
### Overview
**EmoVision** is a Chrome extension that performs real-time emotion detection on video calls (Google Meet, Zoom, Microsoft Teams, YouTube, Twitch).
### Key Features
- **Performance**: Real-time processing at 10 FPS with <100ms latency
- **Privacy**: 100% client-side processing (no server required)
- **Multi-face Detection**: Can detect emotions on multiple faces simultaneously
- **Display**: Shows emotion badges above detected faces
### Technology Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| ML Framework | TensorFlow.js | Browser-based machine learning inference |
| Face Detection | face-api.js | Facial recognition and emotion classification |
| Body Language | pose-detection.min.js | Posture and body language analysis |
| Platform | Chrome Extension APIs | Browser integration and video stream access |
### Emotion Detection Models
EmoVision uses face-api.js, which includes:
- **faceExpressionNet**: Neural network for emotion classification
- **Multiple detection models**: SSD MobileNetV1, Tiny Face Detector, MTCNN
- **7 emotion states**: Typically detects happy, sad, angry, surprised, disgusted, fearful, neutral
- **Additional features**: Age estimation, gender prediction, facial landmarks
### Performance Characteristics
- **Frame Rate**: 10 FPS (100ms per frame)
- **Latency**: <100ms processing time
- **Resource Usage**: Client-side only (uses browser CPU/GPU)
- **Accuracy**: Not specified in documentation, but face-api.js models are pre-trained
### Limitations of Direct Integration
1. **Chrome Extension Format**: Designed specifically for browser extensions, not web applications
2. **No API Exposure**: Does not provide REST API or SDK for external integration
3. **Content Script Architecture**: Uses Chrome extension content scripts to inject into web pages
4. **Limited Documentation**: Minimal API documentation or integration guidelines
5. **Repository Access**: Unable to access full source code for detailed analysis
---
## Current System Context
### Existing Video Infrastructure
The Bionic Interviewer already has robust video call capabilities:
#### Daily.co Integration
- **Current Status**: ✅ Fully implemented
- **Location**: `backend/app/api/daily.py`, `frontend/src/lib/daily.ts`
- **Features**:
  - Room creation and management
  - Meeting token generation
  - Screen sharing and chat enabled
  - WebRTC-based video/audio
#### System Architecture
- **Frontend**: SvelteKit with TypeScript
- **Backend**: FastAPI (Python)
- **Video SDK**: Daily.co Web SDK (`@daily-co/daily-js` v0.83.1)
- **Use Case**: Interview hosts conduct video interviews with candidates
### Daily.co Capabilities Relevant to Emotion Detection
Daily.co provides access to:
- **Video tracks**: Raw video streams from participants
- **Canvas API**: Ability to process video frames
- **Events**: Participant join/leave, track start/stop
- **Participant metadata**: Can attach custom data to participants
---
## Integration Approaches
### Approach 1: Custom Browser-Based Implementation ⭐ RECOMMENDED
**Description**: Build a custom emotion detection feature using face-api.js or TensorFlow.js directly in the Bionic Interviewer frontend.
#### Architecture
```
Daily.co Video Stream
    ↓
Video Frame Extraction (Canvas API)
    ↓
face-api.js / TensorFlow.js Processing
    ↓
Emotion Detection Results
    ↓
UI Display + Backend Storage
```
#### Implementation Components
1. **Frontend Processing Module** (SvelteKit)
   - Load face-api.js models (weights ~6-10MB)
   - Extract video frames from Daily.co participant tracks
   - Process frames at configurable FPS (5-10 FPS)
   - Display emotion overlays on video interface
   - Send emotion data to backend for storage
2. **Backend Storage & Analytics** (FastAPI)
   - New endpoint: `POST /api/emotions/record`
   - Store emotion timeline in database
   - Generate emotion analytics reports
   - Privacy controls for emotion data
3. **Database Schema**
   ```sql
   CREATE TABLE emotion_detections (
       id UUID PRIMARY KEY,
       interview_id UUID REFERENCES interviews(id),
       participant_role TEXT, -- 'host' or 'candidate'
       timestamp TIMESTAMP,
       emotions JSONB, -- {happy: 0.8, neutral: 0.2, ...}
       PRIMARY KEY (id)
   );
   ```
#### Pros
- ✅ Full control over implementation
- ✅ Integrates seamlessly with existing architecture
- ✅ Can customize emotion detection for interview context
- ✅ Privacy-first: processing happens client-side
- ✅ No external dependencies or Chrome extension required
- ✅ Can be deployed as part of main web application
#### Cons
- ❌ Requires custom development (estimated 20-40 hours)
- ❌ Need to load ML models (~6-10MB) on client
- ❌ Ongoing maintenance of emotion detection logic
- ❌ Performance depends on client device capabilities
#### Estimated Complexity: **MODERATE**
---
### Approach 2: Third-Party Emotion Detection API
**Description**: Use a cloud-based emotion detection service (e.g., Azure Face API, AWS Rekognition, Affectiva).
#### Architecture
```
Daily.co Video Stream
    ↓
Frame Capture on Client
    ↓
Send Frames to Backend
    ↓
Backend → Third-Party API
    ↓
Emotion Results → Backend → Frontend
```
#### Pros
- ✅ No ML model maintenance
- ✅ Professional-grade accuracy
- ✅ Potentially better models than open-source
- ✅ Less client-side compute required
#### Cons
- ❌ Privacy concerns (sending video frames to third parties)
- ❌ Ongoing API costs (per API call)
- ❌ Network latency reduces real-time performance
- ❌ Vendor lock-in
- ❌ Requires uploading sensitive interview video frames
#### Estimated Complexity: **LOW-MODERATE**
**Recommendation**: ❌ **NOT RECOMMENDED** due to privacy concerns for interview context
---
### Approach 3: Server-Side ML Processing
**Description**: Run emotion detection models on the backend server using Python ML libraries.
#### Architecture
```
Daily.co Video Stream
    ↓
WebRTC Server-Side Recording
    ↓
Python Backend (OpenCV + TensorFlow)
    ↓
Emotion Detection
    ↓
Results → Frontend via WebSocket
```
#### Pros
- ✅ Centralized processing
- ✅ No client performance impact
- ✅ Can use more powerful models
#### Cons
- ❌ Requires server GPU/compute resources
- ❌ Higher infrastructure costs
- ❌ Increased server load
- ❌ Network bandwidth for video streaming to server
- ❌ More complex deployment (GPU support)
#### Estimated Complexity: **HIGH**
**Recommendation**: ⚠️ **POSSIBLE** but not cost-effective for initial implementation
---
### Approach 4: Chrome Extension Integration (Direct)
**Description**: Require users to install the EmoVision Chrome extension alongside the web app.
#### Pros
- ✅ Pre-built solution
- ✅ No development required
#### Cons
- ❌ Requires users to install separate Chrome extension
- ❌ No integration with Bionic Interviewer UI
- ❌ Cannot store emotion data in application database
- ❌ No control over features or customization
- ❌ Fragmented user experience
- ❌ Only works in Chrome (not Firefox, Safari, mobile)
#### Estimated Complexity: **VERY LOW**
**Recommendation**: ❌ **NOT RECOMMENDED** - Poor user experience and no integration
---
## Technical Implementation Details
### Recommended Approach Deep Dive: Custom Browser-Based Implementation
#### Technology Selection
**Option A: face-api.js (Updated Fork)** ⭐ RECOMMENDED
- **Library**: [vladmandic/face-api](https://github.com/vladmandic/face-api)
- **Version**: Compatible with TensorFlow.js 4.x
- **Size**: ~6-10MB models
- **Performance**: Optimized for browser, supports WebGL acceleration
- **Features**: Emotion detection, age/gender estimation, face landmarks
- **Installation**: `npm install @vladmandic/face-api`
**Option B: TensorFlow.js with Custom Models**
- **Library**: [tensorflow/tfjs](https://github.com/tensorflow/tfjs)
- **Model**: Would need to source emotion detection model separately
- **Size**: Varies by model
- **Flexibility**: More control but more complexity
#### Implementation Phases
##### Phase 1: Proof of Concept (8-12 hours)
**Deliverables**:
1. Load face-api.js in SvelteKit frontend
2. Extract video frames from Daily.co participant track
3. Run emotion detection on frames
4. Display detected emotions in console
**Files to Create**:
- `frontend/src/lib/emotionDetection.ts` - Core emotion detection logic
- `frontend/src/lib/components/EmotionOverlay.svelte` - UI component
**Code Sketch**:
```typescript
// frontend/src/lib/emotionDetection.ts
import * as faceapi from '@vladmandic/face-api';
export class EmotionDetector {
  private isModelLoaded = false;
  async loadModels() {
    const MODEL_URL = '/models'; // Serve from public directory
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
    await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL);
    this.isModelLoaded = true;
  }
  async detectEmotions(videoElement: HTMLVideoElement) {
    if (!this.isModelLoaded) throw new Error('Models not loaded');
    const detections = await faceapi
      .detectAllFaces(videoElement, new faceapi.TinyFaceDetectorOptions())
      .withFaceExpressions();
    return detections.map(d => ({
      box: d.detection.box,
      emotions: d.expressions
    }));
  }
}
```
##### Phase 2: UI Integration (6-10 hours)
**Deliverables**:
1. Emotion overlay component on video interface
2. Real-time emotion display during calls
3. User settings to enable/disable emotion detection
4. Privacy consent flow
**UI Mockup**:
```
┌─────────────────────────────────┐
│   Candidate Video               │
│                                 │
│   😊 Happy (78%)                │ ← Emotion Badge
│                                 │
└─────────────────────────────────┘
```
##### Phase 3: Backend Integration (6-10 hours)
**Deliverables**:
1. API endpoint to store emotion data
2. Database migration for emotion_detections table
3. Privacy controls and data retention policies
4. Analytics/reporting endpoints
**Files to Create**:
- `backend/app/api/emotions.py` - Emotion API endpoints
- `backend/app/migrations/xxx_add_emotions_table.sql` - Database migration
**API Design**:
```python
# POST /api/emotions/record
{
  "interview_id": "uuid",
  "participant_role": "candidate",
  "timestamp": "2025-12-09T10:30:00Z",
  "emotions": {
    "happy": 0.78,
    "neutral": 0.15,
    "surprised": 0.07
  }
}
```
##### Phase 4: Analytics & Reporting (8-12 hours)
**Deliverables**:
1. Emotion timeline visualization
2. Aggregate emotion statistics
3. Export emotion data with interview notes
4. Privacy-preserving analytics
#### Performance Optimization
1. **Frame Rate Control**: Process 5-10 FPS (not every frame)
2. **Model Selection**: Use Tiny Face Detector for speed
3. **WebGL Acceleration**: Leverage TensorFlow.js WebGL backend
4. **Lazy Loading**: Load models only when user enables emotion detection
5. **Worker Threads**: Consider using Web Workers for processing (Phase 2 enhancement)
#### Privacy & Ethical Considerations
1. **Informed Consent**: Both host and candidate must consent to emotion detection
2. **Data Minimization**: Store only aggregate emotion scores, not video frames
3. **User Control**: Allow users to disable emotion detection at any time
4. **Transparency**: Clearly indicate when emotion detection is active
5. **Data Retention**: Implement automatic deletion policies
6. **Bias Awareness**: Document limitations and potential biases in emotion detection
---
## Complexity Assessment
### Development Effort Estimate
| Phase | Description | Estimated Hours |
|-------|-------------|----------------|
| **Phase 1** | Proof of Concept | 8-12 hours |
| **Phase 2** | UI Integration | 6-10 hours |
| **Phase 3** | Backend Integration | 6-10 hours |
| **Phase 4** | Analytics & Reporting | 8-12 hours |
| **Testing & Polish** | QA, bug fixes, optimization | 8-16 hours |
| **Total** | | **36-60 hours** |
### Complexity Factors
| Factor | Rating | Notes |
|--------|--------|-------|
| ML Model Integration | 🟡 Moderate | Libraries are mature but require learning |
| Video Frame Extraction | 🟢 Low | Daily.co SDK provides straightforward access |
| Real-time Performance | 🟡 Moderate | Need to optimize for 10 FPS processing |
| UI/UX Design | 🟢 Low | Simple overlay design |
| Backend Integration | 🟢 Low | Standard REST API patterns |
| Privacy & Compliance | 🟠 Moderate-High | Requires careful handling |
| Testing & QA | 🟡 Moderate | Need to test across devices/browsers |
**Overall Complexity**: 🟡 **MODERATE**
---
## Recommendations
### Primary Recommendation: Custom Browser-Based Implementation
**Verdict**: ✅ **PROCEED with Approach 1**
#### Why This Approach?
1. **Best Fit for Use Case**: Interview context requires privacy and customization
2. **Technical Alignment**: Works seamlessly with existing Daily.co integration
3. **Privacy-First**: All processing stays client-side
4. **Cost-Effective**: No ongoing API costs
5. **Flexible**: Can customize for interview-specific insights
#### Implementation Roadmap
**Sprint 1 (Week 1-2): Proof of Concept**
- Load face-api.js models
- Extract Daily.co video frames
- Basic emotion detection
- Console output of emotions
- **Deliverable**: Working prototype
**Sprint 2 (Week 3): UI Integration**
- Emotion overlay component
- Real-time display during calls
- User settings panel
- **Deliverable**: User-facing feature
**Sprint 3 (Week 4): Backend & Analytics**
- API endpoints for emotion storage
- Database schema migration
- Basic analytics dashboard
- **Deliverable**: Complete feature with data persistence
**Sprint 4 (Week 5): Polish & Launch**
- Privacy consent flows
- Performance optimization
- Cross-browser testing
- Documentation
- **Deliverable**: Production-ready feature
### Alternative Recommendation: Phased Approach
If resources are limited, consider a **Minimum Viable Product (MVP)** approach:
**MVP (1-2 weeks, 16-24 hours)**:
- Emotion detection on candidate video only
- Simple emotion badge display (no historical data)
- No backend storage initially
- Manual enable/disable toggle
**Post-MVP Enhancements**:
- Backend storage and analytics
- Emotion timeline visualization
- Multi-participant detection
- Advanced reporting
---
## Outstanding Questions
### Technical Questions
1. **Model Selection**:
   - Q: Which face detection model provides the best speed/accuracy tradeoff?
   - A: Recommend starting with Tiny Face Detector for speed, can upgrade to SSD MobileNet if accuracy is insufficient
2. **Frame Rate**:
   - Q: What frame rate is optimal for interview emotion detection?
   - A: Recommend 5 FPS initially, can increase to 10 FPS if performance allows
3. **Multi-Face Handling**:
   - Q: Should we detect emotions for both host and candidate?
   - A: Yes, but prioritize candidate detection first (host can enable their own detection)
4. **Model Storage**:
   - Q: Where should face-api.js models be hosted?
   - A: Serve from `/public/models` directory in frontend, or from CDN for production
### Product Questions
1. **Privacy & Consent**:
   - Q: Should emotion detection be opt-in or opt-out?
   - **Recommendation**: Opt-in for candidates, host decision for their own feed
2. **Data Retention**:
   - Q: How long should emotion data be stored?
   - **Recommendation**: Default 30 days, configurable, with automatic deletion
3. **Candidate Visibility**:
   - Q: Should candidates see their own emotion detection results?
   - **Recommendation**: No by default (to avoid anxiety), but could be a post-interview feature
4. **Host Dashboard**:
   - Q: What emotion insights are most valuable to hosts?
   - **Recommendation**:
     - Real-time: Current dominant emotion
     - Post-interview: Emotion timeline, engagement score, moments of interest
5. **Use Case Prioritization**:
   - Q: What's the primary value proposition?
   - **Options**:
     a. Help host gauge candidate engagement
     b. Post-interview analytics
     c. Training tool for interviewers
   - **Recommendation**: Start with (a), expand to (b) and (c)
### Ethical & Legal Questions
1. **Regulatory Compliance**:
   - Q: What are the legal implications of emotion detection in interviews?
   - **Action Required**: Consult legal team, especially for:
     - GDPR compliance (EU)
     - CCPA compliance (California)
     - Employment law considerations
2. **Bias & Fairness**:
   - Q: How do we address potential bias in emotion detection models?
   - **Recommendation**:
     - Disclose model limitations in documentation
     - Do not use emotion data for automated hiring decisions
     - Provide training to hosts on interpretation
3. **Informed Consent**:
   - Q: What level of disclosure is required?
   - **Recommendation**: Clear, explicit consent with:
     - Explanation of what data is collected
     - How it's used and stored
     - Right to decline or revoke
---
## Next Steps
### Immediate Actions (Before Development)
1. **Stakeholder Validation**
   - [ ] Present this analysis to product team
   - [ ] Confirm value proposition and use cases
   - [ ] Validate privacy and ethical approach
2. **Legal Review**
   - [ ] Consult legal team on employment law implications
   - [ ] Review GDPR/CCPA compliance requirements
   - [ ] Draft consent forms and privacy disclosures
3. **Technical Validation**
   - [ ] Create quick prototype (4-8 hours) to validate feasibility
   - [ ] Test face-api.js performance on target devices
   - [ ] Measure model load time and processing latency
### Development Kickoff (If Approved)
1. **Sprint Planning**
   - Allocate 36-60 hours over 4-5 weeks
   - Assign frontend + backend developer
   - Schedule design review for emotion overlay UI
2. **Environment Setup**
   - Add face-api.js to frontend dependencies
   - Download and host ML models
   - Set up development environment
3. **Documentation**
   - Create user-facing documentation on emotion detection
   - Draft privacy policy addendum
   - Create developer documentation for emotion detection module
---
## References & Sources
### Research Sources
- [GitHub - justadudewhohacks/face-api.js: JavaScript API for face detection and face recognition](https://github.com/justadudewhohacks/face-api.js)
- [GitHub - vladmandic/face-api: FaceAPI with updated TensorFlow.js](https://github.com/vladmandic/face-api)
- [face-api.js Official Documentation](https://justadudewhohacks.github.io/face-api.js/docs/index.html)
- [Pre-Trained AI Emotion Detection With face-api and Tensorflow.js - CodeProject](https://www.codeproject.com/Articles/5276822/Pre-Trained-AI-Emotion-Detection-With-face-api-and)
- [FAQ: Emotion Recognition in Video Conferencing – How Does It Work?](https://www.forasoft.com/blog/article/emotion-recognition-video-conferencing)
- [Daily.co: Realtime voice, video, and AI for developers](https://www.daily.co/)
- [Top 30 Affective Computing Applications: Emotion AI Use Cases](https://research.aimultiple.com/affective-computing-applications/)
- [Tavus: Conversational video AI with built-in emotion detection](https://www.tavus.io/post/conversational-video-ai-emotion-detection)
### Related Documentation
- [Vapi Integration Summary](./vapi-integration-summary.md) - Voice AI integration
- [Daily.co Setup Guide](./daily-setup.md) - Video call infrastructure
- [System Architecture](./architecture.md) - Overall system design
---
## Appendix: Alternative Technologies Considered
### Other ML Libraries
1. **ml5.js**
   - Pros: Simpler API than TensorFlow.js
   - Cons: Less mature emotion detection models
2. **MediaPipe (Google)**
   - Pros: High performance, production-ready
   - Cons: Larger bundle size, more complex
3. **clmtrackr**
   - Pros: Lightweight
   - Cons: Less accurate, older library
**Conclusion**: face-api.js (vladmandic fork) offers the best balance of accuracy, performance, and ease of integration.
---
**Document Version**: 1.0
**Last Updated**: December 9, 2025
**Next Review**: After stakeholder validation