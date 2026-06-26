from fastapi import APIRouter, HTTPException
from database import supabase
from telegram_client import get_client
import os, traceback

router = APIRouter()

@router.get("/")
def get_accounts():
    result = supabase.table("accounts").select("id,name,phone,is_active,created_at").execute()
    return result.data

@router.post("/connect/{account_number}")
async def connect_account(account_number: int):
    try:
        # Check session string exists
        session_string = os.getenv(f"ACCOUNT{account_number}_SESSION")
        if not session_string:
            raise HTTPException(status_code=400, detail=f"ACCOUNT{account_number}_SESSION not set in environment")
        
        api_id = os.getenv(f"ACCOUNT{account_number}_API_ID")
        api_hash = os.getenv(f"ACCOUNT{account_number}_API_HASH")
        
        if not api_id or not api_hash:
            raise HTTPException(status_code=400, detail=f"API credentials missing for account {account_number}")

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
                "api_id": str(api_id),
                "api_hash": str(api_hash),
                "is_active": True
            }).execute()
        
        return {"status": "connected", "name": me.first_name, "phone": str(me.phone_number)}
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"{str(e)} | {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)

@router.post("/disconnect/{account_number}")
async def disconnect_account(account_number: int):
    from telegram_client import disconnect_client
    await disconnect_client(account_number)
    return {"status": "disconnected"}
