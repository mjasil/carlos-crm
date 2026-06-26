from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os, asyncio, httpx, traceback

load_dotenv()

from routes import accounts, folders, contacts, campaigns, templates, auth

app = FastAPI(title="Carlos CRM", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(folders.router, prefix="/api/folders", tags=["Folders"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])

@app.get("/")
def root():
    return {"status": "Carlos CRM Backend Running ✅"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug/{account_number}")
async def debug(account_number: int):
    import os
    session = os.getenv(f"ACCOUNT{account_number}_SESSION")
    api_id = os.getenv(f"ACCOUNT{account_number}_API_ID")
    api_hash = os.getenv(f"ACCOUNT{account_number}_API_HASH")
    return {
        "api_id": api_id,
        "api_hash_exists": bool(api_hash),
        "session_length": len(session) if session else 0,
        "session_start": session[:20] if session else None
    }

@app.get("/test-connect/{account_number}")
async def test_connect(account_number: int):
    try:
        from telegram_client import get_client
        client = await get_client(account_number)
        me = await client.get_me()
        return {"success": True, "name": me.first_name, "phone": str(me.phone_number)}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

async def self_ping():
    await asyncio.sleep(60)
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.get("https://carlos-crm.onrender.com/health", timeout=10)
        except:
            pass
        await asyncio.sleep(240)

@app.on_event("startup")
async def startup():
    asyncio.create_task(self_ping())
