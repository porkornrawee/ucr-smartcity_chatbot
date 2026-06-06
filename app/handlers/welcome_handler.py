from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from linebot.v3.messaging import ReplyMessageRequest, TextMessage

from app.models import User
from app.config import WELCOME_STEP_1, WELCOME_STEP_2


async def handle_follow(event, line_bot_api, db: AsyncSession):
    """
    Handles the FollowEvent (user adds the bot / unblocks).
    Registers the user and sends the 2-step welcome that mirrors the
    prototype onboarding intro.
    """
    user_id = event.source.user_id

    # Register the user on first contact (idempotent)
    result = await db.execute(select(User).where(User.lineuser_id == user_id))
    if not result.scalars().first():
        db.add(User(lineuser_id=user_id))
        await db.commit()

    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text=WELCOME_STEP_1),
                TextMessage(text=WELCOME_STEP_2),
            ],
        )
    )
