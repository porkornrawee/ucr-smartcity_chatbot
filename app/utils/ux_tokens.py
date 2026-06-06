"""
ux_tokens.py — Single source of truth for UI design tokens.

Every colour, font, and spacing value used when building LINE FlexMessages
lives here. Do NOT hard-code hex strings anywhere else in the codebase; import
from this module instead. Mirrors the prototype design system
(see docs/uxui-tokens.md) so the chat experience stays visually consistent.

Palette origin:
- COLOR.*   : "บ้านอยู่เย็น" chat prototype (blue family) — primary chat UI
- ACCENT.*  : Rich Menu warm→cool palette — used as per-topic accents
- BANNER.*  : situational banner styles (hot / rain / night / normal)
"""


class COLOR:
    # Brand blue family (primary)
    BRAND = "#4A90C4"          # --b  primary actions, selected state
    BRAND_LIGHT = "#EBF4FB"    # --bl bubble / card background
    BRAND_MUTED = "#B8D8F0"    # --bm soft border
    BRAND_DARK = "#1E527A"     # --bd emphasis text on light bg
    ACCENT = "#72BFD8"         # --ac secondary accent (gradient end)
    ACCENT_LIGHT = "#E2F4FA"   # --al accent surface
    DANGER = "#E05252"         # --red urgent / error

    # Neutrals
    BG = "#EDF4FB"             # --bg page background
    SURFACE = "#FFFFFF"        # --sf cards / bubbles
    TEXT = "#1C2E3E"           # --tx primary text
    MUTED = "#5A7A94"          # --mu secondary text
    HINT = "#96B4C8"           # --hi tertiary / hint text
    BORDER = "#CCDFF0"         # --br hairline border
    ON_BRAND = "#FFFFFF"       # text/icon on brand-coloured surfaces


class ACCENT:
    """Rich Menu warm→cool accents, reused as per-topic colour cues."""
    CORAL = "#E26D54"          # heat / ask
    CORAL_TEXT = "#CF5C43"
    MUSTARD = "#DBA53C"        # report / problem
    MUSTARD_TEXT = "#BC8722"
    CYAN = "#2E97C6"           # contact
    CYAN_TEXT = "#2580AB"
    MINT = "#43A87B"           # summary
    MINT_TEXT = "#358F66"


class BANNER:
    """Situational banner styles: (background, border, text)."""
    HOT = {"bg": "#FFF8E6", "border": "#F5A623", "text": "#4A3000"}
    RAIN = {"bg": COLOR.BRAND_LIGHT, "border": COLOR.BRAND, "text": COLOR.BRAND_DARK}
    NIGHT = {"bg": "#F0EEF9", "border": "#8B7EC8", "text": "#2C1E5A"}
    NORMAL = {"bg": COLOR.ACCENT_LIGHT, "border": COLOR.ACCENT, "text": "#004455"}


# Per-topic accent lookup — keyed by survey topic answer value.
TOPIC_ACCENT = {
    "อากาศร้อนจัด": ACCENT.CORAL,
    "น้ำท่วม/น้ำขัง": COLOR.BRAND,
}


class FONT:
    FAMILY = "Sarabun, sans-serif"   # informational; LINE renders system Thai font
    SIZE_TITLE = "lg"                # FlexText size tokens
    SIZE_BODY = "md"
    SIZE_CAPTION = "sm"
    SIZE_HINT = "xs"


class SPACE:
    # FlexBox spacing / padding tokens (LINE keyword scale)
    NONE = "none"
    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


class RADIUS:
    SM = "8px"
    MD = "12px"
    LG = "16px"
    PILL = "999px"


# Header gradient endpoints (LINE Flex has no gradient; use BRAND as the solid fill,
# ACCENT documented here for parity with the prototype header).
GRADIENT_START = COLOR.BRAND
GRADIENT_END = COLOR.ACCENT
