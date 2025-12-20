import torch
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
import uuid, os
from agent import build_prompt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_ID = "runwayml/stable-diffusion-v1-5"
pipe = None
device = "cuda" if torch.cuda.is_available() else "cpu"


def get_pipe():
    global pipe
    if pipe is None:
        # choose dtype based on device
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        pipe = StableDiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype
        )
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
        pipe = pipe.to(device)
        pipe.enable_attention_slicing()
    return pipe


def _make_multiple_of_8(x: int) -> int:
    return max(8, (int(x) + 7) // 8 * 8)


def generate_design(product, use_case, platform, style,
                    width=384, steps=20, guidance_scale=6.5,
                    negative_prompt=None, seed=None):

    pipe = get_pipe()

    prompt = build_prompt(product, use_case, platform, style)

    # Ensure dimensions are multiples of 8
    try:
        width = int(width)
    except Exception:
        width = 384
    width = _make_multiple_of_8(width)

    if platform == "banner":
        height = max(8, width // 3)
    elif platform == "poster":
        height = max(8, int(width * 1.5))
    else:
        height = width

    height = _make_multiple_of_8(height)

    # default negative prompt to reduce text/artifacts
    if not negative_prompt:
        negative_prompt = "text, letters, watermark, logo, blurry, low quality, deformed"

    # seed handling
    gen = None
    if seed is not None:
        try:
            seed_i = int(seed)
            gen = torch.Generator(device=device).manual_seed(seed_i)
        except Exception:
            gen = None

    with torch.inference_mode():
        call_kwargs = dict(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=int(steps),
            guidance_scale=float(guidance_scale),
            negative_prompt=negative_prompt,
        )
        if gen is not None:
            call_kwargs["generator"] = gen

        image = pipe(**call_kwargs).images[0]

    filename = f"{uuid.uuid4()}.png"
    path = os.path.join(OUTPUT_DIR, filename)
    image.save(path)
    return path
