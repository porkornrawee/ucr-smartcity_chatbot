from linebot.v3.messaging import (
    ReplyMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    LocationAction,
    CameraAction,
    FlexBox,
    FlexButton,
)

from app.config import GO_BACK_KEYWORD, CONFIRM_KEYWORD
from app.utils import flex_builder


def build_question_message(
    question_obj,
    show_go_back: bool = True,
    multi_select_pending: list = None,
    multi_select_max: int = None,
    step: int = 0,
    total: int = 0,
):
    """Build the LINE message for a survey question.

    The card body (progress bar, accent strip, multi-select tally) is built by
    the shared design-system builder in ``flex_builder`` (colours from
    ux_tokens). The tappable options are attached on top: message-action options
    become Flex footer buttons; native location / camera options can't live in a
    Flex button, so they go in the bubble's attached quick-reply bar instead.
    """
    already_selected = set(multi_select_pending or [])
    is_multi = getattr(question_obj, "type", None) == "multi_select"
    selected_list = list(multi_select_pending or [])
    max_sel = multi_select_max or getattr(question_obj, "max_selections", None) or 99

    footer_buttons = []
    quick_reply_items = []

    for opt in question_obj.options:
        # Skip options the user already picked
        if opt.value and opt.value in already_selected:
            continue

        if opt.action_type == "location":
            quick_reply_items.append(QuickReplyItem(action=LocationAction(label=opt.label)))
        elif opt.action_type == "camera":
            quick_reply_items.append(QuickReplyItem(action=CameraAction(label=opt.label)))
        else:  # "message"
            action = MessageAction(label=opt.label, text=opt.value if opt.value else opt.label)
            footer_buttons.append(FlexButton(action=action, style="secondary"))

    if is_multi and selected_list:
        confirm_label = f"✅ ยืนยัน ({len(selected_list)}/{max_sel})"
        footer_buttons.append(FlexButton(
            action=MessageAction(label=confirm_label, text=CONFIRM_KEYWORD),
            style="primary",
        ))

    if show_go_back:
        footer_buttons.append(FlexButton(
            action=MessageAction(label="◀️ ย้อนกลับ", text=GO_BACK_KEYWORD),
            style="link",
        ))

    bubble = flex_builder.question_bubble(
        question_text=question_obj.text,
        step_index=step,
        route_len=total,
        multi_select_pending=selected_list if is_multi else None,
        multi_select_max=max_sel if is_multi else None,
    )
    if footer_buttons:
        bubble.footer = FlexBox(layout="vertical", contents=footer_buttons, spacing="sm")

    quick_reply = QuickReply(items=quick_reply_items) if quick_reply_items else None
    return flex_builder.to_message(_alt_text(question_obj.text), bubble, quick_reply)


def _alt_text(text: str) -> str:
    """LINE caps altText at 400 chars."""
    return text if len(text) <= 400 else text[:397] + "..."


async def send_question(
    reply_token: str,
    question_obj,
    line_bot_api,
    show_go_back: bool = True,
    multi_select_pending: list = None,
    multi_select_max: int = None,
    step: int = 0,
    total: int = 0,
):
    message = build_question_message(
        question_obj, show_go_back, multi_select_pending, multi_select_max, step, total
    )
    await line_bot_api.reply_message(
        ReplyMessageRequest(reply_token=reply_token, messages=[message])
    )


async def send_text(reply_token: str, text: str, line_bot_api):
    """Reply with a plain text message."""
    await line_bot_api.reply_message(
        ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
    )
