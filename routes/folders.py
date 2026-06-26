from fastapi import APIRouter, HTTPException
from telegram_client import get_client
from pyrogram.raw.functions.messages import GetDialogFilters

router = APIRouter()

async def fetch_filters(client):
    result = await client.invoke(GetDialogFilters())
    # result is a list directly
    if isinstance(result, list):
        return result
    # or it has .filters
    return getattr(result, 'filters', result)

@router.get("/{account_number}")
async def get_folders(account_number: int):
    try:
        client = await get_client(account_number)
        filters = await fetch_filters(client)
        
        folders = []
        for f in filters:
            if hasattr(f, 'title'):
                folders.append({
                    "id": f.id,
                    "title": f.title,
                })
        return folders
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_number}/{folder_id}/chats")
async def get_folder_chats(account_number: int, folder_id: int):
    try:
        client = await get_client(account_number)
        filters = await fetch_filters(client)
        
        target = None
        for f in filters:
            if hasattr(f, 'id') and f.id == folder_id:
                target = f
                break
        
        if not target:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        chats = []
        peers = getattr(target, 'include_peers', []) or getattr(target, 'included_peers', [])
        
        for peer in peers:
            try:
                resolved = await client.resolve_peer(peer)
                chat = await client.get_chat(resolved)
                chat_type = "personal"
                t = str(chat.type)
                if "GROUP" in t or "SUPERGROUP" in t:
                    chat_type = "group"
                elif "CHANNEL" in t:
                    chat_type = "channel"
                elif "BOT" in t:
                    chat_type = "bot"
                
                name = getattr(chat, 'title', None)
                if not name:
                    first = getattr(chat, 'first_name', '') or ''
                    last = getattr(chat, 'last_name', '') or ''
                    name = f"{first} {last}".strip()
                
                chats.append({
                    "chat_id": chat.id,
                    "name": name or "Unknown",
                    "username": getattr(chat, 'username', None),
                    "type": chat_type,
                })
            except Exception:
                continue
        
        return {"folder_id": folder_id, "chats": chats, "total": len(chats)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
