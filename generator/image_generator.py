import os
import io
import textwrap
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from openai import OpenAI

def _get_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

FONTS_DIR = Path(__file__).parent.parent / "fonts"

def _load_font(bold=False, size=24):
    candidates = [
        FONTS_DIR / ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf"),
        FONTS_DIR / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw) -> list[str]:
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _generate_dalle_image(prompt: str) -> Image.Image:
    client = _get_client()
    full_prompt = (
        f"{prompt}. "
        "Professional photography style, high quality, realistic, no text, no watermarks, "
        "vibrant colors, sharp focus."
    )
    resp = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    url = resp.data[0].url
    img_data = requests.get(url, timeout=30).content
    return Image.open(io.BytesIO(img_data)).convert("RGB")


def _composite_ad_image(
    bg: Image.Image,
    brand_name: str,
    headline: str,
    phone: str,
    website: str,
    primary_color: tuple = (255, 193, 7),   # yellow
    dark_color: tuple = (18, 24, 45),        # dark navy
) -> Image.Image:
    W, H = 800, 800
    bg = bg.resize((W, H), Image.LANCZOS)
    img = bg.copy()
    draw = ImageDraw.Draw(img)

    # --- Top header bar ---
    bar_h = 52
    header = Image.new("RGBA", (W, bar_h), (*dark_color, 220))
    img.paste(header, (0, 0), header)

    font_header = _load_font(bold=True, size=20)
    draw.text((18, 15), brand_name.lower(), font=font_header, fill=(255, 255, 255))

    # --- Bottom overlay gradient ---
    overlay_h = 260
    overlay = Image.new("RGBA", (W, overlay_h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(overlay_h):
        alpha = int(210 * (i / overlay_h))
        od.line([(0, i), (W, i)], fill=(0, 0, 0, alpha))
    img.paste(overlay, (0, H - overlay_h), overlay)

    # --- Brand logo text (upper-center of image) ---
    logo_font = _load_font(bold=True, size=38)
    logo_text = brand_name.lower() + "."
    bbox = draw.textbbox((0, 0), logo_text, font=logo_font)
    lw = bbox[2] - bbox[0]
    lx = (W - lw) // 2
    ly = int(H * 0.38)  # slightly above center
    # Shadow
    draw.text((lx + 2, ly + 2), logo_text, font=logo_font, fill=(0, 0, 0, 120))
    draw.text((lx, ly), logo_text, font=logo_font, fill=(255, 255, 255))

    # --- Headline text ---
    headline_font = _load_font(bold=True, size=36)
    lines = _wrap_text(headline.upper(), headline_font, W - 60, draw)
    y_start = H - overlay_h + 22
    for line in lines[:3]:
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        draw.text((30, y_start), line, font=headline_font, fill=(255, 255, 255))
        y_start += lh + 6

    # --- CTA button ---
    btn_y = H - 100
    btn_w, btn_h = 260, 46
    btn_x = 30
    btn_color = primary_color
    # Rounded rectangle simulation
    draw.rounded_rectangle(
        [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
        radius=6,
        fill=btn_color,
    )
    btn_font = _load_font(bold=True, size=18)
    btn_text = "ÜRLAPKITÖLTÉS"
    bbox = draw.textbbox((0, 0), btn_text, font=btn_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = btn_x + (btn_w - tw) // 2
    ty = btn_y + (btn_h - th) // 2
    draw.text((tx, ty), btn_text, font=btn_font, fill=dark_color)

    # --- Footer: phone + website ---
    footer_font = _load_font(bold=False, size=16)
    footer_text = f"{phone}  •  {website}"
    draw.text((30, H - 40), footer_text, font=footer_font, fill=(200, 200, 200))

    return img


def _create_fb_post_mockup(
    brand_name: str,
    caption: str,
    bullets: list[str],
    phone: str,
    website: str,
    cta_text: str,
    hook: str,
    ad_thumbnail: Image.Image,
    primary_color: tuple = (255, 193, 7),
    dark_color: tuple = (18, 24, 45),
) -> Image.Image:
    W, H = 680, 800
    bg_color = (242, 243, 245)
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    card_margin = 16
    card_x, card_y = card_margin, card_margin
    card_w = W - 2 * card_margin
    card_h = H - 2 * card_margin
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=12,
        fill=(255, 255, 255),
    )

    # --- Profile header ---
    cx, cy = card_x + 22, card_y + 20
    draw.ellipse([cx, cy, cx + 44, cy + 44], fill=dark_color)
    initial_font = _load_font(bold=True, size=20)
    initial = brand_name[0].upper() if brand_name else "B"
    ib = draw.textbbox((0, 0), initial, font=initial_font)
    draw.text(
        (cx + (44 - (ib[2] - ib[0])) // 2, cy + (44 - (ib[3] - ib[1])) // 2),
        initial, font=initial_font, fill=(255, 255, 255)
    )

    name_font = _load_font(bold=True, size=16)
    sponsored_font = _load_font(bold=False, size=13)
    draw.text((cx + 54, cy + 4), brand_name, font=name_font, fill=(28, 30, 33))
    draw.text((cx + 54, cy + 24), "Szponzorált", font=sponsored_font, fill=(96, 103, 112))

    # --- Caption text ---
    y = card_y + 84
    caption_font = _load_font(bold=False, size=15)
    hook_font = _load_font(bold=True, size=16)

    # Hook line
    hook_lines = _wrap_text(hook, hook_font, card_w - 40, draw)
    for line in hook_lines:
        draw.text((card_x + 20, y), line, font=hook_font, fill=(28, 30, 33))
        bbox = draw.textbbox((0, 0), line, font=hook_font)
        y += (bbox[3] - bbox[1]) + 4

    y += 6

    # Caption
    cap_lines = _wrap_text(caption, caption_font, card_w - 40, draw)
    for line in cap_lines[:5]:
        draw.text((card_x + 20, y), line, font=caption_font, fill=(50, 50, 50))
        bbox = draw.textbbox((0, 0), line, font=caption_font)
        y += (bbox[3] - bbox[1]) + 3

    y += 10

    # --- Bullet points ---
    bullet_font = _load_font(bold=False, size=14)
    check_color = (34, 197, 94)
    for b in bullets[:5]:
        blines = _wrap_text(b, bullet_font, card_w - 70, draw)
        # Draw green circle bullet manually
        cb_size = 12
        draw.ellipse(
            [card_x + 20, y + 2, card_x + 20 + cb_size, y + 2 + cb_size],
            fill=check_color,
        )
        for bline in blines:
            draw.text((card_x + 38, y), bline, font=bullet_font, fill=(28, 30, 33))
            bbox = draw.textbbox((0, 0), bline, font=bullet_font)
            y += (bbox[3] - bbox[1]) + 2
        y += 4

    y += 8

    # --- Phone ---
    phone_font = _load_font(bold=True, size=14)
    draw.text((card_x + 20, y), f"Tel: {phone}", font=phone_font, fill=(28, 30, 33))
    y += 26

    # --- Separator ---
    draw.line([(card_x + 20, y), (card_x + card_w - 20, y)], fill=(220, 220, 220), width=1)
    y += 12

    # --- Ad preview row (website + thumbnail) ---
    thumb_size = 80
    thumb = ad_thumbnail.resize((thumb_size, thumb_size), Image.LANCZOS)

    preview_bg_x = card_x + 20
    preview_bg_w = card_w - 40
    preview_bg_h = thumb_size + 20
    draw.rectangle(
        [preview_bg_x, y, preview_bg_x + preview_bg_w, y + preview_bg_h],
        fill=(240, 242, 245)
    )

    # Thumbnail on right
    thumb_x = preview_bg_x + preview_bg_w - thumb_size - 10
    img.paste(thumb, (thumb_x, y + 10))

    # Website info
    site_font = _load_font(bold=False, size=12)
    site_bold = _load_font(bold=True, size=13)
    domain = website.replace("https://", "").replace("http://", "").rstrip("/").upper()
    draw.text((preview_bg_x + 12, y + 10), domain, font=site_bold, fill=(96, 103, 112))
    cta_preview_text = cta_text if cta_text else "Ajánlatkérés"
    draw.text((preview_bg_x + 12, y + 30), cta_preview_text, font=site_font, fill=(50, 50, 50))

    y += preview_bg_h + 12

    # --- CTA blue button ---
    btn_w, btn_h = card_w - 40, 40
    btn_x2 = card_x + 20
    draw.rounded_rectangle(
        [btn_x2, y, btn_x2 + btn_w, y + btn_h],
        radius=6,
        fill=(24, 119, 242),
    )
    cta_font = _load_font(bold=True, size=16)
    cta_display = cta_text if cta_text else "Ajánlatkérés"
    cb = draw.textbbox((0, 0), cta_display, font=cta_font)
    draw.text(
        (btn_x2 + (btn_w - (cb[2] - cb[0])) // 2, y + (btn_h - (cb[3] - cb[1])) // 2),
        cta_display, font=cta_font, fill=(255, 255, 255)
    )

    return img


def generate_ad_images(data: dict, ad_copies: list[dict]) -> list[dict]:
    brand_name = data.get("brand_name", "Brand")
    phone = data.get("phone", "")
    website = data.get("website", "")
    results = []

    for i, copy in enumerate(ad_copies):
        prompt = copy.get("image_prompt", f"Professional service worker at work, high quality photo")
        headline = copy.get("headline", "")
        hook = copy.get("hook", "")
        caption = copy.get("caption", "")
        bullets = copy.get("bullets", [])
        cta_text = copy.get("cta_text", "Ajánlatkérés")

        # Generate DALL-E image
        bg_image = _generate_dalle_image(prompt)

        # Composite the Facebook ad image
        ad_image = _composite_ad_image(
            bg=bg_image,
            brand_name=brand_name,
            headline=headline,
            phone=phone,
            website=website,
        )

        # Create Facebook post mockup
        fb_mock = _create_fb_post_mockup(
            brand_name=brand_name,
            caption=caption,
            bullets=bullets if isinstance(bullets, list) else [bullets],
            phone=phone,
            website=website,
            cta_text=cta_text,
            hook=hook,
            ad_thumbnail=ad_image,
        )

        results.append({
            "index": i + 1,
            "ad_image": ad_image,
            "fb_mockup": fb_mock,
            "copy": copy,
        })

    return results
