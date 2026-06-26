from fastapi import APIRouter, HTTPException
from database import supabase
from telegram_client import get_client
import os

router = APIRouter()

@router.get("/")
def get_accounts():
    result = supabase.table("accounts").select("id,name,phone,is_active,created_at").execute()
    return result.data

@router.post("/connect/{account_number}")
async def connect_account(account_number: int):
    try:
        client = await get_client(account_number)
        me = await client.get_me()
        name = os.getenv(f"ACCOUNT{account_number}_NAME", f"Account {account_number}")
        
        existing = supabase.table("accounts").select("*").eq("name", name).execute()
        if existing.data:
            supabase.table("accounts").update({
                "phone": str(me.phone_number),
                "is_active": True
            }).eq("name", name).execute()
        else:
            supabase.table("accounts").insert({
                "name": name,
                "phone": str(me.phone_number),
                "api_id": os.getenv(f"ACCOUNT{account_number}_API_ID"),
                "api_hash": os.getenv(f"ACCOUNT{account_number}_API_HASH"),
                "is_active": True
            }).execute()
        
        return {"status": "connected", "name": me.first_name, "phone": str(me.phone_number)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/disconnect/{account_number}")
async def disconnect_account(account_number: int):
    from telegram_client import disconnect_client
    await disconnect_client(account_number)
    return {"status": "disconnected"}
