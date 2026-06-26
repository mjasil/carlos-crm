from fastapi import APIRouter, HTTPException
from telegram_client import get_client
from pyrogram.raw.functions.messages import GetDialogFilters
from pyrogram.raw.types import InputPeerUser, InputPeerChannel, InputPeerChat

router = APIRouter()

async def fetch_filters(client):
    result = await client.invoke(GetDialogFilters())
    if isinstance(result, list):
        return result
    return getattr(result, 'filters', result)

@router.get("/{account_number}")
async def get_folders(account_number: int):
    try:
        client = await get_client(account_number)
        filters = await fetch_filters(client)
        folders = []
        for f in filters:
            if hasattr(f, 'title'):
                peers = getattr(f, 'include_peers', []) or []
                folders.append({
                    "id": f.id,
                    "title": f.title,
                    "chat_count": len(peers)
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
        
        peers = getattr(target, 'include_peers', []) or []
        pinned = getattr(target, 'pinned_peers', []) or []
        all_peers = list(peers) + list(pinned)
        
        chats = []
        for peer in all_peers:
            try:
                # Get ID and type directly from peer object
                if isinstance(peer, InputPeerUser):
                    peer_id = peer.user_id
                    chat_type = "personal"
                    chat = await client.get_chat(peer_id)
                elif isinstance(peer, InputPeerChannel):
                    peer_id = peer.channel_id
                    chat_type = "channel"
                    chat = await client.get_chat(int(f"-100{peer_id}"))
                elif isinstance(peer, InputPeerChat):
                    peer_id = peer.chat_id
                    chat_type = "group"
                    chat = await client.get_chat(-peer_id)
                else:
                    continue

                name = getattr(chat, 'title', None)
                if not name:
                    first = getattr(chat, 'first_name', '') or ''
                    last = getattr(chat, 'last_name', '') or ''
                    name = f"{first} {last}".strip()

                actual_type = str(getattr(chat, 'type', ''))
                if 'BOT' in actual_type:
                    chat_type = 'bot'
                elif 'SUPERGROUP' in actual_type or 'GROUP' in actual_type:
                    chat_type = 'group'
                elif 'CHANNEL' in actual_type:
                    chat_type = 'channel'

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
