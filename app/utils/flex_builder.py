"""
flex_builder.py — Builds LINE FlexMessage cards for the survey UI.

Hybrid rendering strategy (see docs/uxui-tokens.md):
- The FlexMessage *card* carries the visual identity (progress bar, accent,
  question text). Some questions have up to 12 options, which do not fit as
  Flex buttons, so the tappable options live in a QuickReply attached to the
  same message (built in survey_service).

All colours come from ux_tokens — never hard-code hex here.
"""
from typing import List, Optional

from linebot.v3.messaging import (
    FlexMessage,
    FlexBubble,
    FlexBox,
    FlexText,
    FlexSeparator,
    QuickReply,
)

from app.utils.ux_tokens import COLOR, ACCENT


def _bar(width_pct: int, fill_color: str) -> FlexBox:
    """A thin progress bar: a filled segment over a light track."""
    width_pct = max(0, min(100, width_pct))
    track = FlexBox(
        layout="vertical",
        contents=[],
        height="6px",
        background_color=COLOR.BRAND_LIGHT,
        corner_radius="999px",
    )
    if width_pct <= 0:
        return track
    fill = FlexBox(
        layout="vertical",
        contents=[],
        width=f"{width_pct}%",
        height="6px",
        background_color=fill_color,
        corner_radius="999px",
    )
    # Overlay fill on the track by stacking in a fixed-height container.
    return FlexBox(
        layout="vertical",
        contents=[fill],
        height="6px",
        background_color=COLOR.BRAND_LIGHT,
        corner_radius="999px",
    )


def _accent_strip(color: str) -> FlexBox:
    return FlexBox(
        layout="vertical",
        contents=[],
        height="6px",
        width="48px",
        background_color=color,
        corner_radius="999px",
    )


def question_bubble(
    question_text: str,
    step_index: int,
    route_len: int,
    accent_color: Optional[str] = None,
    multi_select_pending: Optional[List[str]] = None,
    multi_select_max: Optional[int] = None,
) -> FlexBubble:
    """Card shown for every survey question (optionFlex / multiFlex)."""
    accent_color = accent_color or COLOR.BRAND
    route_len = max(1, route_len)
    human_step = min(step_index + 1, route_len)
    pct = round(human_step / route_len * 100)

    header_row = FlexBox(
        layout="horizontal",
        contents=[
            FlexText(
                text=f"ข้อ {human_step} จาก {route_len}",
                size="xs",
                color=COLOR.HINT,
                flex=1,
            ),
            FlexText(
                text=f"{pct}%",
                size="xs",
                color=COLOR.HINT,
                align="end",
            ),
        ],
    )

    body_contents: list = [
        header_row,
        _bar(pct, accent_color),
        _accent_strip(accent_color),
        FlexText(
            text=question_text,
            size="lg",
            weight="bold",
            color=COLOR.TEXT,
            wrap=True,
        ),
    ]

    # multi_select: show running selection + how many more can be picked
    if multi_select_pending is not None:
        chosen = ", ".join(multi_select_pending) if multi_select_pending else "—"
        cap = (
            f"เลือกแล้ว {len(multi_select_pending)}/{multi_select_max}"
            if multi_select_max
            else f"เลือกแล้ว {len(multi_select_pending)}"
        )
        body_contents.append(FlexSeparator(margin="md"))
        body_contents.append(
            FlexText(text=cap, size="xs", color=COLOR.MUTED, margin="sm")
        )
        body_contents.append(
            FlexText(text=chosen, size="sm", color=COLOR.BRAND_DARK, wrap=True)
        )

    return FlexBubble(
        size="kilo",
        body=FlexBox(
            layout="vertical",
            spacing="md",
            padding_all="16px",
            background_color=COLOR.SURFACE,
            contents=body_contents,
        ),
    )


def info_bubble(title: str, body_text: str, accent_color: Optional[str] = None) -> FlexBubble:
    """Static informational card (infoFlex) — e.g. project info."""
    accent_color = accent_color or COLOR.BRAND
    return FlexBubble(
        size="kilo",
        body=FlexBox(
            layout="vertical",
            spacing="md",
            padding_all="16px",
            background_color=COLOR.SURFACE,
            contents=[
                _accent_strip(accent_color),
                FlexText(text=title, size="lg", weight="bold", color=COLOR.TEXT, wrap=True),
                FlexText(text=body_text, size="sm", color=COLOR.MUTED, wrap=True),
            ],
        ),
    )


def summary_bubble(title: str, lines: List[str], accent_color: Optional[str] = None) -> FlexBubble:
    """Completion / thank-you card (summaryFlex)."""
    accent_color = accent_color or ACCENT.MINT
    contents: list = [
        _accent_strip(accent_color),
        FlexText(text=title, size="lg", weight="bold", color=COLOR.TEXT, wrap=True),
        FlexSeparator(margin="md"),
    ]
    for ln in lines:
        contents.append(FlexText(text=ln, size="sm", color=COLOR.MUTED, wrap=True, margin="sm"))
    return FlexBubble(
        size="kilo",
        body=FlexBox(
            layout="vertical",
            spacing="sm",
            padding_all="16px",
            background_color=COLOR.SURFACE,
            contents=contents,
        ),
    )


def contact_bubble(title: str, sub: str, contacts: List[dict], accent_color: Optional[str] = None) -> FlexBubble:
    """Contact card (contactFlex). Each contact: {icon, name, detail}."""
    accent_color = accent_color or ACCENT.CYAN
    contents: list = [
        _accent_strip(accent_color),
        FlexText(text=title, size="lg", weight="bold", color=COLOR.TEXT, wrap=True),
        FlexText(text=sub, size="sm", color=COLOR.MUTED, wrap=True),
        FlexSeparator(margin="md"),
    ]
    for c in contacts:
        contents.append(
            FlexBox(
                layout="horizontal",
                margin="md",
                spacing="sm",
                contents=[
                    FlexText(text=c.get("icon", "•"), size="lg", flex=0),
                    FlexBox(
                        layout="vertical",
                        contents=[
                            FlexText(text=c.get("name", ""), size="sm", weight="bold", color=COLOR.TEXT, wrap=True),
                            FlexText(text=c.get("detail", ""), size="xs", color=COLOR.MUTED, wrap=True),
                        ],
                    ),
                ],
            )
        )
    return FlexBubble(
        size="kilo",
        body=FlexBox(
            layout="vertical",
            spacing="sm",
            padding_all="16px",
            background_color=COLOR.SURFACE,
            contents=contents,
        ),
    )


def confirm_bubble(title: str, body: str, accent_color: Optional[str] = None) -> FlexBubble:
    """Two-button confirmation dialog — caller attaches footer buttons."""
    accent_color = accent_color or COLOR.BRAND
    return FlexBubble(
        size="kilo",
        body=FlexBox(
            layout="vertical",
            spacing="md",
            padding_all="16px",
            background_color=COLOR.SURFACE,
            contents=[
                _accent_strip(accent_color),
                FlexText(text=title, size="lg", weight="bold", color=COLOR.TEXT, wrap=True),
                FlexText(text=body, size="sm", color=COLOR.MUTED, wrap=True),
            ],
        ),
    )


def to_message(alt_text: str, bubble: FlexBubble, quick_reply: Optional[QuickReply] = None) -> FlexMessage:
    """Wrap a bubble into a sendable FlexMessage, optionally with a QuickReply."""
    return FlexMessage(alt_text=alt_text, contents=bubble, quick_reply=quick_reply)
