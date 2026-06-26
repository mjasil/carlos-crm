from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import supabase
from typing import Optional, List

router = APIRouter()

class ContactUpdate(BaseModel):
    deposit_amount: Optional[float] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    blacklisted: Optional[bool] = None

@router.get("/")
def get_contacts():
    result = supabase.table("contacts").select("*").execute()
    return result.data

@router.get("/blacklist")
def get_blacklist():
    result = supabase.table("contacts").select("*").eq("blacklisted", True).execute()
    return result.data

@router.put("/{contact_id}")
def update_contact(contact_id: str, update: ContactUpdate):
    data = {k: v for k, v in update.dict().items() if v is not None}
    result = supabase.table("contacts").update(data).eq("id", contact_id).execute()
    return result.data

@router.post("/blacklist/{chat_id}")
def blacklist_chat(chat_id: int):
    # Check if exists
    existing = supabase.table("contacts").select("*").eq("chat_id", chat_id).execute()
    if existing.data:
        supabase.table("contacts").update({"blacklisted": True, "status": "blacklisted"}).eq("chat_id", chat_id).execute()
    else:
        supabase.table("contacts").insert({
            "chat_id": chat_id,
            "blacklisted": True,
            "status": "blacklisted"
        }).execute()
    return {"status": "blacklisted", "chat_id": chat_id}

@router.delete("/blacklist/{chat_id}")
def remove_blacklist(chat_id: int):
    supabase.table("contacts").update({"blacklisted": False, "status": "active"}).eq("chat_id", chat_id).execute()
    return {"status": "removed from blacklist"}
