from sqlalchemy.ext.asyncio import AsyncSession
from app.services.survey_service import start_survey_session, process_survey_answer, resend_current_question
from app.services import survey_repository as repo
from app.services import survey_messages as messages
from app.config import (
    SURVEY_TRIGGER_MAP,
    GO_BACK_KEYWORD,
    GO_BACK_POSTBACK,
    RESTART_SURVEY_POSTBACK,
    CONTINUE_SURVEY_POSTBACK,
)


async def handle_chatbot_chat(event, line_bot_api, db: AsyncSession, text: str):
    """Handles the Chatbot-based survey/chat flow."""
    if text in SURVEY_TRIGGER_MAP:
        target_version = SURVEY_TRIGGER_MAP[text]
        # issue #19: ถ้ามี session ค้างอยู่ ให้ถามก่อน ไม่ลบทันที
        active = await repo.load_session(db, event.source.user_id)
        if active:
            await messages.send_restart_confirm(event.reply_token, target_version, line_bot_api)
            return True
        await start_survey_session(event.source.user_id, target_version, event.reply_token, line_bot_api, db)
        return True

    # Otherwise, it might be an answer to an ongoing survey
    await process_survey_answer(event.source.user_id, text, event.reply_token, line_bot_api, db)
    return True


async def handle_chatbot_postback(event, line_bot_api, db: AsyncSession):
    """Routes PostbackEvent data to the correct survey action (issue #18)."""
    data = event.postback.data
    user_id = event.source.user_id
    reply_token = event.reply_token

    if data == GO_BACK_POSTBACK:
        await process_survey_answer(user_id, GO_BACK_KEYWORD, reply_token, line_bot_api, db)
    elif data.startswith(f"{RESTART_SURVEY_POSTBACK}:"):
        version = data.split(":", 1)[1]
        await start_survey_session(user_id, version, reply_token, line_bot_api, db)
    elif data == CONTINUE_SURVEY_POSTBACK:
        await resend_current_question(user_id, reply_token, line_bot_api, db)


async def handle_chatbot_location(event, line_bot_api, db: AsyncSession):
    """Handles incoming location messages for the chatbot."""
    answer_data = {
        "lat": event.message.latitude,
        "lng": event.message.longitude,
    }
    await process_survey_answer(event.source.user_id, answer_data, event.reply_token, line_bot_api, db)


async def handle_chatbot_image(event, line_bot_api, db: AsyncSession):
    """Handles incoming image messages for the chatbot."""
    answer_data = {"image_id": event.message.id}
    await process_survey_answer(event.source.user_id, answer_data, event.reply_token, line_bot_api, db)
