from fastapi import APIRouter
from pydantic import BaseModel
from database import supabase

router = APIRouter()

class TemplateCreate(BaseModel):
    title: str
    message: str

@router.get("/")
def get_templates():
    result = supabase.table("templates").select("*").execute()
    return result.data

@router.post("/")
def create_template(t: TemplateCreate):
    result = supabase.table("templates").insert({"title": t.title, "message": t.message}).execute()
    return result.data[0]

@router.delete("/{template_id}")
def delete_template(template_id: str):
    supabase.table("templates").delete().eq("id", template_id).execute()
    return {"deleted": True}
