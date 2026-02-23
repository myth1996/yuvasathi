from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from converter import compress_pdf, compress_image
from payment import router as payment_router
import io
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payment_router, prefix="/payment")

TRACKING_FILE = "conversions.json"
FREE_LIMIT = 2

def load_tracking():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tracking(data):
    with open(TRACKING_FILE, "w") as f:
        json.dump(data, f)

def get_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def check_free_limit(ip: str):
    data = load_tracking()
    return data.get(ip, 0) < FREE_LIMIT

def increment_count(ip: str):
    data = load_tracking()
    data[ip] = data.get(ip, 0) + 1
    save_tracking(data)

def is_paid(request: Request):
    return request.headers.get("X-Access-Token") == "paid"

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/check-limit")
def check_limit(request: Request):
    ip = get_ip(request)
    data = load_tracking()
    used = data.get(ip, 0)
    return {"used": used, "remaining": max(0, FREE_LIMIT - used)}

@app.post("/convert/pdf")
async def convert_pdf(request: Request, file: UploadFile = File(...)):
    ip = get_ip(request)
    if not check_free_limit(ip) and not is_paid(request):
        return JSONResponse(status_code=402, content={"error": "paywall"})
    contents = await file.read()
    output = compress_pdf(contents)
    del contents
    increment_count(ip)
    return StreamingResponse(
        io.BytesIO(output),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=compressed.pdf"}
    )

@app.post("/convert/photo")
async def convert_photo(request: Request, file: UploadFile = File(...)):
    ip = get_ip(request)
    if not check_free_limit(ip) and not is_paid(request):
        return JSONResponse(status_code=402, content={"error": "paywall"})
    contents = await file.read()
    output = compress_image(contents, fmt="JPEG")
    del contents
    increment_count(ip)
    return StreamingResponse(
        io.BytesIO(output),
        media_type="image/jpeg",
        headers={"Content-Disposition": "attachment; filename=compressed.jpg"}
    )

@app.post("/convert/signature")
async def convert_signature(request: Request, file: UploadFile = File(...)):
    ip = get_ip(request)
    if not check_free_limit(ip) and not is_paid(request):
        return JSONResponse(status_code=402, content={"error": "paywall"})
    contents = await file.read()
    output = compress_image(contents, fmt="PNG")
    del contents
    increment_count(ip)
    return StreamingResponse(
        io.BytesIO(output),
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=compressed.png"}
    )