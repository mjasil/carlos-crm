from fastapi import APIRouter, HTTPException
from database import supabase
from telegram_client import get_client
import asyncio

router = APIRouter()

@router.get("/{account_number}")
async def get_folders(account_number: int):
    try:
        client = await get_client(account_number)
        folders = await client.get_dialogs_filters()
        
        result = []
        for folder in folders:
            result.append({
                "id": folder.id,
                "title": folder.title,
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_number}/{folder_id}/chats")
async def get_folder_chats(account_number: int, folder_id: int):
    try:
        client = await get_client(account_number)
        folders = await client.get_dialogs_filters()
        
        target = None
        for f in folders:
            if f.id == folder_id:
                target = f
                break
        
        if not target:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        chats = []
        for peer in target.included_peers:
            try:
                chat = await client.get_chat(peer)
                chat_type = "personal"
                if hasattr(chat, 'type'):
                    if str(chat.type) in ["ChatType.GROUP", "ChatType.SUPERGROUP"]:
                        chat_type = "group"
                    elif str(chat.type) == "ChatType.CHANNEL":
                        chat_type = "channel"
                    elif str(chat.type) == "ChatType.BOT":
                        chat_type = "bot"
                
                chats.append({
                    "chat_id": chat.id,
                    "name": getattr(chat, 'title', None) or f"{getattr(chat, 'first_name', '')} {getattr(chat, 'last_name', '')}".strip(),
                    "username": getattr(chat, 'username', None),
                    "type": chat_type,
                })
            except:
                continue
        
        return {"folder_id": folder_id, "chats": chats, "total": len(chats)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
