# def build_prompt(product, use_case, platform, style, intent='design'):
#     """
#     Build a composition-aware prompt for Stable Diffusion that focuses on
#     product/background visuals only (no text). The `intent` parameter allows
#     the agent to adjust phrasing for marketing vs pure photography.

#     This prompt intentionally avoids any request for in-image typography.
#     """
#     subject = (product or '').strip() or 'product'

#     # Base visual intent: emphasize photorealism and studio-quality rendering
#     base = "photorealistic product image, studio lighting, sharp details, high resolution"

#     # Use-case variations
#     if use_case == 'sale':
#         marketing = f"close-up of {subject}, front-facing, clear product visibility, room for headline above or beside"
#     elif use_case == 'event':
#         marketing = f"stylized product scene for {subject}, dynamic composition, vibrant accents, negative space for overlay"
#     else:
#         marketing = f"branding-style product shot for {subject}, minimalist composition, centered, negative space for logo"

#     # Layout framing hints
#     if platform == 'banner':
#         framing = 'wide composition, subject off-center to the left or right, generous empty space for overlay elements'
#     elif platform == 'poster':
#         framing = 'tall composition, product slightly lower in frame, top area left empty for title'
#     else:
#         framing = 'square composition, product centered, balanced negative space'

#     # Style hints
#     if style == 'minimal':
#         style_hint = 'minimal aesthetic, clean background, soft shadows'
#     elif style == 'festive':
#         style_hint = 'vibrant colors, warm lighting, subtle decorative elements (no text)'
#     else:
#         style_hint = 'modern look, cinematic lighting, realistic textures'

#     # Combine and enforce no text or typography in the image
#     prompt = (
#         f"{base}, {marketing}, {framing}, {style_hint}, "
#         "no text, no letters, no watermark, no logo, do not generate typography, avoid human faces"
#     )

#     return prompt


# def get_layout_preset(name: str):
#     """Return recommended (width, height) aspect sizes for known layouts.

#     These are design presets; frontend may use these to crop or request exact generation.
#     """
#     name = (name or '').lower()
#     if name == 'banner':
#         return (960, 320)  # 3:1 wide
#     if name == 'poster':
#         return (512, 768)  # 2:3 tall
#     # instagram / square
#     return (640, 640)

def build_prompt(product, use_case, platform, style, template='sale_poster'):
    subject = product.strip() or "product"

    base = "photorealistic product background, studio lighting, clean composition"

    if use_case == "sale":
        intent = f"{subject}, clear focus, marketing background, empty space for text"
    elif use_case == "event":
        intent = f"{subject}, festive background, dynamic lighting, no text"
    else:
        intent = f"{subject}, branding background, minimal aesthetic"

    if platform == "banner":
        framing = "wide composition, subject off-center"
    elif platform == "poster":
        framing = "tall composition, subject lower half"
    else:
        framing = "square composition, centered subject"

    style_hint = {
        "minimal": "minimal, clean background",
        "festive": "festive colors, soft lights",
        "corporate": "neutral colors, professional look"
    }.get(style, "modern style")

    return (
        f"{base}, {intent}, {framing}, {style_hint}, "
        "no text, no letters, no logo, no watermark"
    )
