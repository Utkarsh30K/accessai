import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.credit import UserCredit, CreditTransaction


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits to complete a transaction."""
    pass


async def add_credits(db: AsyncSession, user_id: str, amount: int, reason: str):
    """
    Add credits to user balance and log the transaction.
    
    Args:
        db: Database session
        user_id: The user's UUID (as string)
        amount: Number of credits to add (positive)
        reason: Description of why credits were added
    
    Returns:
        Updated UserCredit object
    """
    # Convert string to UUID
    user_uuid = uuid.UUID(user_id)
    
    # Get or create user credit record
    stmt = select(UserCredit).where(UserCredit.user_id == user_uuid)
    result = await db.execute(stmt)
    user_credit = result.scalar_one_or_none()
    
    if not user_credit:
        user_credit = UserCredit(user_id=user_uuid, balance=0)
        db.add(user_credit)
    
    # Add credits
    user_credit.balance += amount
    
    # Log transaction
    transaction = CreditTransaction(
        user_id=user_uuid,
        amount=amount,
        reason=reason
    )
    db.add(transaction)
    
    await db.commit()
    await db.refresh(user_credit)
    return user_credit


async def deduct_credits(db: AsyncSession, user_id: str, amount: int, reason: str):
    """
    Deduct credits from user balance if sufficient.
    Raises InsufficientCreditsError if not enough balance.
    
    Args:
        db: Database session
        user_id: The user's UUID (as string)
        amount: Number of credits to deduct
        reason: Description of why credits were deducted
    
    Returns:
        Updated UserCredit object
    
    Raises:
        InsufficientCreditsError: If balance is less than amount
    """
    # Convert string to UUID
    user_uuid = uuid.UUID(user_id)
    
    # Get user credit
    stmt = select(UserCredit).where(UserCredit.user_id == user_uuid)
    result = await db.execute(stmt)
    user_credit = result.scalar_one_or_none()
    
    if not user_credit or user_credit.balance < amount:
        current_balance = user_credit.balance if user_credit else 0
        raise InsufficientCreditsError(
            f"Insufficient credits. Required: {amount}, Available: {current_balance}"
        )
    
    # Deduct credits
    user_credit.balance -= amount
    
    # Log transaction (negative amount)
    transaction = CreditTransaction(
        user_id=user_uuid,
        amount=-amount,
        reason=reason
    )
    db.add(transaction)
    
    await db.commit()
    await db.refresh(user_credit)
    return user_credit


async def get_user_credits(db: AsyncSession, user_id: str) -> UserCredit | None:
    """
    Get user's credit balance.
    
    Args:
        db: Database session
        user_id: The user's UUID (as string)
    
    Returns:
        UserCredit object or None if not found
    """
    user_uuid = uuid.UUID(user_id)
    stmt = select(UserCredit).where(UserCredit.user_id == user_uuid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_transactions(db: AsyncSession, user_id: str, limit: int = 10):
    """
    Get user's credit transaction history.
    
    Args:
        db: Database session
        user_id: The user's UUID (as string)
        limit: Number of transactions to return
    
    Returns:
        List of CreditTransaction objects
    """
    user_uuid = uuid.UUID(user_id)
    stmt = (
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user_uuid)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def add_credits_by_email(db: AsyncSession, email: str, amount: int, reason: str):
    """
    Find user by email and add credits to their account.
    
    Args:
        db: Database session
        email: User's email address
        amount: Number of credits to add
        reason: Description of why credits were added
    
    Returns:
        Updated UserCredit object or None if user not found
    """
    from ..models.user import User
    
    # Find user by email
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        return await add_credits(db, str(user.id), amount, reason)
    return None
