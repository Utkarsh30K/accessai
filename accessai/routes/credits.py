from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.user import User
from ..dependencies.auth import get_current_user
from ..services.credit import (
    get_user_credits, 
    get_user_transactions, 
    deduct_credits, 
    InsufficientCreditsError
)

router = APIRouter(prefix="/credits", tags=["Credits"])


# Request models
class SummarizeRequest(BaseModel):
    text: str


class AnalyzeRequest(BaseModel):
    text: str


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
async def summarize(
    request: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Summarize text - costs 10 credits.
    Returns a fake summary of the input text.
    """
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
    summary = f"Summary: {request.text[:50]}..."
    return {"result": summary}


@router.post("/analyze", tags=["AI Features"])
async def analyze(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze text - costs 25 credits.
    Returns word count and sentiment (fake).
    """
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
    word_count = len(request.text.split())
    return {
        "result": "Analysis complete.",
        "word_count": word_count,
        "sentiment": "Positive"
    }
