from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.requests import Request
from ..database import get_db
from ..models.user import User
from ..services.oauth import oauth
from ..services.jwt import create_access_token
from ..services.credit import add_credits
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google")
async def google_login(request: Request):
    """
    Redirect the user to Google OAuth login page.
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle the Google OAuth callback.
    Get user info from Google, create/update user in database, and return JWT token.
    """
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('sub')
        
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                name=name,
                google_id=google_id
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Add 100 signup credits for new users
            await add_credits(db, str(user.id), 100, "signup_bonus")
        
        # Create JWT token
        jwt_token = create_access_token(str(user.id), user.email)
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")
