from pyrogram import Client
import os
import asyncio

sessions = {}

async def get_client(account_number: int) -> Client:
    key = f"account{account_number}"
    if key in sessions and sessions[key].is_connected:
        return sessions[key]
    
    api_id = int(os.getenv(f"ACCOUNT{account_number}_API_ID"))
    api_hash = os.getenv(f"ACCOUNT{account_number}_API_HASH")
    name = os.getenv(f"ACCOUNT{account_number}_NAME", f"account{account_number}")
    
    client = Client(
        name=f"session_{account_number}",
        api_id=api_id,
        api_hash=api_hash,
        sessions_directory="sessions/"
    )
    await client.start()
    sessions[key] = client
    return client

async def disconnect_client(account_number: int):
    key = f"account{account_number}"
    if key in sessions:
        await sessions[key].stop()
        del sessions[key]
