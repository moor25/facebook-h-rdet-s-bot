# Facebook Kreatív Generátor

AI-alapú Facebook hirdetési kreatív generátor. A kitöltött felmérőből automatikusan generál **6 pattern-interrupt kreatívot** DALL-E 3 képekkel és GPT-4o szövegekkel, majd egy professzionális PDF-ben küldi el az eredményt.

## Működés

1. Kitöltöd a felmérőt (márkanév, szolgáltatás, ajánlat, előnyök, stílus)
2. GPT-4o megírja a 6 különböző szögű hirdetési szöveget
3. DALL-E 3 legenerálja a háttérképeket
4. A rendszer összerakja az ad mockupokat (hirdetéskép + Facebook poszt preview)
5. Letöltöd a kész PDF-et

## Telepítés

```bash
# 1. Clone-olás
git clone <repo-url>
cd facebook-ad-generator

# 2. Függőségek
pip install -r requirements.txt

# 3. API kulcs beállítása
cp .env.example .env
# Szerkeszd a .env fájlt, add hozzá az OpenAI API kulcsot

# 4. Fontok (ha nem lennének)
cp /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf fonts/
cp /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf fonts/

# 5. Indítás
python app.py
```

Ezután nyisd meg: http://localhost:5000

## Környezeti változók

```
OPENAI_API_KEY=sk-...
```

## Projekt struktúra

```
├── app.py                   # Flask web szerver
├── generator/
│   ├── copy_generator.py    # GPT-4o hirdetési szöveg generálás
│   ├── image_generator.py   # DALL-E 3 képgenerálás + PIL mockup összeállítás
│   └── pdf_generator.py     # ReportLab PDF generálás
├── templates/
│   └── survey.html          # Felmérő oldal
├── static/
│   ├── css/style.css
│   └── js/survey.js
├── fonts/                   # TTF fontok (Liberation Sans)
├── uploads/                 # Temp referencia képek
└── output/                  # Generált PDF-ek
```

## Technológiák

- **Flask** – web szerver
- **OpenAI GPT-4o** – hirdetési szöveg generálás
- **OpenAI DALL-E 3** – háttérkép generálás
- **Pillow** – képmontázs (ad image + FB mockup)
- **ReportLab** – PDF összeállítás
