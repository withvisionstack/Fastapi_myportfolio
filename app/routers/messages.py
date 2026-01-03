import uuid
from fastapi import APIRouter, HTTPException
from app.models.messages import MessageCreate, MessageDB
import os
import httpx

# Configuração Supabase via variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

router = APIRouter(prefix="/messages", tags=["Mensagens"])

# 🔧 Cliente HTTP assíncrono
async def supabase_request(method: str, endpoint: str, json: dict = None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method,
            f"{SUPABASE_URL}/rest/v1/{endpoint}",
            headers=headers,
            json=json
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

# ✅ Criar mensagem
@router.post("/", response_model=MessageDB, summary="Cria uma nova mensagem")
async def create_message(msg: MessageCreate):
    data = {
        "id": str(uuid.uuid4()),
        "content": msg.content,
        "sender_email": msg.sender_email,
        "user_id": msg.sender_name
    }
    result = await supabase_request("POST", "messages", json=data)
    return result[0] if result else data

# ✅ Listar mensagens
@router.get("/", summary="Lista todas as mensagens")
async def list_messages():
    result = await supabase_request("GET", "messages")
    return result

# ✅ Buscar mensagem por UUID
@router.get("/{id}", response_model=MessageDB, summary="Busca mensagem por ID")
async def get_message(id: uuid.UUID):
    result = await supabase_request("GET", f"messages?id=eq.{id}")
    if not result:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return result[0]

