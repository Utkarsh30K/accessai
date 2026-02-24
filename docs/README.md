# AccessAI - Week 1 Documentation

## What the App Does

AccessAI is a backend platform that allows users to:
- Sign in with their Google account
- Receive free credits upon signup
- Use those credits to call AI-powered endpoints

By the end of Week 5, this will be a fully deployed production system with Stripe payments, credit purchases, and live deployment.

---

## What's in the Database

### Users Table

The application uses PostgreSQL with a single table for now:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `email` | String | User's email (unique) |
| `name` | String | User's name from Google |
| `google_id` | String | Unique Google identifier |
| `created_at` | DateTime | Timestamp when user was created |

---

## How Google Login Works

The OAuth flow follows these steps:

### 1. User Initiates Login
```
GET /auth/google
```
The server redirects the user to Google's login page.

### 2. User Signs in with Google
User enters their Google credentials on Google's website.

### 3. Google Redirects Back
```
GET /auth/callback?code=...
```
Google redirects back to our `/auth/callback` endpoint with an authorization code.

### 4. Backend Exchanges Code for Token
The backend:
- Exchanges the authorization code for an access token
- Retrieves the user's email and name from Google
- Checks if the user already exists in our database
- Creates a new user if they don't exist

### 5. JWT Token Returned
The backend returns a JWT token that the frontend uses for subsequent requests.

---

## What the JWT Token Is For

### Purpose
The JWT (JSON Web Token) serves as a **digital identity card**:

1. **Proof of Identity**: It proves the user has successfully authenticated with Google
2. **Stateless Authentication**: No need to store sessions on the server
3. **Protected Routes**: Required in the `Authorization` header for protected endpoints

### How to Use
For any protected endpoint, include the token in the request:

```
Authorization: Bearer <your_jwt_token>
```

### Token Contents
The JWT contains:
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": "2024-01-22T12:00:00Z"
}
```

---

## API Endpoints (Week 1)

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/health` | GET | No | Health check |
| `/auth/google` | GET | No | Redirect to Google login |
| `/auth/callback` | GET | No | Handle OAuth callback |
| `/users/me` | GET | Yes | Get current user info |

---

## Project Structure

```
accessai/
├── main.py              # FastAPI app, middleware, logging
├── config.py           # Settings loaded from .env
├── database.py         # SQLAlchemy async engine setup
├── models/
│   └── user.py         # User SQLAlchemy model
├── routes/
│   ├── auth.py         # OAuth endpoints
│   └── users.py        # User endpoints
├── services/
│   ├── oauth.py        # Google OAuth configuration
│   └── jwt.py          # JWT token creation/verification
└── dependencies/
    └── auth.py         # get_current_user dependency
```

---

## Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Key for JWT signing |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL |

---

## Testing the Flow

### 1. Start the Server
```bash
docker-compose up -d
uvicorn accessai.main:app --reload
```

### 2. Get a Token
Visit `http://localhost:8000/auth/google` in a browser and sign in with Google.

### 3. Test Protected Endpoint
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/users/me
```

---

## Summary

- **Week 1** establishes the foundation: Google OAuth + JWT authentication
- Users sign in once with Google, then use JWT tokens for all subsequent requests
- The system is ready for Week 2 (credit system) and beyond
