from fastapi import APIRouter, Depends
from ..models.user import User
from ..dependencies.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


# Test endpoint to trigger Sentry error
@router.get("/test-error")
async def test_error():
    """Test endpoint to verify Sentry is working. Raises a test exception."""
    raise Exception("This is a test error for Sentry!")


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    Requires valid JWT token in Authorization header.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "created_at": current_user.created_at
    }
