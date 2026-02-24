from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import time
from datetime import datetime, timedelta
from jose import jwt

# Import settings to get secret key, algorithm, and Cashfree creds
from settings import settings

router = APIRouter()

# Define plan details
PLANS = {
    "student": {"amount": 15, "docs": 6, "hours_valid": 24 * 30},  # Valid for 30 days
    "cafe": {"amount": 49, "docs": 50, "hours_valid": 24},  # Valid for 24 hours
}


class VerifyRequest(BaseModel):
    order_id: str
    plan: str


def create_access_token(data: dict, expires_delta: timedelta):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


@router.post("/create-order")
def create_order(plan: str):
    plan_details = PLANS.get(plan)
    if not plan_details:
        return {"error": "Invalid plan selected"}

    order_id = f"yuvasathi_{plan}_{int(time.time())}"
    headers = {
        "x-client-id": settings.cashfree_app_id,
        "x-client-secret": settings.cashfree_secret,
        "x-api-version": "2023-08-01",
        "Content-Type": "application/json",
    }
    payload = {
        "order_id": order_id,
        "order_amount": plan_details["amount"],
        "order_currency": "INR",
        "customer_details": {
            "customer_id": f"cust_{int(time.time())}",
            "customer_name": "User",
            "customer_email": "user@example.com",
            "customer_phone": "9999999999",
        },
    }
    with httpx.Client() as client:
        res = client.post(
            f"{settings.cashfree_url}/orders", json=payload, headers=headers
        )
        data = res.json()

    return {
        "order_id": order_id,
        "payment_session_id": data.get("payment_session_id"),
    }


@router.post("/verify")
def verify_payment(req: VerifyRequest):
    headers = {
        "x-client-id": settings.cashfree_app_id,
        "x-client-secret": settings.cashfree_secret,
        "x-api-version": "2023-08-01",
    }
    with httpx.Client() as client:
        res = client.get(
            f"{settings.cashfree_url}/orders/{req.order_id}", headers=headers
        )
        data = res.json()

    if data.get("order_status") == "PAID":
        plan_details = PLANS.get(req.plan)
        if not plan_details:
            return {"success": False, "error": "Invalid plan"}

        # Create a JWT for the user
        token_data = {"plan": req.plan, "docs": plan_details["docs"]}
        expires_delta = timedelta(hours=plan_details["hours_valid"])

        access_token = create_access_token(
            data=token_data, expires_delta=expires_delta
        )

        return {"success": True, "token": access_token}

    return {"success": False, "error": "Payment not successful"}
