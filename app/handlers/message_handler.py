from sqlalchemy.ext.asyncio import AsyncSession
from linebot.v3.webhooks import TextMessageContent, LocationMessageContent, ImageMessageContent
from app.handlers.info_handler import handle_info_request
from app.handlers.stat_handler import handle_stat_request
from app.handlers.report_handler import handle_report_request
from app.handlers.contact_handler import handle_contact_request
from app.handlers.chatbot_handler import handle_chatbot_chat, handle_chatbot_location, handle_chatbot_image


async def route_message_event(event, line_bot_api, db: AsyncSession):
    """Single router for a MessageEvent: dispatch by content type."""
    message = event.message
    if isinstance(message, TextMessageContent):
        await handle_text_message(event, line_bot_api, db)
    elif isinstance(message, LocationMessageContent):
        await handle_chatbot_location(event, line_bot_api, db)
    elif isinstance(message, ImageMessageContent):
        await handle_chatbot_image(event, line_bot_api, db)


async def handle_text_message(event, line_bot_api, db: AsyncSession):
    """Main Router for incoming text messages."""
    text = event.message.text.strip()

    # 1. Route to Info Handler
    if text == "ข้อมูลโครงการ":
        await handle_info_request(event, line_bot_api)
        return

    # 2. Route to Stat Handler
    if text == "สรุปผล":
        await handle_stat_request(event, line_bot_api)
        return

    # 3. Route to Report Handler
    if text in ("รายงานปัญหา", "แจ้งปัญหา"):
        await handle_report_request(event, line_bot_api)
        return

    # 4. Route to Contact Handler
    if text == "ติดต่อ":
        await handle_contact_request(event, line_bot_api)
        return

    # 5. Route to Chatbot Handler (Default for other text/surveys)
    await handle_chatbot_chat(event, line_bot_api, db, text)
