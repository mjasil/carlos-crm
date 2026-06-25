from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from database import supabase
from telegram_client import get_client
from typing import Optional, List
import asyncio, datetime

router = APIRouter()

class CampaignRequest(BaseModel):
    account_number: int
    folder_id: int
    message: str
    chat_ids: List[int]
    delay_seconds: int = 3
    sent_by: str = "admin"
    scheduled_at: Optional[str] = None

async def send_bulk(campaign_id: str, client, chat_ids: list, message: str, delay: int):
    supabase.table("campaigns").update({"status": "running", "started_at": datetime.datetime.utcnow().isoformat()}).eq("id", campaign_id).execute()
    
    sent = 0
    failed = 0
    
    for chat_id in chat_ids:
        try:
            await client.send_message(chat_id, message)
            sent += 1
            supabase.table("campaign_logs").insert({
                "campaign_id": campaign_id,
                "chat_id": chat_id,
                "status": "sent"
            }).execute()
        except Exception as e:
            failed += 1
            supabase.table("campaign_logs").insert({
                "campaign_id": campaign_id,
                "chat_id": chat_id,
                "status": "failed",
                "error_message": str(e)
            }).execute()
        
        supabase.table("campaigns").update({"sent_count": sent, "failed_count": failed}).eq("id", campaign_id).execute()
        await asyncio.sleep(delay)
    
    supabase.table("campaigns").update({
        "status": "completed",
        "completed_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", campaign_id).execute()

@router.post("/send")
async def send_campaign(req: CampaignRequest, background_tasks: BackgroundTasks):
    campaign = supabase.table("campaigns").insert({
        "message": req.message,
        "total_chats": len(req.chat_ids),
        "sent_count": 0,
        "failed_count": 0,
        "status": "pending",
        "sent_by": req.sent_by
    }).execute()
    
    campaign_id = campaign.data[0]["id"]
    client = await get_client(req.account_number)
    background_tasks.add_task(send_bulk, campaign_id, client, req.chat_ids, req.message, req.delay_seconds)
    
    return {"campaign_id": campaign_id, "status": "started", "total": len(req.chat_ids)}

@router.get("/")
def get_campaigns():
    result = supabase.table("campaigns").select("*").order("created_at", desc=True).execute()
    return result.data

@router.get("/{campaign_id}/progress")
def get_progress(campaign_id: str):
    result = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    c = result.data[0]
    total = c["total_chats"] or 1
    return {
        "campaign_id": campaign_id,
        "status": c["status"],
        "total": c["total_chats"],
        "sent": c["sent_count"],
        "failed": c["failed_count"],
        "progress_percent": round((c["sent_count"] + c["failed_count"]) / total * 100)
    }

@router.get("/{campaign_id}/logs")
def get_logs(campaign_id: str):
    result = supabase.table("campaign_logs").select("*").eq("campaign_id", campaign_id).execute()
    return result.data
