from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import supabase
from jose import jwt
import os, datetime, bcrypt

router = APIRouter()
SECRET = os.getenv("SECRET_KEY", "secret")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "member"

@router.post("/register")
def register(req: RegisterRequest):
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    result = supabase.table("team_members").insert({
        "name": req.name,
        "email": req.email,
        "password_hash": hashed,
        "role": req.role
    }).execute()
    return {"message": "Registered successfully"}

@router.post("/login")
def login(req: LoginRequest):
    result = supabase.table("team_members").select("*").eq("email", req.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = result.data[0]
    try:
        valid = bcrypt.checkpw(req.password.encode(), user["password_hash"].encode())
    except Exception:
        valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({
        "sub": user["id"],
        "name": user["name"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, SECRET)
    return {"token": token, "user": {"name": user["name"], "role": user["role"]}}
