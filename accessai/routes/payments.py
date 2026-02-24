import stripe
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..config import settings, CREDIT_PACKAGES
from ..database import get_db
from ..services.credit import add_credits_by_email, get_user_transactions
from ..models.payment import Payment
from ..models.user import User
from ..dependencies.auth import get_current_user

# Configure Stripe with the secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/payments", tags=["Payments"])


class CheckoutRequest(BaseModel):
    package_name: str


@router.post("/checkout")
async def create_checkout_session(request: CheckoutRequest):
    """
    Create a Stripe checkout session for purchasing credits.
    
    Args:
        request: Contains package_name ("starter" or "pro")
    
    Returns:
        checkout_url: URL to redirect user for payment
    """
    package_name = request.package_name
    
    if package_name not in CREDIT_PACKAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid package name. Use 'starter' or 'pro'."
        )
    
    package = CREDIT_PACKAGES[package_name]
    price_cents = package["price_usd"] * 100
    
    # Create checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"{package['credits']} Credits - {package_name.title()}",
                },
                "unit_amount": price_cents,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="http://localhost:8000/payments/success",
        cancel_url="http://localhost:8000/payments/cancel",
        metadata={
            "package_name": package_name,
            "credits": str(package["credits"])
        }
    )
    
    return {"checkout_url": session.url}


@router.get("/success")
async def payment_success():
    """Redirect here after successful payment."""
    return {"message": "Payment successful! Credits will be added shortly."}


@router.get("/cancel")
async def payment_cancel():
    """Redirect here if payment is cancelled."""
    return {"message": "Payment cancelled."}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle Stripe webhook events.
    Verifies signature and processes payment events.
    
    This endpoint is called by Stripe after successful payment.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return {"error": "Invalid payload"}, 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return {"error": "Invalid signature"}, 400
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Get session ID for idempotency check
        session_id = session.get("id")
        
        # Check if already processed
        stmt = select(Payment).where(Payment.stripe_session_id == session_id)
        result = await db.execute(stmt)
        existing_payment = result.scalar_one_or_none()
        
        if existing_payment:
            return {"status": "already_processed"}
        
        # Get customer email and credits from metadata
        customer_email = session.get("customer_details", {}).get("email")
        credits = int(session.get("metadata", {}).get("credits", 0))
        
        if customer_email and credits:
            # Add credits to user account
            credit_result = await add_credits_by_email(db, customer_email, credits, "stripe_payment")
            if credit_result:
                # Record the payment to prevent duplicates
                payment = Payment(
                    stripe_session_id=session_id,
                    user_email=customer_email,
                    credits=credits
                )
                db.add(payment)
                await db.commit()
                print(f"Added {credits} credits to {customer_email}")
            else:
                print(f"User not found for email: {customer_email}")
    
    return {"status": "success"}


@router.get("/history")
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's payment-related credit transactions.
    Requires JWT authentication.
    """
    # Get user's transactions
    transactions = await get_user_transactions(db, str(current_user.id), limit=10)
    
    # Filter for payment-related transactions
    payment_transactions = [
        {
            "id": t.id,
            "amount": t.amount,
            "reason": t.reason,
            "created_at": t.created_at
        }
        for t in transactions
        if "stripe" in t.reason or "payment" in t.reason
    ]
    
    return {"transactions": payment_transactions}
