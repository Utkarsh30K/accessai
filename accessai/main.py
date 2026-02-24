import time
import structlog
import stripe
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from .database import engine, Base, get_db
from .models import user  # Ensure the User model is imported
from .models import credit  # Ensure the Credit models are imported
from .models import payment  # Ensure the Payment model is imported
from .routes import auth  # Import auth routes
from .routes import users  # Import users routes
from .routes import credits  # Import credits routes
from .routes import payments  # Import payments routes
from .config import settings

# Configure structlog for structured JSON logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Store startup time for uptime calculation
start_time = time.time()

# Initialize Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/health", "/metrics"]
)

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    logger.info("AccessAI server starting up...")
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    yield
    logger.info("AccessAI server shutting down...")


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AccessAI", lifespan=lifespan)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add Prometheus metrics
instrumentator.instrument(app).expose(app)

# Add SessionMiddleware for OAuth (required by authlib)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Add CORS middleware (allow specific origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth.router)

# Include users routes
app.include_router(users.router)

# Include credits routes
app.include_router(credits.router)

# Include payments routes
app.include_router(payments.router)


# Logging middleware - logs every HTTP request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log incoming request
    logger.info(
        "request",
        method=request.method,
        path=request.url.path
    )

    # Process the request
    response = await call_next(request)

    # Calculate duration in milliseconds
    duration = (time.time() - start_time) * 1000

    # Log response details
    logger.info(
        "response",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration, 2)
    )

    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "deny"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


@app.get("/health", tags=["Health"])
async def health_check(db_session: AsyncSession = Depends(get_db)):
    """
    Enhanced health check with database and Stripe verification.
    Returns the server status, database status, Stripe status, and uptime.
    """
    status = {"status": "ok", "database": "ok", "stripe": "ok", "uptime_seconds": int(time.time() - start_time)}
    is_healthy = True
    
    # Check database
    try:
        await db_session.execute(text("SELECT 1"))
    except Exception as e:
        status["database"] = "error"
        is_healthy = False
    
    # Check Stripe (if key is set)
    if settings.STRIPE_SECRET_KEY:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Account.retrieve()
        except Exception:
            status["stripe"] = "warning"
    
    if not is_healthy:
        status["status"] = "degraded"
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=status)
    
    return status

#Commit added to test ci