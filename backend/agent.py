def build_prompt(product, use_case, platform, style):
    subject = product.strip() or "product"

    # Keep prompt SIMPLE and VISUAL
    base = "high quality product photography, studio lighting, clean composition"

    if style == "minimal":
        style_hint = "minimal, white background, soft light"
    elif style == "festive":
        style_hint = "colorful background, vibrant lighting"
    else:
        style_hint = "modern, professional lighting"

    if platform == "banner":
        framing = "wide framing, subject on one side, empty space"
    else:
        framing = "centered composition"

    # CRITICAL: explicitly forbid text
    return (
        f"{base}, {subject}, {style_hint}, {framing}, "
        f"photorealistic, sharp focus, no text, no letters, no typography"
    )
