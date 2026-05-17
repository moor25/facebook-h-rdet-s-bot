import io
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONTS_DIR = Path(__file__).parent.parent / "fonts"
DARK = HexColor("#12182D")
YELLOW = HexColor("#FFC107")
LIGHT_GRAY = HexColor("#F0F0F0")
MID_GRAY = HexColor("#888888")

def _register_fonts():
    font_map = {
        "AppFont": "LiberationSans-Regular.ttf",
        "AppFont-Bold": "LiberationSans-Bold.ttf",
    }
    for name, filename in font_map.items():
        path = FONTS_DIR / filename
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
            except Exception:
                pass


def _pil_image_to_bytes(img: Image.Image, fmt="PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


def _draw_cover_page(c: canvas.Canvas, page_w: float, page_h: float, data: dict):
    brand = data.get("brand_name", "Brand")
    service = data.get("service_type", "")
    num = data.get("num_creatives", 6)

    c.setFillColor(white)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Center brand name
    c.setFillColor(DARK)
    try:
        c.setFont("AppFont-Bold", 52)
    except Exception:
        c.setFont("Helvetica-Bold", 52)

    brand_text = brand.lower() + "."
    text_w = c.stringWidth(brand_text, "AppFont-Bold", 52)
    x = (page_w - text_w) / 2
    y = page_h / 2 + 10

    # Draw yellow dot separately
    main_text = brand.lower()
    main_w = c.stringWidth(main_text, "AppFont-Bold", 52)
    c.drawString(x, y, main_text)

    c.setFillColor(YELLOW)
    dot_x = x + main_w
    c.drawString(dot_x, y, ".")

    # Subtitle line
    subtitle = f"{num} új pattern-interrupt kreatív"
    try:
        c.setFont("AppFont", 16)
    except Exception:
        c.setFont("Helvetica", 16)

    c.setFillColor(MID_GRAY)
    sub_w = c.stringWidth(subtitle, "AppFont", 16)
    c.drawString((page_w - sub_w) / 2, y - 50, subtitle)

    # Decorative lines
    line_w = 200
    lx = (page_w - line_w) / 2
    c.setStrokeColor(YELLOW)
    c.setLineWidth(1.5)
    c.line(lx, y - 30, lx + line_w, y - 30)
    c.line(lx, y - 65, lx + line_w, y - 65)

    # Service label
    if service:
        try:
            c.setFont("AppFont", 12)
        except Exception:
            c.setFont("Helvetica", 12)
        c.setFillColor(MID_GRAY)
        svc_w = c.stringWidth(service, "AppFont", 12)
        c.drawString((page_w - svc_w) / 2, y - 90, service)


def _draw_creative_page(
    c: canvas.Canvas,
    page_w: float,
    page_h: float,
    item: dict,
    data: dict,
):
    c.setFillColor(LIGHT_GRAY)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    margin = 18 * mm
    content_w = page_w - 2 * margin
    content_h = page_h - 2 * margin

    # Left panel: ad image (55% of content width)
    left_w = content_w * 0.57
    right_w = content_w - left_w - 8 * mm

    ad_img: Image.Image = item["ad_image"]
    fb_img: Image.Image = item["fb_mockup"]

    # Scale ad image to fit left panel
    aspect = ad_img.height / ad_img.width
    img_w = left_w
    img_h = min(img_w * aspect, content_h)
    img_y = margin + (content_h - img_h) / 2

    ad_bytes = _pil_image_to_bytes(ad_img)
    c.drawImage(
        ImageReader(io.BytesIO(ad_bytes)),
        margin, img_y,
        width=img_w, height=img_h,
        preserveAspectRatio=True,
    )

    # Right panel: FB mockup
    fb_aspect = fb_img.height / fb_img.width
    fb_w = right_w
    fb_h = min(fb_w * fb_aspect, content_h)
    fb_y = margin + (content_h - fb_h) / 2
    fb_x = margin + left_w + 8 * mm

    fb_bytes = _pil_image_to_bytes(fb_img)
    c.drawImage(
        ImageReader(io.BytesIO(fb_bytes)),
        fb_x, fb_y,
        width=fb_w, height=fb_h,
        preserveAspectRatio=True,
    )

    # Page number
    try:
        c.setFont("AppFont", 9)
    except Exception:
        c.setFont("Helvetica", 9)
    c.setFillColor(MID_GRAY)
    c.drawString(margin, 8 * mm, f"Kreatív #{item['index']}")
    c.drawRightString(page_w - margin, 8 * mm, data.get("brand_name", "").lower() + ".")


def generate_pdf(
    data: dict,
    ad_copies: list[dict],
    images: list[dict],
    output_path: str,
):
    _register_fonts()

    page_size = landscape(A4)
    page_w, page_h = page_size

    c = canvas.Canvas(output_path, pagesize=page_size)
    c.setTitle(f"{data.get('brand_name', 'Brand')} – Facebook Kreatívok")

    # Cover page
    _draw_cover_page(c, page_w, page_h, data)
    c.showPage()

    # Creative pages
    for item in images:
        _draw_creative_page(c, page_w, page_h, item, data)
        c.showPage()

    c.save()
