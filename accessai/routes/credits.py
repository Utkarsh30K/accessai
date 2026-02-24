from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..models.user import User
from ..dependencies.auth import get_current_user
from ..services.credit import (
    get_user_credits, 
    get_user_transactions, 
    deduct_credits, 
    InsufficientCreditsError
)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/credits", tags=["Credits"])


# Request models with validation
class SummarizeRequest(BaseModel):
    text: str = Field(min_length=10, max_length=2000, description="Text to summarize (10-2000 characters)")


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=10, max_length=2000, description="Text to analyze (10-2000 characters)")


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's credit balance and last 10 transactions.
    Requires JWT authentication.
    """
    # Get user credits
    user_credits = await get_user_credits(db, str(current_user.id))
    balance = user_credits.balance if user_credits else 0
    
    # Get last 10 transactions
    transactions = await get_user_transactions(db, str(current_user.id), limit=10)
    
    return {
        "balance": balance,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "reason": t.reason,
                "created_at": t.created_at
            }
            for t in transactions
        ]
    }


@router.post("/summarize", tags=["AI Features"])
@limiter.limit("20/minute")
async def summarize(
    request: Request,
    request_data: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Summarize text - costs 10 credits.
    Returns a fake summary of the input text.
    Rate limit: 20 requests per minute.
    """
    text = request_data.text
    COST = 10
    
    # Try to deduct credits
    try:
        await deduct_credits(db, str(current_user.id), COST, "summarize")
    except InsufficientCreditsError:
        # Get current balance for error response
        user_credits = await get_user_credits(db, str(current_user.id))
        balance = user_credits.balance if user_credits else 0
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_credits",
                "balance": balance,
                "required": COST
            }
        )
    
    # Return fake summary (first 50 characters)
    summary = f"Summary: {text[:50]}..."
    return {"result": summary}


@router.post("/analyze", tags=["AI Features"])
@limiter.limit("20/minute")
async def analyze(
    request: Request,
    request_data: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze text - costs 25 credits.
    Returns word count and sentiment (fake).
    Rate limit: 20 requests per minute.
    """
    text = request_data.text
    COST = 25
    
    # Try to deduct credits
    try:
        await deduct_credits(db, str(current_user.id), COST, "analyze")
    except InsufficientCreditsError:
        # Get current balance for error response
        user_credits = await get_user_credits(db, str(current_user.id))
        balance = user_credits.balance if user_credits else 0
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_credits",
                "balance": balance,
                "required": COST
            }
        )
    
    # Return fake analysis
    word_count = len(text.split())
    return {
        "result": "Analysis complete.",
        "word_count": word_count,
        "sentiment": "Positive"
    }
