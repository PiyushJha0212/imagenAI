def build_prompt(product, use_case, platform, style):
    base = "professional marketing design, high quality, clean layout"

    if use_case == "sale":
        marketing = f"sale poster for {product}, bold headline, discount offer, eye-catching"
    elif use_case == "event":
        marketing = f"event promotion poster for {product}, attractive typography"
    else:
        marketing = f"branding design for {product}, minimal logo focused"

    if platform == "instagram":
        layout = "square layout, instagram post, social media design"
    elif platform == "banner":
        layout = "wide banner, website header design"
    else:
        layout = "poster design, print ready"

    style_hint = f"{style} style, modern, professional"

    return f"{base}, {marketing}, {layout}, {style_hint}"
