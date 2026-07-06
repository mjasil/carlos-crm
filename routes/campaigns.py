from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from database import supabase
from telegram_client import get_client
from typing import Optional, List
import asyncio, datetime, os, tempfile

router = APIRouter()
campaign_controls = {}

def get_file_type(filename):
    ext = filename.split(".")[-1].lower()
    if ext in ["jpg","jpeg","png","gif","webp"]: return "photo"
    elif ext in ["mp3","ogg","wav","m4a"]: return "audio"
    elif ext in ["mp4","mov","avi"]: return "video"
    return "document"

async def save_file(file):
    ext = file.filename.split(".")[-1].lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.write(await file.read())
    tmp.close()
    return tmp.name, get_file_type(file.filename)

async def send_to_chat(client, chat_id, message, files):
    if not files:
        await client.send_message(chat_id, message)
        return
    
    if len(files) == 1:
        path, ftype = files[0]
        if ftype == "photo":
            await client.send_photo(chat_id, path, caption=message or None)
        elif ftype == "audio":
            await client.send_audio(chat_id, path, caption=message or None)
        elif ftype == "video":
            await client.send_video(chat_id, path, caption=message or None)
        else:
            await client.send_document(chat_id, path, caption=message or None)
        return
    
    # Multiple files - send as media group if all photos/videos
    photo_video = [(p, t) for p, t in files if t in ["photo", "video"]]
    others = [(p, t) for p, t in files if t not in ["photo", "video"]]
    
    if photo_video:
        from pyrogram.types import InputMediaPhoto, InputMediaVideo
        media = []
        for i, (path, ftype) in enumerate(photo_video):
            cap = message if i == 0 else None
            if ftype == "photo":
                media.append(InputMediaPhoto(path, caption=cap))
            else:
                media.append(InputMediaVideo(path, caption=cap))
        await client.send_media_group(chat_id, media)
        message = None  # Already sent with first photo
    
    for path, ftype in others:
        if ftype == "audio":
            await client.send_audio(chat_id, path, caption=message or None)
        else:
            await client.send_document(chat_id, path, caption=message or None)
        message = None

async def send_bulk(campaign_id, client, chat_ids, message, delay, files=None):
    campaign_controls[campaign_id] = {"paused": False, "cancelled": False}
    files = files or []
    
    supabase.table("campaigns").update({
        "status": "running",
        "started_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", campaign_id).execute()
    
    sent = 0
    failed = 0
    
    for chat_id in chat_ids:
        ctrl = campaign_controls.get(campaign_id, {})
        if ctrl.get("cancelled"): break
        while campaign_controls.get(campaign_id, {}).get("paused"):
            await asyncio.sleep(1)
            if campaign_controls.get(campaign_id, {}).get("cancelled"): break
        if campaign_controls.get(campaign_id, {}).get("cancelled"): break

        try:
            await send_to_chat(client, chat_id, message, files)
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
    
    # Cleanup files
    for path, _ in files:
        try: os.remove(path)
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
    scheduled_at: str = Form(""),
    files: List[UploadFile] = File(default=[])
):
    ids = [int(x) for x in chat_ids.split(",") if x.strip()]
    
    # Save all uploaded files
    saved_files = []
    for file in files:
        if file and file.filename:
            path, ftype = await save_file(file)
            saved_files.append((path, ftype))

    campaign = supabase.table("campaigns").insert({
        "message": message,
        "total_chats": len(ids),
        "sent_count": 0,
        "failed_count": 0,
        "status": "scheduled" if scheduled_at else "pending",
        "sent_by": sent_by,
        "scheduled_at": scheduled_at if scheduled_at else None
    }).execute()
    
    campaign_id = campaign.data[0]["id"]
    client = await get_client(account_number)

    if scheduled_at:
        try:
            scheduled_time = datetime.datetime.fromisoformat(scheduled_at)
            delay_secs = (scheduled_time - datetime.datetime.utcnow()).total_seconds()
            if delay_secs > 0:
                async def run_scheduled():
                    await asyncio.sleep(delay_secs)
                    await send_bulk(campaign_id, client, ids, message, delay_seconds, saved_files)
                background_tasks.add_task(run_scheduled)
                return {"campaign_id": campaign_id, "status": "scheduled", "total": len(ids)}
        except: pass

    background_tasks.add_task(send_bulk, campaign_id, client, ids, message, delay_seconds, saved_files)
    return {"campaign_id": campaign_id, "status": "started", "total": len(ids)}

@router.post("/{campaign_id}/resend-failed")
async def resend_failed(campaign_id: str, background_tasks: BackgroundTasks, account_number: int = Form(1), delay_seconds: int = Form(3)):
    logs = supabase.table("campaign_logs").select("*").eq("campaign_id", campaign_id).eq("status", "failed").execute()
    if not logs.data:
        raise HTTPException(status_code=404, detail="No failed messages found")
    campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
    if not campaign.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    c = campaign.data[0]
    chat_ids = [log["chat_id"] for log in logs.data]
    new_campaign = supabase.table("campaigns").insert({
        "message": c["message"],
        "total_chats": len(chat_ids),
        "sent_count": 0,
        "failed_count": 0,
        "status": "pending",
        "sent_by": f"Resend of {campaign_id[:8]}"
    }).execute()
    new_id = new_campaign.data[0]["id"]
    client = await get_client(account_number)
    background_tasks.add_task(send_bulk, new_id, client, chat_ids, c["message"], delay_seconds)
    return {"campaign_id": new_id, "status": "started", "total": len(chat_ids)}

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
