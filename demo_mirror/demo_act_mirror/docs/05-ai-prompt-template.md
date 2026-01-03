# AI Prompt Template: Elderly Care Solutions Platform

**Document Version**: 1.0
**Last Updated**: January 2025
**Purpose**: Standardized prompts for AI agent interactions

---

## Overview

This document provides standardized prompt templates for interacting with AI agents (Claude, GPT-4, etc.) throughout the Elderly Care Solutions Platform development lifecycle.

### Prompt Engineering Principles

1. **Be Specific**: Clear, unambiguous instructions
2. **Provide Context**: Relevant background information
3. **Define Output Format**: Specify expected format (code, markdown, JSON)
4. **Include Examples**: Show expected output
5. **Set Constraints**: What to avoid, limitations, boundaries
6. **Iterate**: Refine prompts based on results

---

## 1. Architecture and Design Prompts

### Prompt 1.1: System Architecture Design

```
You are a senior software architect specializing in healthcare technology and HIPAA-compliant systems.

Context:
We are building the Elderly Care Solutions Platform, a technology-enabled elderly care service targeting the middle-market segment ($3,000-$5,000/month budget).

Key Requirements:
- HIPAA compliant (encryption, access controls, audit logging)
- Real-time health monitoring from wearables and IoT sensors
- AI-powered anomaly detection for predictive alerts
- Multi-user system (care recipients, family members, healthcare providers)
- Senior-friendly interface (WCAG 2.1 AA accessibility)
- Scale from 100 to 1,000,000 users

Technology Stack:
- Backend: Python FastAPI
- Frontend: React + TypeScript
- Mobile: iOS (Swift), Android (Kotlin)
- Database: PostgreSQL + Redis
- Cloud: AWS or GCP

Task:
Design a high-level system architecture including:
1. Component diagram (frontend, API gateway, backend services, databases, external integrations)
2. Data flow for real-time health monitoring
3. Security architecture (authentication, authorization, encryption)
4. Scalability strategy (horizontal scaling, caching, database partitioning)

Output Format:
- Markdown with ASCII diagrams
- Component descriptions
- Data flow explanations
- Justification for technology choices

Constraints:
- Prioritize HIPAA compliance
- Optimize for elderly users (low latency, high reliability)
- Consider cost-effectiveness for middle-market positioning
```

---

### Prompt 1.2: Database Schema Design

```
You are a database architect specializing in PostgreSQL and time-series data.

Context:
Elderly Care Solutions Platform needs to store:
- User accounts and care recipient profiles
- Health metrics from wearables (heart rate, steps, sleep, blood pressure)
- Alerts (falls, medication missed, vital signs abnormal)
- Care plans and tasks
- Messages and conversations

Requirements:
- ACID compliance for healthcare data
- Time-series optimization for health metrics
- Efficient querying for dashboards and analytics
- HIPAA audit logging (who accessed what data when)

Task:
Design a PostgreSQL database schema including:
1. Tables with columns, data types, constraints, indexes
2. Relationships (foreign keys, joins)
3. Partitioning strategy for time-series data
4. Audit logging tables

Output Format:
- SQL CREATE TABLE statements
- Entity-Relationship diagram (ASCII)
- Indexing strategy
- Justification for design decisions

Constraints:
- Normalize to 3NF, denormalize where performance-critical
- Use JSONB for flexible schemas where appropriate
- Consider partitioning for tables >10M rows
```

---

## 2. Feature Development Prompts

### Prompt 2.1: Feature Implementation (Backend)

```
You are a senior backend engineer specializing in FastAPI and healthcare systems.

Context:
Elderly Care Solutions Platform - implementing alert generation system.

Requirements:
- Ingest health metrics from wearables (heart rate, blood pressure, steps)
- Rule-based alert generation (threshold-based: heart rate >100 or <60, blood pressure >140/90)
- AI-based anomaly detection (isolation forest algorithm)
- Multi-level notifications (email, SMS, push)
- Alert escalation (notify primary family member → secondary → emergency services)

Task:
Implement the alert generation service in FastAPI including:
1. API endpoint to receive health metrics
2. Rule engine for threshold-based alerts
3. Integration with ML model for anomaly detection
4. Notification service (email via SendGrid, SMS via Twilio, push via Firebase)
5. Alert storage in PostgreSQL
6. Alert escalation logic (time-based)

Output Format:
- Python FastAPI code with type hints
- Pydantic models for request/response
- Error handling and logging
- Unit tests (pytest)
- API documentation (OpenAPI)

Constraints:
- Async/await for high concurrency
- Structured logging (JSON format)
- Input validation (Pydantic)
- Error responses follow RFC 7807 (Problem Details for HTTP APIs)
- HIPAA compliance (audit logging)
```

---

### Prompt 2.2: Feature Implementation (Frontend)

```
You are a senior frontend engineer specializing in React, TypeScript, and accessible UI design.

Context:
Elderly Care Solutions Platform - building health metrics dashboard for elderly users and their family members.

Requirements:
- Display health metrics (heart rate, blood pressure, steps, sleep)
- Real-time updates via WebSocket
- Charts for trend visualization (line charts, bar charts)
- Senior-friendly interface (large text, high contrast, simple navigation)
- WCAG 2.1 AA accessibility compliance

User Stories:
- As an elderly user, I want to see my vital signs at a glance so I can monitor my health
- As a family member, I want to receive alerts if my parent's vital signs are abnormal
- As a healthcare provider, I want to export health data for analysis

Task:
Implement the health metrics dashboard in React + TypeScript including:
1. Dashboard layout with metric cards and charts
2. WebSocket integration for real-time updates
3. Data visualization using Recharts or Chart.js
4. Senior-friendly UI (Mantine UI components with customization)
5. Accessibility features (ARIA labels, keyboard navigation, screen reader support)
6. Data export (CSV, PDF)

Output Format:
- React functional components with hooks
- TypeScript types and interfaces
- Responsive CSS (Tailwind or Mantine)
- Unit tests (Vitest + React Testing Library)
- Accessibility audit results

Constraints:
- No unnecessary re-renders (useMemo, useCallback)
- Error boundaries for graceful degradation
- Loading states and empty states
- Accessibility: WCAG 2.1 AA, color contrast ≥4.5:1
- Performance: Dashboard loads in <2 seconds
```

---

### Prompt 2.3: Mobile App Feature (iOS)

```
You are a senior iOS engineer specializing in SwiftUI and healthcare apps.

Context:
Elderly Care Solutions Platform - iOS app for elderly users and family members.

Requirements:
- One-tap video calling (optimized for seniors)
- Integration with Agora or Twilio Video SDK
- Senior-friendly interface (large buttons, high contrast, simplified navigation)
- Biometric authentication (Face ID, Touch ID)
- Push notifications for alerts

User Stories:
- As an elderly user, I want to start a video call with one tap so I can easily talk to my family
- As a family member, I want to receive push notifications when my parent has an emergency

Task:
Implement the one-tap video calling feature in SwiftUI including:
1. Video call UI with large answer/decline buttons
2. Agora Video SDK integration
3. Push notification handling (incoming call notification)
4. Call management (mute, camera toggle, hang up, speaker toggle)
5. Contact list with photos for easy recognition
6. Senior-friendly UI (custom fonts, high contrast colors)

Output Format:
- SwiftUI views and view models
- Combine publishers for reactive programming
- AVFoundation for camera/microphone
- Unit tests (XCTest)
- UI tests (XCUITest)

Constraints:
- iOS 15+ deployment target
- Auto Layout for different screen sizes (iPhone, iPad)
- Accessibility: VoiceOver support, Dynamic Type
- Performance: Smooth 60fps animations
- Permissions: Camera, microphone, notifications handled gracefully
```

---

## 3. Testing Prompts

### Prompt 3.1: Unit Test Generation

```
You are a test engineer specializing in pytest and testing best practices.

Context:
Elderly Care Solutions Platform - alert generation service.

Code to Test:
```python
async def generate_alert(metric: HealthMetric, db: AsyncSession) -> Optional[Alert]:
    # Check if metric breaches threshold
    if metric.metric_type == MetricType.HEART_RATE:
        if metric.value["bpm"] > 100 or metric.value["bpm"] < 60:
            return Alert(
                care_recipient_id=metric.care_recipient_id,
                alert_type=AlertType.VITAL_ABNORMAL,
                severity=AlertSeverity.WARNING,
                message=f"Heart rate {'high' if metric.value['bpm'] > 100 else 'low'}: {metric.value['bpm']} bpm"
            )
    return None
```

Task:
Generate comprehensive unit tests including:
1. Happy path tests (normal heart rate, high heart rate, low heart rate)
2. Edge cases (boundary values: 59, 60, 61, 99, 100, 101 bpm)
3. Error cases (missing data, invalid data types)
4. Mock dependencies (database, external APIs)
5. Test coverage >90%

Output Format:
- pytest test functions with descriptive names
- Fixtures for test data
- Assertions with clear error messages
- Test organization (test class or module)

Constraints:
- Use pytest-asyncio for async tests
- Mock external dependencies (pytest-mock)
- Parametrize tests for multiple inputs
- Arrange-Act-Assert (AAA) pattern
```

---

### Prompt 3.2: Integration Test Generation

```
You are a test engineer specializing in integration testing and FastAPI.

Context:
Elderly Care Solutions Platform - health metrics API endpoint.

API Endpoint:
POST /api/v1/health-metrics
Request Body:
{
  "care_recipient_id": "uuid",
  "metric_type": "HEART_RATE",
  "value": {"bpm": 72},
  "unit": "bpm",
  "timestamp": "2025-01-03T10:30:00Z"
}

Response:
201 Created
{
  "id": "uuid",
  "care_recipient_id": "uuid",
  "metric_type": "HEART_RATE",
  "value": {"bpm": 72},
  "unit": "bpm",
  "timestamp": "2025-01-03T10:30:00Z",
  "created_at": "2025-01-03T10:30:01Z"
}

Task:
Generate integration tests including:
1. Test database insertion (metric saved to PostgreSQL)
2. Test message queue publishing (metric sent to RabbitMQ for async processing)
3. Test authentication (JWT token required)
4. Test input validation (invalid data rejected)
5. Test alert generation (alert created if threshold breached)

Output Format:
- pytest tests with FastAPI TestClient
- Test database (docker-compose PostgreSQL)
- Test message queue (docker-compose RabbitMQ)
- Cleanup after each test (rollback transactions)

Constraints:
- Use pytest-asyncio for async tests
- Test database isolated from development database
- Mock external APIs (wearable OAuth)
- Test authentication with real JWT tokens
```

---

## 4. Documentation Prompts

### Prompt 4.1: API Documentation

```
You are a technical writer specializing in REST API documentation.

Context:
Elderly Care Solutions Platform - health metrics API.

API Endpoint: POST /api/v1/health-metrics
Purpose: Submit health metric data from wearable devices or IoT sensors

Request:
Headers:
- Authorization: Bearer <JWT_TOKEN>
- Content-Type: application/json

Body:
{
  "care_recipient_id": "string (UUID)",
  "metric_type": "enum (HEART_RATE, BLOOD_PRESSURE, STEPS, SLEEP, FALL_DETECTED)",
  "value": "object (flexible schema based on metric_type)",
  "unit": "string (e.g., 'bpm', 'mmHg', 'count')",
  "timestamp": "string (ISO 8601 format)",
  "device_id": "string (UUID, optional)",
  "source": "enum (WEARABLE, IOT_SENSOR, MANUAL_ENTRY)"
}

Response:
201 Created
{
  "id": "string (UUID)",
  "care_recipient_id": "string (UUID)",
  "metric_type": "enum",
  "value": "object",
  "unit": "string",
  "timestamp": "string (ISO 8601)",
  "device_id": "string (UUID)",
  "source": "enum",
  "created_at": "string (ISO 8601)"
}

Error Responses:
- 400 Bad Request: Invalid input (validation error details)
- 401 Unauthorized: Missing or invalid JWT token
- 403 Forbidden: User does not have permission to submit metrics for this care recipient
- 404 Not Found: Care recipient not found

Task:
Write API documentation including:
1. Endpoint description and purpose
2. Authentication requirements
3. Request parameters with examples
4. Response format with examples
5. Error responses with examples
6. Code examples (Python, JavaScript, cURL)
7. Rate limiting information
8. HIPAA considerations (PHI handling)

Output Format:
- Markdown with clear headings
- Code blocks with syntax highlighting
- JSON request/response examples
- Troubleshooting section

Constraints:
- Write for external developers (integrating wearable devices)
- Include security best practices
- Provide cURL examples for easy testing
- Link to related endpoints (get metrics, get alerts)
```

---

### Prompt 4.2: User Guide for Elderly Users

```
You are a technical writer specializing in user-friendly documentation for elderly users.

Context:
Elderly Care Solutions Platform - mobile app for elderly users.

Task: Write a user guide for setting up and using the mobile app.

Target Audience: Elderly users (65+), varying tech literacy, may have vision or motor impairments

Topics to Cover:
1. Downloading and installing the app
2. Creating an account (with family member assistance)
3. Pairing a wearable device (Apple Watch, Fitbit)
4. Viewing health metrics dashboard
5. Understanding and responding to alerts
6. Video calling with family members

Guidelines:
- Use simple language (8th grade reading level)
- Include screenshots with annotations
- Step-by-step instructions with numbered lists
- Large print recommendations (font size 14-16pt)
- Avoid technical jargon
- Include troubleshooting tips
- Provide contact information for support

Output Format:
- PDF document with table of contents
- Screenshots with callouts
- Print-friendly (high contrast, avoid color-only meaning)

Constraints:
- Accessibility: PDF tagged for screen readers
- Print-friendly: Black text on white background
- Length: <20 pages
```

---

## 5. Code Review Prompts

### Prompt 5.1: Code Review Checklist

```
You are a senior engineer conducting a code review.

Context:
Pull Request: Implement alert generation service
Files Changed: `alert_service.py`, `alert_models.py`, `test_alert_service.py`
Lines Changed: +450, -50

Task:
Review the code for:
1. **Correctness**: Does the code implement the requirements correctly?
2. **Security**: Are there any security vulnerabilities (SQL injection, XSS, hardcoded secrets)?
3. **Performance**: Are there performance issues (N+1 queries, inefficient algorithms)?
4. **Readability**: Is the code easy to understand (good naming, comments, structure)?
5. **Testing**: Are there sufficient tests (unit, integration, edge cases)?
6. **Error Handling**: Are errors handled gracefully (logging, user-friendly messages)?
7. **HIPAA Compliance**: Is PHI handled correctly (encryption, audit logging, access controls)?

Output Format:
- Review comments with line numbers
- Severity levels: [BLOCKER], [CRITICAL], [MAJOR], [MINOR], [SUGGESTION]
- Actionable feedback (what to change and why)
- Positive feedback (what's done well)

Example Comment:
[L120] [CRITICAL] Security Issue: The API key is hardcoded in the source code. Move to environment variable or secrets manager.
Risk: If this code is exposed in a public repository, the API key can be stolen.
Fix: Use `os.getenv("SENDGRID_API_KEY")` and add to environment configuration.
```

---

## 6. Debugging Prompts

### Prompt 6.1: Debugging Production Issue

```
You are a senior DevOps engineer debugging a production issue.

Context:
Elderly Care Solutions Platform - monitoring alert

Issue: Health metrics API latency degraded (p95 response time increased from 200ms to 2.5s)

Monitoring Data:
- Time: 2025-01-03 10:00-11:00 UTC
- Affected Endpoint: POST /api/v1/health-metrics
- Error Rate: 0.05% (baseline 0.01%)
- Database CPU: 85% (baseline 40%)
- Database Connections: 950/1000 (connection pool nearly exhausted)
- Slow Query Log: Query `SELECT * FROM health_metrics WHERE care_recipient_id = ...` taking 8s

Task:
Debug the issue and provide:
1. Root cause analysis (why did latency increase?)
2. Impact assessment (how many users affected?)
3. Immediate mitigation (how to restore performance now?)
4. Long-term fix (how to prevent recurrence?)
5. Monitoring improvements (what alerts to add?)

Output Format:
- Incident report style
- Timeline of events
- Technical explanation with evidence
- Action items with priorities (P0, P1, P2)

Constraints:
- Prioritize restoring service over deep analysis
- Communicate clearly to stakeholders (technical and non-technical)
- Document learnings for post-mortem
```

---

## 7. AI Training Prompts

### Prompt 7.1: ML Model Training

```
You are a machine learning engineer specializing in healthcare anomaly detection.

Context:
Elderly Care Solutions Platform - training anomaly detection model for health metrics.

Dataset:
- 10,000 care recipients
- 6 months of health data (heart rate, blood pressure, steps, sleep)
- 100 confirmed anomalies (falls, hospitalizations, critical health events)
- Features: Time-series vital signs, demographic data, medical history

Task:
Train an anomaly detection model including:
1. Feature engineering (time-series features, rolling averages, trend analysis)
2. Model selection (isolation forest, autoencoder, LSTM)
3. Training/validation/test split (80/10/10)
4. Evaluation metrics (precision, recall, F1, ROC-AUC)
5. Hyperparameter tuning
6. Model interpretation (which features contribute to anomaly score?)

Output Format:
- Python code (scikit-learn or TensorFlow)
- Model evaluation report (confusion matrix, classification report)
- Feature importance plot
- Deployment recommendations (how to serve predictions in production)

Constraints:
- Handle imbalanced data (100 anomalies vs. 9,900 normal)
- Minimize false positives (<10%)
- Maximize recall for critical anomalies (>90%)
- Model inference time <100ms per prediction
- Model size <100MB (for fast deployment)
```

---

## Prompt Optimization Tips

### General Tips

1. **Start Simple**: Begin with basic prompt, iterate based on results
2. **Provide Examples**: Show input → output examples
3. **Specify Format**: JSON, Python code, Markdown, etc.
4. **Set Boundaries**: What NOT to do (e.g., "Don't use external libraries")
5. **Request Reasoning**: Ask AI to explain its thought process
6. **Iterate**: Refine prompt if output isn't what you expected

### Common Mistakes to Avoid

- ❌ Too vague: "Write code for health monitoring"
- ✅ Specific: "Write a FastAPI endpoint that receives health metrics, validates input, stores in PostgreSQL, and generates alerts if thresholds breached"

- ❌ No constraints: "Create a database schema"
- ✓ With constraints: "Create a PostgreSQL schema for health metrics, normalize to 3NF, use JSONB for flexible data, add indexes for query performance"

- ❌ Missing context: "Debug this error"
- ✓ With context: "Debug this error in health metrics API. Error: 'Connection pool exhausted'. Context: 950/1000 connections used, slow query taking 8s"

---

## Document Control

**Author**: AI Prompt Engineering Team
**Reviewers**: Engineering Lead, Data Science Lead
**Approval**: Technical Steering Committee
**Version History**:
- v1.0 (January 2025): Initial prompt template library

---

**Next Steps**:
1. Test prompts with actual AI agents (Claude, GPT-4)
2. Measure prompt effectiveness (output quality, iteration count)
3. Create prompt variant library (A/B testing different prompts)
4. Train team on prompt engineering best practices
5. Establish prompt review process (optimize low-performing prompts)
