from linebot.v3.messaging import ReplyMessageRequest
from app.config import CONTACT_TITLE, CONTACT_SUB, CONTACT_LIST
from app.utils import flex_builder
from app.utils.ux_tokens import ACCENT


async def handle_contact_request(event, line_bot_api):
    """Handles the 'ติดต่อ' request from the Rich Menu (contactFlex card)."""
    bubble = flex_builder.contact_bubble(
        title=CONTACT_TITLE,
        sub=CONTACT_SUB,
        contacts=CONTACT_LIST,
        accent_color=ACCENT.CYAN,
    )
    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[flex_builder.to_message("ติดต่อทีมงาน", bubble)],
        )
    )
