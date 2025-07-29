import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import chat_bot_prompt as db_chat_bot_prompt
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.chat_bot_prompt import (
    CreateChatBotPrompt,
    DisplayChatBotPrompt,
    UpdateChatBotPrompt,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_chat_bot_prompt_permission,
    delete_chat_bot_prompt_permission,
    update_chat_bot_prompt_permission,
    view_chat_bot_prompt_permission,
)

# from fedrisk_api.utils.utils import PaginateResponse, pagination

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/chat_bot_prompts", tags=["chat_bot_prompts"])


@router.post(
    "/",
    response_model=DisplayChatBotPrompt,
    dependencies=[Depends(create_chat_bot_prompt_permission)],
)
def create_chat_bot_prompt(
    request: CreateChatBotPrompt, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        chat_bot_prompt = db_chat_bot_prompt.create_chat_bot_prompt(chat_bot_prompt=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Chat Bot Prompt Error. Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"ChatBot Prompt with prompt '{request.prompt}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)
    return chat_bot_prompt


@router.get(
    "/",
    response_model=List[DisplayChatBotPrompt],
    dependencies=[Depends(view_chat_bot_prompt_permission)],
)
def get_all_chat_bot_prompts(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_chat_bot_prompt.get_chat_bot_prompt(
        db=db,
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayChatBotPrompt,
    dependencies=[Depends(view_chat_bot_prompt_permission)],
)
def get_chat_bot_prompt_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_chat_bot_prompt.get_chat_bot_prompt_by_id(db=db, chat_bot_prompt_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ChatBot prompt with specified id does not exists",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_chat_bot_prompt_permission)])
def update_chat_bot_prompt_by_id(
    request: UpdateChatBotPrompt, id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        queryset = db_chat_bot_prompt.update_chat_bot_prompt_by_id(
            chat_bot_prompt=request, db=db, chat_bot_prompt_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ChatBot Prompt with specified id does not exists",
            )
        return {"detail": "Successfully updated ChatBot Prompt."}
    except IntegrityError as ie:
        LOGGER.exception("Get Project_Group Error - Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"ChatBot Prompt with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_chat_bot_prompt_permission)])
def delete_chat_bot_prompt_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_chat_bot_prompt.delete_chat_bot_prompt_by_id(db=db, chat_bot_prompt_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ChatBot Prompt with sepcified id does not exists",
        )
    return {"detail": "Successfully deleted ChatBot Prompt."}
