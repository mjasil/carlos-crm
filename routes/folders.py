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
        
        peers = list(getattr(target, 'include_peers', []) or [])
        pinned = list(getattr(target, 'pinned_peers', []) or [])
        all_peers = peers + pinned

        # Fast method: read directly from peer objects without get_chat
        chats = []
        for peer in all_peers:
            try:
                if isinstance(peer, InputPeerUser):
                    chats.append({
                        "chat_id": peer.user_id,
                        "name": f"User {peer.user_id}",
                        "username": None,
                        "type": "personal",
                        "access_hash": peer.access_hash
                    })
                elif isinstance(peer, InputPeerChannel):
                    chats.append({
                        "chat_id": int(f"-100{peer.channel_id}"),
                        "name": f"Channel {peer.channel_id}",
                        "username": None,
                        "type": "channel",
                        "access_hash": peer.access_hash
                    })
                elif isinstance(peer, InputPeerChat):
                    chats.append({
                        "chat_id": -peer.chat_id,
                        "name": f"Group {peer.chat_id}",
                        "username": None,
                        "type": "group",
                        "access_hash": 0
                    })
            except Exception:
                continue

        # Try to get names from dialogs cache (fast, no API calls)
        try:
            chat_ids_set = {abs(c["chat_id"]) for c in chats}
            dialog_names = {}
            async for dialog in client.get_dialogs(limit=500):
                chat = dialog.chat
                raw_id = abs(chat.id)
                if raw_id in chat_ids_set or chat.id in {c["chat_id"] for c in chats}:
                    name = getattr(chat, 'title', None)
                    if not name:
                        first = getattr(chat, 'first_name', '') or ''
                        last = getattr(chat, 'last_name', '') or ''
                        name = f"{first} {last}".strip()
                    dialog_names[chat.id] = name or getattr(chat, 'username', None) or str(chat.id)
            
            # Update names
            for c in chats:
                if c["chat_id"] in dialog_names:
                    c["name"] = dialog_names[c["chat_id"]]
        except Exception:
            pass

        return {"folder_id": folder_id, "chats": chats, "total": len(chats)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
