from pyrogram import Client
import os

sessions = {}

async def get_client(account_number: int) -> Client:
    key = f"account{account_number}"
    if key in sessions:
        try:
            if sessions[key].is_connected:
                return sessions[key]
        except:
            pass

    api_id = int(os.getenv(f"ACCOUNT{account_number}_API_ID"))
    api_hash = os.getenv(f"ACCOUNT{account_number}_API_HASH")
    session_string = os.getenv(f"ACCOUNT{account_number}_SESSION")

    client = Client(
        name=f"account{account_number}",
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string,
        in_memory=True
    )

    await client.start()
    sessions[key] = client
    return client

async def disconnect_client(account_number: int):
    key = f"account{account_number}"
    if key in sessions:
        try:
            await sessions[key].stop()
        except:
            pass
        del sessions[key]
