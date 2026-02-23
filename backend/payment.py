from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import time

router = APIRouter()

CASHFREE_APP_ID = "YOUR_APP_ID"
CASHFREE_SECRET = "YOUR_SECRET"
CASHFREE_URL = "https://sandbox.cashfree.com/pg"

PLANS = {
    "student": 15,
    "cafe": 49
}

class VerifyRequest(BaseModel):
    order_id: str
    plan: str

@router.post("/create-order")
def create_order(plan: str):
    amount = PLANS.get(plan, 15)
    order_id = f"yuvasathi_{plan}_{int(time.time())}"
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET,
        "x-api-version": "2023-08-01",
        "Content-Type": "application/json"
    }
    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": f"cust_{int(time.time())}",
            "customer_name": "Student",
            "customer_email": "student@yuvasathi.in",
            "customer_phone": "9999999999"
        }
    }
    with httpx.Client() as client:
        res = client.post(f"{CASHFREE_URL}/orders", json=payload, headers=headers)
        data = res.json()
    return {
        "order_id": order_id,
        "payment_session_id": data.get("payment_session_id"),
        "amount": amount,
        "app_id": CASHFREE_APP_ID
    }

@router.post("/verify")
def verify_payment(req: VerifyRequest):
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET,
        "x-api-version": "2023-08-01"
    }
    with httpx.Client() as client:
        res = client.get(f"{CASHFREE_URL}/orders/{req.order_id}", headers=headers)
        data = res.json()
    if data.get("order_status") == "PAID":
        if req.plan == "student":
            return {"success": True, "docs_allowed": 6, "plan": "student"}
        else:
            return {"success": True, "docs_allowed": 50, "plan": "cafe", "hours": 24}
    return {"success": False}
