import stripe
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.database import get_pool

router = APIRouter()

# Map Stripe subscription statuses to our internal statuses
_STATUS_MAP = {
    "trialing": "trialing",
    "active": "active",
    "past_due": "past_due",
    "canceled": "canceled",
    "unpaid": "past_due",
    "incomplete": "trialing",
    "incomplete_expired": "canceled",
    "paused": "canceled",
}


@router.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event_type: str = event["type"]

    if event_type.startswith("customer.subscription."):
        subscription = event["data"]["object"]
        customer_id: str = subscription["customer"]
        stripe_status: str = subscription["status"]
        internal_status = _STATUS_MAP.get(stripe_status, "free")

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE profiles SET subscription_status = $1 WHERE stripe_customer_id = $2",
                internal_status,
                customer_id,
            )

    elif event_type == "customer.created":
        customer = event["data"]["object"]
        customer_id = customer["id"]
        email: str = customer.get("email", "")
        if email:
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE profiles SET stripe_customer_id = $1 WHERE email = $2 AND stripe_customer_id IS NULL",
                    customer_id,
                    email,
                )

    return {"received": True}
