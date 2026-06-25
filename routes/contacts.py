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

@router.get("/")
def get_contacts():
    result = supabase.table("contacts").select("*").execute()
    return result.data

@router.put("/{contact_id}")
def update_contact(contact_id: str, update: ContactUpdate):
    data = {k: v for k, v in update.dict().items() if v is not None}
    result = supabase.table("contacts").update(data).eq("id", contact_id).execute()
    return result.data
