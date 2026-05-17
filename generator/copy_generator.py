import os
import json
from openai import OpenAI

def _get_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """Te egy tapasztalt Facebook hirdetési szövegíró vagy, aki pattern-interrupt (figyelemfelkeltő) kreatívokat készít.

Minden kreatívhoz adj meg:
1. "hook": Egy rövid, ütős headline (max 6 szó, NAGYBETŰVEL), ami megszakítja a scroll-t
2. "headline": A fő cím az ad képen (max 10 szó, NAGYBETŰVEL)
3. "caption": A Facebook poszt szövege (2-3 mondat, érzelmes, közvetlen hangnem)
4. "bullets": 4-5 rövid bullet point (előnyök/tulajdonságok, max 6 szó/bullet)
5. "cta_text": CTA szöveg a gombra (max 3 szó)
6. "image_prompt": DALL-E 3 prompt angolul - reális fotó stílusú kép, ember/helyszín alapú, NO text in image

A 6 kreatív KÜLÖNBÖZŐ szögből közelítse meg a szolgáltatást:
- Érzelmi fájdalom (mi a probléma ami nélkül élnek)
- Sürgősség / azonnali megoldás
- Társadalmi bizonyíték / szakértelem
- Időjárás / évszak alapú
- Ár / érték ajánlat
- Megkönnyebbülés / megoldás érzése

Csak JSON array-t adj vissza, semmi mást."""

def generate_ad_copies(data: dict) -> list[dict]:
    brand = data.get("brand_name", "")
    service = data.get("service_type", "")
    area = data.get("target_area", "")
    offer = data.get("main_offer", "")
    benefits = data.get("benefits", [])
    phone = data.get("phone", "")
    website = data.get("website", "")
    tone = data.get("tone", "sürgős")
    num = data.get("num_creatives", 6)
    extra = data.get("additional_info", "")

    benefits_str = "\n".join(f"- {b}" for b in benefits) if benefits else ""

    user_prompt = f"""Cég: {brand}
Szolgáltatás: {service}
Területi lefedettség: {area}
Fő ajánlat/promóció: {offer}
Előnyök/USP-k:
{benefits_str}
Telefon: {phone}
Weboldal: {website}
Hangnem: {tone}
Extra info: {extra}

Készíts {num} különböző pattern-interrupt Facebook hirdetési kreatívot ehhez a vállalkozáshoz.
Minden image_prompt legyen angolul és NE tartalmazzon szöveget a képen.
Adj vissza egy JSON array-t [{num} objektummal]."""

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    # Handle both {"creatives": [...]} and [...] responses
    if isinstance(parsed, list):
        creatives = parsed
    elif isinstance(parsed, dict):
        # Find the first list value
        for v in parsed.values():
            if isinstance(v, list):
                creatives = v
                break
        else:
            creatives = [parsed]
    else:
        creatives = []

    # Ensure we have the right number
    return creatives[:num]
