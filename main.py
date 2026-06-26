from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

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
