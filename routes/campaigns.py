from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from database import supabase
from telegram_client import get_client
from typing import Optional
import asyncio, datetime, os, tempfile

router = APIRouter()

# Global state for pause/cancel
campaign_controls = {}

async def send_bulk(campaign_id, client, chat_ids, message, delay, file_path=None, file_type=None, parse_mode="markdown"):
    campaign_controls[campaign_id] = {"paused": False, "cancelled": False}
    
    supabase.table("campaigns").update({
        "status": "running",
        "started_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", campaign_id).execute()
    
    sent = 0
    failed = 0
    
    for chat_id in chat_ids:
        # Check cancelled
        ctrl = campaign_controls.get(campaign_id, {})
        if ctrl.get("cancelled"):
            break
        
        # Check paused - wait until unpaused
        while campaign_controls.get(campaign_id, {}).get("paused"):
            await asyncio.sleep(1)
            ctrl = campaign_controls.get(campaign_id, {})
            if ctrl.get("cancelled"):
                break
        
        if campaign_controls.get(campaign_id, {}).get("cancelled"):
            break

        try:
            if file_path and os.path.exists(file_path):
                if file_type == "photo":
                    await client.send_photo(chat_id, file_path, caption=message or None, parse_mode=parse_mode if message else None)
                elif file_type == "audio":
                    await client.send_audio(chat_id, file_path, caption=message or None)
                elif file_type == "video":
                    await client.send_video(chat_id, file_path, caption=message or None, parse_mode=parse_mode if message else None)
                else:
                    await client.send_document(chat_id, file_path, caption=message or None)
            else:
                await client.send_message(chat_id, message, parse_mode=parse_mode)
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
                "error_message": str(e)[:200]
            }).execute()
        
        supabase.table("campaigns").update({
            "sent_count": sent,
            "failed_count": failed
        }).eq("id", campaign_id).execute()
        await asyncio.sleep(delay)
    
    if file_path and os.path.exists(file_path):
        try: os.remove(file_path)
        except: pass
    
    ctrl = campaign_controls.get(campaign_id, {})
    final_status = "cancelled" if ctrl.get("cancelled") else "completed"
    supabase.table("campaigns").update({
        "status": final_status,
        "completed_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", campaign_id).execute()
    
    campaign_controls.pop(campaign_id, None)

@router.post("/send")
async def send_campaign(
    background_tasks: BackgroundTasks,
    account_number: int = Form(...),
    folder_id: int = Form(...),
    message: str = Form(""),
    chat_ids: str = Form(...),
    delay_seconds: int = Form(3),
    sent_by: str = Form("admin"),
    parse_mode: str = Form("markdown"),
    file: Optional[UploadFile] = File(None)
):
    ids = [int(x) for x in chat_ids.split(",") if x.strip()]
    
    file_path = None
    file_type = None
    if file and file.filename:
        ext = file.filename.split(".")[-1].lower()
        if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
            file_type = "photo"
        elif ext in ["mp3", "ogg", "wav", "m4a"]:
            file_type = "audio"
        elif ext in ["mp4", "mov", "avi"]:
            file_type = "video"
        else:
            file_type = "document"
        
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        content = await file.read()
        tmp.write(content)
        tmp.close()
        file_path = tmp.name

    campaign = supabase.table("campaigns").insert({
        "message": message,
        "total_chats": len(ids),
        "sent_count": 0,
        "failed_count": 0,
        "status": "pending",
        "sent_by": sent_by
    }).execute()
    
    campaign_id = campaign.data[0]["id"]
    client = await get_client(account_number)
    background_tasks.add_task(
        send_bulk, campaign_id, client, ids,
        message, delay_seconds, file_path, file_type, parse_mode
    )
    
    return {"campaign_id": campaign_id, "status": "started", "total": len(ids)}

@router.post("/{campaign_id}/pause")
def pause_campaign(campaign_id: str):
    if campaign_id in campaign_controls:
        campaign_controls[campaign_id]["paused"] = True
        supabase.table("campaigns").update({"status": "paused"}).eq("id", campaign_id).execute()
        return {"status": "paused"}
    raise HTTPException(status_code=404, detail="Campaign not running")

@router.post("/{campaign_id}/resume")
def resume_campaign(campaign_id: str):
    if campaign_id in campaign_controls:
        campaign_controls[campaign_id]["paused"] = False
        supabase.table("campaigns").update({"status": "running"}).eq("id", campaign_id).execute()
        return {"status": "resumed"}
    raise HTTPException(status_code=404, detail="Campaign not found")

@router.post("/{campaign_id}/cancel")
def cancel_campaign(campaign_id: str):
    if campaign_id in campaign_controls:
        campaign_controls[campaign_id]["cancelled"] = True
        return {"status": "cancelling"}
    raise HTTPException(status_code=404, detail="Campaign not running")

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
    is_paused = campaign_controls.get(campaign_id, {}).get("paused", False)
    return {
        "campaign_id": campaign_id,
        "status": "paused" if is_paused else c["status"],
        "total": c["total_chats"],
        "sent": c["sent_count"],
        "failed": c["failed_count"],
        "progress_percent": round((c["sent_count"] + c["failed_count"]) / total * 100)
    }

@router.get("/{campaign_id}/logs")
def get_logs(campaign_id: str):
    result = supabase.table("campaign_logs").select("*").eq("campaign_id", campaign_id).execute()
    return result.data
