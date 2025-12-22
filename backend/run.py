from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from generator import generate_design
import os

app = FastAPI(title="Graphic AI Agent")

# Serve generated images from the outputs/images directory at /images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, '..', 'outputs', 'images')
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Allow CORS for local development so the frontend (served on a different port)
# can call the backend. For production, restrict origins appropriately.
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DesignRequest(BaseModel):
    product: str
    use_case: str
    platform: str
    style: str
    template: str = "sale_poster"
    width: int = 384
    steps: int = 20
    guidance_scale: float = 7.5
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    profile: str = "balanced"
    exact: bool = False


@app.post("/generate")
def generate(data: DesignRequest):
    image_path = generate_design(
        data.product,
        data.use_case,
        data.platform,
        data.style,
        template=data.template,
        width=data.width,
        steps=data.steps,
        guidance_scale=data.guidance_scale,
        negative_prompt=data.negative_prompt,
        seed=data.seed,
        profile=data.profile,
        exact=data.exact,
    )

    # image_path is a filesystem path; return a web URL path under /images
    filename = os.path.basename(image_path)
    web_path = f"/images/{filename}"

    return {
        "status": "success",
        "image_path": web_path
    }
