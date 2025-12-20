import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import uuid
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_ID = "runwayml/stable-diffusion-v1-5"

pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = pipe.to(device)

pipe.enable_attention_slicing()
# Try to enable sequential CPU offload only when supported (accelerate installed)
try:
    import importlib
    if importlib.util.find_spec("accelerate") is not None:
        pipe.enable_sequential_cpu_offload()
    else:
        # accelerate not installed — skip CPU offload
        pass
except Exception as e:
    # If enable_sequential_cpu_offload raises (missing accelerator, etc.),
    # warn and continue without CPU offload so the server can start.
    import warnings
    warnings.warn(f"Could not enable sequential CPU offload: {e}")

def _make_multiple_of_8(x: int) -> int:
    return max(8, (x + 7) // 8 * 8)


def generate_design(product, use_case, platform, style, width=384, steps=20, guidance_scale=7.5, negative_prompt=None, seed=None):
    # import locally to avoid import-time circular dependencies
    build_prompt = None
    try:
        import agent as agent_mod
        build_prompt = getattr(agent_mod, "build_prompt", None)
    except Exception:
        build_prompt = None

    # If agent.build_prompt is unavailable (circular import or missing),
    # fall back to a local implementation that mirrors the agent logic.
    if not callable(build_prompt):
        def build_prompt(product, use_case, platform, style):
            # Stronger product-focused prompt for higher-quality results
            subject = product.strip() or "product"

            # Base intent
            base = "highly detailed product photography, studio lighting, sharp details, realistic, high resolution"

            # Marketing-specific instructions
            if use_case == "sale":
                marketing = f"close-up of {subject}, centered product, clean white background, simple composition, prominent text area for headline"
            elif use_case == "event":
                marketing = f"stylized promotional shot for {subject}, dynamic composition, vibrant colors, bold typography space"
            else:
                marketing = f"branding-focused image for {subject}, minimalist layout, logo-friendly space, clean aesthetic"

            # Layout hints
            if platform == "instagram":
                layout = "square composition, product centered"
            elif platform == "banner":
                layout = "wide composition, left or right aligned product with negative space"
            else:
                layout = "tall composition, poster layout, printable quality"

            # Style hints
            style_hint = f"{style} style, modern, professional, cinematic lighting"

            # Combine and encourage photorealism
            return f"{base}, {marketing}, {layout}, {style_hint}, photorealistic, extremely detailed, 8k"

    prompt = build_prompt(product, use_case, platform, style)

    # Determine aspect ratio / height based on platform
    try:
        width = int(width)
    except Exception:
        width = 384
    width = _make_multiple_of_8(width)

    if platform == 'instagram':
        height = width
    elif platform == 'banner':
        # wide banner: 3:1 (width:height)
        height = max(8, int(width / 3))
    else:
        # poster: taller (2:3 width:height -> height = width * 1.5)
        height = max(8, int(width * 1.5))

    height = _make_multiple_of_8(height)

    # Reduce steps by default to speed up generation on low-spec machines
    try:
        steps = int(steps)
    except Exception:
        steps = 20

    try:
        guidance_scale = float(guidance_scale)
    except Exception:
        guidance_scale = 7.5

    # sensible negative prompts to reduce artifacts and text
    if not negative_prompt:
        negative_prompt = (
            "lowres, text, watermark, blurry, deformed, poorly drawn, extra limbs, ugly, duplicate"
        )

    # If a seed is provided, use a deterministic generator
    gen = None
    if seed is not None:
        try:
            seed_i = int(seed)
            gen = torch.Generator(device=device).manual_seed(seed_i)
        except Exception:
            gen = None

    # Call pipeline with explicit steps, guidance, and negative prompt
    call_kwargs = dict(num_inference_steps=steps, width=width, height=height, guidance_scale=guidance_scale, negative_prompt=negative_prompt)
    if gen is not None:
        call_kwargs['generator'] = gen

    image = pipe(prompt, **call_kwargs).images[0]

    filename = f"{uuid.uuid4()}.png"
    path = os.path.join(OUTPUT_DIR, filename)
    image.save(path)

    # Return absolute filesystem path (backend will convert to a web URL)
    return path
