from datetime import datetime

from pydantic import BaseModel


class CreateChatBotPrompt(BaseModel):
    prompt: str
    message: str


class UpdateChatBotPrompt(BaseModel):
    prompt: str = None
    message: str = None

    class Config:
        orm_mode = True


class DisplayChatBotPrompt(BaseModel):
    id: int
    prompt: str
    message: str
    created: datetime = None

    class Config:
        orm_mode = True
