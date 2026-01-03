import uuid
from pydantic import BaseModel, EmailStr, Field

class MessageBase(BaseModel):
    sender_name: str = Field(..., min_length=10)
    sender_email: EmailStr
    content: str = Field(..., min_length=600)

class MessageCreate(MessageBase):
    """Schema usado para criação de mensagens"""
    pass

class MessageDB(MessageBase):
    """Schema usado para retorno de mensagens do banco"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

