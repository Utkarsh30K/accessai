# AccessAI - Backend Assignment Report

## **Project Overview**

AccessAI is a backend platform where users can:

- Sign in with Google OAuth
- Get free credits on signup
- Buy more credits via Stripe
- Spend credits to call AI-powered endpoints

This project was built over 5 weeks using Python and FastAPI.

---

## **Project Structure**

```
accessai/
├── config.py          # Configuration settings
├── database.py        # Database connection
├── main.py           # FastAPI app entry point
├── models/           # SQLAlchemy models
│   ├── user.py
│   ├── credit.py
│   └── payment.py
├── routes/           # API endpoints
│   ├── auth.py
│   ├── users.py
│   ├── credits.py
│   └── payments.py
├── services/         # Business logic
│   ├── credit.py
│   ├── jwt.py
│   └── oauth.py
└── dependencies/    # FastAPI dependencies
    └── auth.py
```

---

## **Week 1: Secure Foundation + Google Login**

### **What Was Implemented:**

1. **FastAPI Project Setup**
   - Created a Python backend with FastAPI
   - Set up async SQLAlchemy with PostgreSQL

2. **Database Models**
   - Users table: id, email, name, google_id, created_at

3. **Environment Configuration**
   - All secrets in `.env` file
   - Uses pydantic-settings for loading

4. **Structured Logging**
   - JSON logging with structlog
   - Logs: timestamp, method, path, status, duration_ms

5. **Google OAuth**
   - Using authlib library
   - Flow: /auth/google → Google → /auth/callback → JWT token

6. **JWT Authentication**
   - Token generation and validation
   - Protected endpoints with get_current_user dependency

### **Endpoints:**

- `GET /health` - Health check
- `GET /auth/google` - Google login redirect
- `GET /auth/callback` - Google OAuth callback
- `GET /me` - Get current user info

---

## **Week 2: Credit System**

### **What Was Implemented:**

1. **Database Tables**
   - `UserCredits`: user_id, balance, updated_at
   - `CreditTransactions`: id, user_id, amount, reason, created_at

2. **Credit Service Functions**
   - `add_credits()` - Add credits to user
   - `deduct_credits()` - Deduct credits with balance check
   - Both run in database transactions

3. **Free Credits on Signup**
   - New users get 100 credits automatically

4. **Product Endpoints**
   - POST /credits/summarize (10 credits)
   - POST /credits/analyze (25 credits)

5. **Error Handling**
   - Returns 402 Payment Required when insufficient credits

### **Endpoints:**

- `GET /credits/balance` - Get balance and transactions
- `POST /credits/summarize` - Summarize text (costs 10 credits)
- `POST /credits/analyze` - Analyze text (costs 25 credits)

---

## **Week 3: Stripe Payments**

### **What Was Implemented:**

1. **Stripe Integration**
   - Stripe Python library
   - Two credit packages:
     - Starter: 200 credits for $9
     - Pro: 500 credits for $19

2. **Checkout Session**
   - Creates Stripe Checkout Session
   - Returns checkout URL for payment

3. **Webhook Handling**
   - POST /payments/webhook
   - Verifies Stripe signature
   - Adds credits automatically on payment

4. **Idempotency**
   - Prevents duplicate credit addition
   - Stores processed session IDs

5. **Payment History**
   - GET /payments/history

### **Endpoints:**

- `POST /payments/checkout` - Create Stripe checkout session
- `POST /payments/webhook` - Stripe webhook handler
- `GET /payments/history` - Payment history

---

## **Week 4: Observability + CI/CD**

### **What Was Implemented:**

1. **Structured Logging**
   - JSON logs with structlog
   - Logs: timestamp, level, route, user_id, duration_ms

2. **Error Tracking**
   - Sentry integration
   - Auto-captures exceptions with stack traces

3. **Enhanced Health Check**
   - Checks database connectivity
   - Checks Stripe API
   - Returns 503 if degraded

4. **Prometheus Metrics**
   - GET /metrics endpoint
   - Tracks: requests/sec, response time, error rate

5. **GitHub Actions CI**
   - Runs on every PR
   - Tests: installs deps, starts DB, hits /health

6. **Docker Support**
   - Dockerfile for containerization
   - cloudbuild.yaml for Google Cloud Build
   - Deploys to Cloud Run

### **Files Created:**

- `.github/workflows/ci.yml`
- `Dockerfile`
- `cloudbuild.yaml`
- `.gcloudignore`
- `.dockerignore`

---

## **Week 5: Polish, Harden, and Full Demo**

### **What Was Implemented:**

1. **Rate Limiting**
   - Using slowapi library
   - 20 requests/minute per user
   - Returns 429 when exceeded

2. **Input Validation**
   - Text must be 10-2000 characters
   - Returns 422 for validation errors

3. **Security Hardening**
   - CORS configuration
   - Security headers:
     - X-Content-Type-Options
     - X-Frame-Options
     - Strict-Transport-Security

### **Test Script:**

- `test_rate_limit.py` - Tests rate limiting and validation

---

## **Technologies Used**

| Technology       | Purpose            |
| ---------------- | ------------------ |
| FastAPI          | Web framework      |
| SQLAlchemy       | ORM                |
| PostgreSQL       | Database           |
| Google OAuth     | Authentication     |
| JWT              | Token-based auth   |
| Stripe           | Payments           |
| structlog        | Structured logging |
| Sentry           | Error tracking     |
| Prometheus       | Metrics            |
| slowapi          | Rate limiting      |
| Docker           | Containerization   |
| GitHub Actions   | CI/CD              |
| Google Cloud Run | Deployment         |

---

## **API Endpoints Summary**

| Endpoint           | Method | Description           |
| ------------------ | ------ | --------------------- |
| /health            | GET    | Health check          |
| /auth/google       | GET    | Google OAuth redirect |
| /auth/callback     | GET    | OAuth callback        |
| /me                | GET    | Get current user      |
| /credits/balance   | GET    | Get credit balance    |
| /credits/summarize | POST   | Summarize text        |
| /credits/analyze   | POST   | Analyze text          |
| /payments/checkout | POST   | Create Stripe session |
| /payments/webhook  | POST   | Stripe webhook        |
| /payments/history  | GET    | Payment history       |
| /metrics           | GET    | Prometheus metrics    |

---

## **Testing Completed**

✅ Health check working  
✅ Google OAuth flow  
✅ JWT authentication  
✅ Credit balance system  
✅ Credit deduction  
✅ Insufficient credits error  
✅ Stripe checkout  
✅ Stripe webhook  
✅ Rate limiting (20/min)  
✅ Input validation (10-2000 chars)  
✅ Security headers  
✅ CORS configuration  
✅ Prometheus metrics  
✅ GitHub Actions CI

---

## **How to Run**

1. **Start Database:**

   ```bash
   docker-compose up -d
   ```

2. **Start Server:**

   ```bash
   uvicorn accessai.main:app --reload
   ```

3. **Access:**
   - Server: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

---

## **Conclusion**

The AccessAI backend is a production-ready system with:

- Secure authentication (Google OAuth + JWT)
- Credit system with transaction tracking
- Stripe payment integration
- Comprehensive logging and monitoring
- CI/CD pipeline
- Rate limiting and security features

All 5 weeks of the assignment have been completed and tested!
