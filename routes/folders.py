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

        # Build a set of peer IDs from folder
        folder_peer_ids = set()
        peer_types = {}
        for peer in all_peers:
            if isinstance(peer, InputPeerUser):
                folder_peer_ids.add(peer.user_id)
                peer_types[peer.user_id] = "personal"
            elif isinstance(peer, InputPeerChannel):
                folder_peer_ids.add(peer.channel_id)
                peer_types[peer.channel_id] = "channel"
            elif isinstance(peer, InputPeerChat):
                folder_peer_ids.add(peer.chat_id)
                peer_types[peer.chat_id] = "group"

        # Get all dialogs and filter by folder peers
        chats = []
        async for dialog in client.get_dialogs():
            chat = dialog.chat
            raw_id = abs(chat.id)
            # Match by stripping -100 prefix for channels
            match_id = raw_id
            if str(chat.id).startswith("-100"):
                match_id = int(str(raw_id)[3:]) if len(str(raw_id)) > 3 else raw_id

            if match_id in folder_peer_ids or raw_id in folder_peer_ids:
                chat_type = peer_types.get(match_id) or peer_types.get(raw_id, "personal")
                actual_type = str(getattr(chat, 'type', ''))
                if 'BOT' in actual_type:
                    chat_type = 'bot'
                elif 'SUPERGROUP' in actual_type or 'GROUP' in actual_type:
                    chat_type = 'group'
                elif 'CHANNEL' in actual_type:
                    chat_type = 'channel'

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

            if len(chats) >= len(folder_peer_ids):
                break

        return {"folder_id": folder_id, "chats": chats, "total": len(chats)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
