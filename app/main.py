import os
import uuid
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

# 📦 Carregar variáveis de ambiente
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_SECRET = os.getenv("API_SECRET")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# 🚦 Configurar limiter (15 req/min por IP)
limiter = Limiter(key_func=get_remote_address, default_limits=["15/minute"])

app = FastAPI(title="Mensageria API")
app.state.limiter = limiter

# Tratamento de erro de limite
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests, try again later."}
    )

# 🔒 Dependência para verificar API Key
async def verify_api_key(authorization: str = Header(...)):
    if authorization != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

# 📝 Modelo de entrada
class MessageCreate(BaseModel):
    sender_name: str = Field(..., min_length=10)
    sender_email: EmailStr
    content: str = Field(..., min_length=600)

# 📤 Modelo de saída
class MessageDB(MessageCreate):
    id: uuid.UUID

# 🔧 Cliente HTTP assíncrono para Supabase
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

# 🔔 Função para enviar email via Brevo
async def send_email_notification(msg: MessageCreate):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "Mensageria API", "email": "no-reply@seudominio.com"},
        "to": [{"email": "stafproject125bpm@gmail.com"}],  
        "subject": "Nova mensagem recebida",
        "htmlContent": f"""
            <h3>Nova mensagem recebida</h3>
            <p><strong>Nome:</strong> {msg.sender_name}</p>
            <p><strong>Email:</strong> {msg.sender_email}</p>
            <p><strong>Mensagem:</strong> {msg.content}</p>
        """
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            print("Erro ao enviar email:", resp.text)

#  Criar mensagem com UUID + enviar email
@app.get("/", summary="Rota raiz")
async def root():
    return {"message": "API Mensageria rodando "}


@app.post("/messages", response_model=MessageDB,
          summary="Cria uma nova mensagem",
          dependencies=[Depends(verify_api_key)])
@limiter.limit("15/minute")
async def create_message(request: Request, msg: MessageCreate):  #  request adicionado
    data = {
        "id": str(uuid.uuid4()),
        "content": msg.content,
        "sender_email": msg.sender_email,
        "sender_name": msg.sender_name,
        "user_id": str(uuid.uuid4())
    }
    result = await supabase_request("POST", "messages", json=data)
    await send_email_notification(msg)
    return result[0] if result else data

#  Listar todas as mensagens
@app.get("/messages", summary="Lista todas as mensagens",
        dependencies=[Depends(verify_api_key)])
@limiter.limit("15/minute")
async def list_messages(request: Request):  # request adicionado
    result = await supabase_request("GET", "messages")
    return result

#  Buscar mensagem por ID
@app.get("/messages/{id}", response_model=MessageDB,
         summary="Busca mensagem por ID",
         dependencies=[Depends(verify_api_key)])
@limiter.limit("15/minute")
async def get_message(request: Request, id: uuid.UUID):  #  request adicionado
    result = await supabase_request("GET", f"messages?id=eq.{id}")
    if not result:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return result[0]

#  Entrypoint
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

