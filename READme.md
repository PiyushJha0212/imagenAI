# Imagen AI — Local Stable Diffusion UI

Small local web UI and backend for generating marketing-style images (posters, banners, Instagram) using Stable Diffusion. This README explains how to run the project, how to call the API, and how to provide prompts. The system already applies a default negative prompt in the generator to reduce text/watermarks.

# Team Details 
Piyush Jha(Leader) :- handled the backend of the ImagenAI and integrate the code .
Komal Dumka :- handled the logic behind the agent.py and improve the UI/UX of ImagenAi.

# Tech Stack 
backend:- Python (stablediffuser)
Frontend:- Web Stack (HTML , CSS , JS )

# Direct URL's 
backend :- (http://127.0.0.1:8000/docs)
Frontend :- (http://127.0.0.1:5500/try.html)

# Steps 

Go to the Home page http://127.0.0.1:5500/index.html and on the header click on [try it] then you are on designing page 

# Example promt 
🖼️ POSTER (Tall – headline at top)
Poster Background (Universal)
Premium studio-style background with soft cinematic lighting, elegant and minimal composition, subject placed slightly lower in frame, large clean empty space at the top for headline text, balanced shadows, professional advertising poster look, high quality, realistic, no text, no letters, no logo, no watermark
Best for:
Festival posters
Product posters
Event announcements

🌐 BANNER (Wide – CTA on side)
Website Banner Background
Wide cinematic background with modern lighting and smooth gradients, subject placed on left side, large empty space on right for call-to-action text, clean professional marketing design, subtle depth and contrast, high quality commercial banner style, no text, no letters, no logo, no watermark
Best for:
Website hero banners
Landing pages
Ads & promotions

📸 INSTAGRAM POST (Square – centered)
Instagram Post Background
Square composition with centered subject, soft studio lighting, modern minimal aesthetic, clean background with balanced negative space around subject, professional social media marketing look, high quality, sharp details, no text, no letters, no logo, no watermark
Best for:
Instagram posts
Social media creatives
Brand 

🎉 FESTIVE (Diwali / New Year / Celebration)
Festive Poster Background
Festive decorative background with warm lighting and subtle glowing elements, elegant celebration mood, premium colors, subject placed lower with clear empty space at top for headline, professional festive advertising style, high quality, no text, no letters, no logo, no watermark

🛍️ SALE / MARKETING
Sale Promotion Background
Dynamic commercial background with soft gradients and lighting accents, bold yet clean composition, empty space at top and center for promotional text, professional sale poster design, modern advertising aesthetic, high quality, no text, no letters, no logo, no watermark

⚙️ IMPORTANT (Why these work)
❌ No text generation → frontend handles text
✅ Negative space enforced → templates work correctly
⚡ CPU-friendly → no over-complex details
🧠 Agent understands layout intent
🏆 Judges see “Graphic Designer”, not just Image Generator


## Repository layout

- `backend/` — FastAPI backend and generator logic (`run.py`, `generator.py`, `agent.py`).
- `frontend/` — Simple static frontend (`index.html`, `try.html`, `app.js`, `style.css`).
- `outputs/images/` — Generated images are written here and served by the backend at `/images`.

## Requirements

- Python 3.10+ (or 3.9+) with the dependencies in `requirements.txt` installed.
- A local GPU is optional but recommended for reasonable generation speed.

Install dependencies (recommended in a venv):

```bash
python -m venv .venv
.
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start the backend

From the project root run (recommended):

```bash
cd backend
python -m uvicorn run:app --host 127.0.0.1 --port 8000
```

- Health endpoint: `http://127.0.0.1:8000/ping`
- Generated images are available at `http://127.0.0.1:8000/images/<filename>`
- CORS is already enabled in `backend/run.py` to allow the frontend to call the API.

## Serve the frontend

You can open the HTML files directly in a browser, but it's better to serve them with a small static server so resources and fetch behave normally:

```bash
cd frontend
python -m http.server 5500
# Open http://127.0.0.1:5500/try.html
```

The frontend fetches the backend at `http://127.0.0.1:8000` by default (see `frontend/app.js`). If you run the backend on a different port, update the `API_BASE` constant in `frontend/app.js` or start uvicorn with `--port <port>`.

## How to give prompts (what to send)

The UI collects a small set of high-level fields. Those fields are sent to the backend `/generate` endpoint as JSON. The main input is the `product` string — a concise description/title of what you want.

Typical fields accepted by the API (see `backend/run.py` / `DesignRequest`):

- `product` (string) — the item/title you want to appear in the design (required).
- `use_case` (string) — `sale`, `event`, `branding` (affects prompt construction).
- `platform` (string) — `poster`, `banner`, `instagram` (affects size/aspect ratio).
- `style` (string) — e.g. `minimal`, `corporate`, `festive` (affects prompt wording).
- `template` (string) — template hint like `sale_poster`, `website_banner`, `instagram`.
- `width` (int) — pixel width hint for generation (generator may adjust to multiple of 8).
- `steps` (int) — diffusion steps.
- `guidance_scale` (float) — classifier-free guidance strength.
- `negative_prompt` (string) — instructs the model what to avoid (see note below).
- `seed` (int) — optional deterministic seed.
- `profile` (string) — `fast`, `balanced`, `high` — maps to step/size presets.
- `exact` (bool) — when true the generator will use template exact sizes.

Example direct API call using `curl` (works even without the frontend):

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "product": "Winter Jacket Sale",
    "use_case": "sale",
    "platform": "poster",
    "style": "minimal",
    "template": "sale_poster",
    "width": 512,
    "steps": 20,
    "guidance_scale": 7.0,
    "negative_prompt": "no text, watermark, logo, blurry",
    "seed": 42,
    "profile": "balanced",
    "exact": false
  }'
```

Response shape (JSON):

```json
{
  "status": "success",
  "image_path": "/images/<generated-file>.png"
}
```

Then open `http://127.0.0.1:8000/images/<generated-file>.png` or use the frontend preview which will display the returned image URL.

## Negative prompt behavior (important)

- The generator provides a default negative prompt to reduce unwanted text, watermarks, or logos. See `backend/generator.py` where a default `negative_prompt` like `"text, letters, watermark, logo, low quality, blurry"` is applied when none is supplied.
- You can override this by providing `negative_prompt` in the API request JSON (as shown in the `curl` example), or by adding a `negative_prompt` input to the UI. The frontend already reads `negative_prompt` from an element with id `negative_prompt` if present (`frontend/app.js` uses `getVal('negative_prompt')`).

To add a visible input to `try.html`, insert a textarea input with id `negative_prompt` anywhere in the form. No code changes to `app.js` are required because it already reads that id.

Example HTML snippet to add into `frontend/try.html`:

```html
<label for="negative_prompt">Negative prompt (optional)</label>
<textarea id="negative_prompt" placeholder="e.g., no text, watermark, logo"></textarea>
```
## Troubleshooting

## Example prompts

Use the `product` field as the main subject and add optional context (mood, composition, color, and style). Here are example prompts you can try in the UI or via the API `product` field.

- Simple product-focused:
  - "Winter jacket sale — cozy wool jacket on a model, warm tones, modern minimal layout"

- Style + mood:
  - "Outdoor music festival poster — energetic crowd, sunset, vibrant colors, bold headline space, festival branding style"

- Composition-focused (useful for banners):
  - "Summer collection banner — panoramic scene with models on a beach, soft pastel palette, clear center area for text"

- Brand/photoreal variant:
  - "Premium leather backpack product shot, studio lighting, shallow depth of field, high detail, clean white background"

- Creative / illustrative:
  - "Festive holiday poster, flat vector illustration style, warm reds and golds, decorative ornaments, centered product title space"

- With explicit negative prompt guidance (sent as `negative_prompt` or left to default):
  - Product: "Limited edition sneaker drop — streetwear, high contrast"
  - Negative prompt: "no text, watermark, logo, blurry, deformed"

- Precise layout + seed for repeatability:
  - `product`: "Black Friday poster — bold headline area, dramatic lighting"
  - `platform`: `poster`, `exact`: `true`, `seed`: `12345`, `profile`: `balanced`

Tips:
- If you want to avoid artifacts like unwanted text or logos, include a `negative_prompt` string (the backend also applies a sensible default).
- Use `profile` set to `fast` for quicker, lower-resolution results, or `high` on GPU for best quality.

## Troubleshooting

- ERR_CONNECTION_REFUSED / "Failed to fetch": ensure the backend is running on the port the frontend expects (`8000` by default) and uvicorn started successfully.
- If you changed ports, update `frontend/app.js`'s `API_BASE` constant or start the backend on the expected port.
- If images don't display, check the backend log and verify the file exists under `outputs/images/` and is being served at `/images`.
- If you get CORS errors, `backend/run.py` already enables permissive CORS for development; double-check you restarted the backend after edits.

## Where to customize behavior

- Prompt construction: `backend/agent.py` builds the textual prompt given `product`, `use_case`, `platform`, and `style`.
- Generation parameters and negative prompt default: `backend/generator.py`.
- API routing and static mounting: `backend/run.py`.
- Frontend UI and how requests are made: `frontend/app.js`, `frontend/try.html`.

If you want, I can:

- add a `negative_prompt` textarea into `frontend/try.html` and wire up enabling/disabling the overlay controls,
- or help you change the default negative prompt in `backend/generator.py`.

Enjoy generating! If you want I can add a small example prompt list or tune default negative prompts for better artifact removal.
