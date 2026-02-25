from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
import io
import redis
from datetime import datetime, timedelta

# Local application imports
from converter import compress_pdf, compress_image
from payment import router as payment_router
from settings import settings

# --- Application Setup ---
app = FastAPI(title="YuvaSathi Document Formatter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payment_router, prefix="/payment")

# --- Redis Connection ---
# This connection will be reused across the application
try:
    if settings.redis_url:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    else:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
            decode_responses=True,
        )
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")
    redis_client = None

# --- Security & Rate Limiting ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/payment/token", auto_error=False)

class TokenData(BaseModel):
    plan: str | None = None
    docs: int | None = None

class UserContext(BaseModel):
    is_paid: bool
    ip: str
    token: str | None = None

def get_ip(request: Request) -> str:
    """Safely get the client's IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.split(",")[0].strip() if forwarded else request.client.host

async def get_user_context(request: Request, token: str | None = Depends(oauth2_scheme)) -> UserContext:
    """
    Dependency to determine if the user is on a paid or free plan.
    This runs before endpoints that inject it.
    """
    ip = get_ip(request)
    
    # If the user provides a token, they are attempting to use a paid plan.
    if token and redis_client:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            plan = payload.get("plan")
            
            # Use Redis HASH to store paid user data to avoid key clashes
            paid_user_key = f"paid_user:{token}"
            
            # Check if this token has been used before
            if not redis_client.exists(paid_user_key):
                 # First time using this token, initialize their doc count
                docs_allowed = payload.get("docs", 0)
                redis_client.hset(paid_user_key, "remaining", docs_allowed)
                # Set expiry on the key to match token expiry
                token_exp = payload.get("exp")
                if token_exp:
                    expire_at = int(token_exp) - int(datetime.utcnow().timestamp())
                    if expire_at > 0:
                        redis_client.expire(paid_user_key, time=expire_at)

            # Check if they have docs remaining
            remaining_docs = int(redis_client.hget(paid_user_key, "remaining") or 0)
            if remaining_docs > 0:
                return UserContext(is_paid=True, ip=ip, token=token)

        except JWTError:
            # Token is invalid, fall through to free limit check
            pass

    # If no valid token, or token has no docs left, treat as free user
    return UserContext(is_paid=False, ip=ip)

def process_usage(user: UserContext = Depends(get_user_context)):
    """
    Dependency that processes usage counts after a successful conversion.
    This should be used by the conversion endpoints.
    """
    if not redis_client:
        return # Cannot process usage if Redis is down

    if user.is_paid and user.token:
        paid_user_key = f"paid_user:{user.token}"
        redis_client.hincrby(paid_user_key, "remaining", -1)
    else:
        # For free users, increment their IP-based counter
        # Use a pipeline for atomic increment and expire operations
        p = redis_client.pipeline()
        p.incr(user.ip, 1)
        p.expire(user.ip, timedelta(days=1)) # Usage resets every 24 hours
        p.execute()

# --- API Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok", "redis_connected": redis_client is not None}

@app.get("/check-limit")
def check_limit_endpoint(request: Request, myref: str | None = None):
    """Checks remaining free conversions, including referral bonuses."""
    if not redis_client:
        return {"used": 0, "remaining": settings.free_limit, "bonus": 0}

    ip = get_ip(request)
    used = int(redis_client.get(ip) or 0)
    bonus = 0
    if myref:
        raw = redis_client.get(f"ref_credit:{myref}")
        bonus = min(int(raw or 0), 5)  # cap at 5 bonus conversions
    effective_limit = settings.free_limit + bonus
    return {"used": used, "remaining": max(0, effective_limit - used), "bonus": bonus}


@app.post("/referral/credit")
def referral_credit(ref_code: str, request: Request):
    """
    Called when a referred visitor completes their first conversion.
    Credits the referrer with +1 bonus conversion (capped at 5 total).
    Prevents the same visitor IP from crediting more than once.
    """
    if not redis_client or not ref_code:
        return {"credited": False}

    visitor_ip = get_ip(request)
    already_key = f"ref_credited:{visitor_ip}"
    if redis_client.exists(already_key):
        return {"credited": False, "reason": "already credited"}

    current = int(redis_client.get(f"ref_credit:{ref_code}") or 0)
    if current >= 5:
        return {"credited": False, "reason": "cap reached"}

    redis_client.incr(f"ref_credit:{ref_code}")
    redis_client.set(already_key, "1", ex=60 * 60 * 24 * 30)  # lock for 30 days
    return {"credited": True}

async def conversion_gate(user: UserContext = Depends(get_user_context)):
    """A dependency that blocks access if usage limits are exceeded."""
    if user.is_paid:
        return # Paid users are allowed

    # Free user check
    if not redis_client:
        # If redis is down, we allow access but can't track.
        # Could also choose to deny all.
        return

    used_count = int(redis_client.get(user.ip) or 0)
    if used_count >= settings.free_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Free limit reached. Please purchase a plan to continue.",
        )

@app.post("/convert/pdf", dependencies=[Depends(conversion_gate)])
async def convert_pdf(file: UploadFile = File(...), user_context: None = Depends(process_usage)):
    contents = await file.read()
    output = compress_pdf(contents)
    return StreamingResponse(
        io.BytesIO(output),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=compressed.pdf"}
    )

@app.post("/convert/photo", dependencies=[Depends(conversion_gate)])
async def convert_photo(file: UploadFile = File(...), user_context: None = Depends(process_usage)):
    contents = await file.read()
    output = compress_image(contents, fmt="JPEG")
    return StreamingResponse(
        io.BytesIO(output),
        media_type="image/jpeg",
        headers={"Content-Disposition": "attachment; filename=compressed.jpg"}
    )

@app.post("/convert/signature", dependencies=[Depends(conversion_gate)])
async def convert_signature(file: UploadFile = File(...), user_context: None = Depends(process_usage)):
    contents = await file.read()
    output = compress_image(contents, fmt="PNG")
    return StreamingResponse(
        io.BytesIO(output),
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=compressed.png"}
    )