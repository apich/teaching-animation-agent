"""Auth router for teaching animation website."""
import hashlib
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory storage
users_db = {}  # {username: {password_hash, phone, created_at}}
tokens_db = {}  # {token: {username, created_at}}

INVITE_CODE = "XSYY2026"
TEST_VERIFY_CODE = "123456"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    invite_code: str


class SendCodeRequest(BaseModel):
    phone: str


class ResetPasswordRequest(BaseModel):
    phone: str
    code: str
    new_password: str


@router.post("/login")
async def login(req: LoginRequest):
    user = users_db.get(req.username)
    if not user or user["password_hash"] != hash_password(req.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = str(uuid.uuid4())
    tokens_db[token] = {"username": req.username, "created_at": datetime.utcnow().isoformat()}
    return {"token": token, "user": {"username": req.username}}


@router.post("/register")
async def register(req: RegisterRequest):
    if req.invite_code != INVITE_CODE:
        raise HTTPException(status_code=400, detail="邀请码无效")
    if req.username in users_db:
        raise HTTPException(status_code=400, detail="用户名已存在")
    users_db[req.username] = {
        "password_hash": hash_password(req.password),
        "phone": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    token = str(uuid.uuid4())
    tokens_db[token] = {"username": req.username, "created_at": datetime.utcnow().isoformat()}
    return {"token": token, "user": {"username": req.username}}


@router.post("/send-code")
async def send_code(req: SendCodeRequest):
    # Hardcoded test code for development
    return {"success": True, "code": TEST_VERIFY_CODE}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    if req.code != TEST_VERIFY_CODE:
        raise HTTPException(status_code=400, detail="验证码错误")
    # Find user by phone
    target_user = None
    for username, data in users_db.items():
        if data.get("phone") == req.phone:
            target_user = username
            break
    if not target_user:
        raise HTTPException(status_code=404, detail="未找到绑定该手机号的用户")
    users_db[target_user]["password_hash"] = hash_password(req.new_password)
    return {"success": True}


@router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    token_data = tokens_db.get(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="登录已过期")
    return {"username": token_data["username"]}
