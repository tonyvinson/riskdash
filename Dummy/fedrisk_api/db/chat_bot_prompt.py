import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import ChatBotPrompt
from fedrisk_api.schema.chat_bot_prompt import CreateChatBotPrompt, UpdateChatBotPrompt

LOGGER = logging.getLogger(__name__)


def create_chat_bot_prompt(chat_bot_prompt: CreateChatBotPrompt, db: Session):
    chat_bot_prompt = ChatBotPrompt(**chat_bot_prompt.dict())
    db.add(chat_bot_prompt)
    db.commit()
    return chat_bot_prompt


def get_chat_bot_prompt(
    db: Session,
):
    queryset = db.query(ChatBotPrompt).all()
    return queryset


def get_chat_bot_prompt_by_id(db: Session, chat_bot_prompt_id: int):
    queryset = db.query(ChatBotPrompt).filter(ChatBotPrompt.id == chat_bot_prompt_id).first()
    return queryset


def update_chat_bot_prompt_by_id(
    chat_bot_prompt: UpdateChatBotPrompt, db: Session, chat_bot_prompt_id: int
):
    queryset = db.query(ChatBotPrompt).filter(ChatBotPrompt.id == chat_bot_prompt_id)

    if not queryset.first():
        return False

    queryset.update(chat_bot_prompt.dict(exclude_unset=True))
    db.commit()
    return True


def delete_chat_bot_prompt_by_id(db: Session, chat_bot_prompt_id: int):
    chat_bot_prompt = db.query(ChatBotPrompt).filter(ChatBotPrompt.id == chat_bot_prompt_id).first()

    if not chat_bot_prompt:
        return False

    db.delete(chat_bot_prompt)
    db.commit()
    return True
