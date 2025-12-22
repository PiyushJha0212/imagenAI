# import torch
# from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
# import uuid, os, hashlib
# from agent import build_prompt

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs", "images")
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# MODEL_ID = "runwayml/stable-diffusion-v1-5"
# pipe = None
# device = "cuda" if torch.cuda.is_available() else "cpu"


# def get_pipe():
#     global pipe
#     if pipe is None:
#         # choose dtype based on device
#         dtype = torch.float16 if torch.cuda.is_available() else torch.float32
#         pipe = StableDiffusionPipeline.from_pretrained(
#             MODEL_ID,
#             torch_dtype=dtype
#         )
#         pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
#         pipe = pipe.to(device)
#         pipe.enable_attention_slicing()
#     return pipe


# def _make_multiple_of_8(x: int) -> int:
#     return max(8, (int(x) + 7) // 8 * 8)


# def generate_design(product, use_case, platform, style,
#                     width=384, steps=20, guidance_scale=6.5,
#                     negative_prompt=None, seed=None, profile='balanced', exact=False):

#     pipe = get_pipe()

#     prompt = build_prompt(product, use_case, platform, style)

#     # Performance profile adjustments
#     profile = (profile or 'balanced').lower()
#     is_gpu = device == 'cuda'

#     if profile == 'fast':
#         # CPU-safe defaults
#         steps = min(int(steps), 12)
#         width = min(int(width), 320)
#         guidance_scale = float(guidance_scale) if guidance_scale is not None else 6.0
#     elif profile == 'high':
#         # High quality — only on GPU. If CPU, fall back to balanced.
#         if not is_gpu:
#             profile = 'balanced'
#         else:
#             steps = max(int(steps), 40)
#             width = max(int(width), 768)
#             guidance_scale = float(guidance_scale) if guidance_scale is not None else 7.5
#     else:
#         # balanced
#         steps = int(steps)
#         width = int(width)
#         guidance_scale = float(guidance_scale)

#     # Ensure dimensions are multiples of 8
#     try:
#         width = int(width)
#     except Exception:
#         width = 384
#     width = _make_multiple_of_8(width)

#     # compute target height per platform; normally we generate a square base (unless exact=True)
#     if platform == "banner":
#         target_h = max(8, width // 3)
#     elif platform == "poster":
#         target_h = max(8, int(width * 1.5))
#     else:
#         target_h = width

#     # If not exact, generate a square image (best for client-side cropping)
#     if not exact:
#         # choose square base large enough to cover target
#         base_size = max(width, target_h)
#         width = base_size
#         height = base_size
#     else:
#         height = target_h

#     height = _make_multiple_of_8(height)

#     # default negative prompt to reduce text/artifacts
#     if not negative_prompt:
#         negative_prompt = "text, letters, watermark, logo, blurry, low quality, deformed"

#     # seed handling
#     # deterministic default seed: hash of inputs (product/use_case/platform/style/profile/width/steps/guidance)
#     if seed is None:
#         digest = hashlib.sha256(f"{product}|{use_case}|{platform}|{style}|{profile}|{width}|{steps}|{guidance_scale}".encode('utf-8')).hexdigest()
#         # convert hex digest to int in a safe range
#         seed_i = int(digest[:16], 16) % (2 ** 31)
#     else:
#         try:
#             seed_i = int(seed)
#         except Exception:
#             seed_i = 0

#     gen = torch.Generator(device=device).manual_seed(seed_i)

#     with torch.inference_mode():
#         call_kwargs = dict(
#             prompt=prompt,
#             width=width,
#             height=height,
#             num_inference_steps=int(steps),
#             guidance_scale=float(guidance_scale),
#             negative_prompt=negative_prompt,
#             generator=gen,
#         )

#         image = pipe(**call_kwargs).images[0]

#     filename = f"{uuid.uuid4()}.png"
#     path = os.path.join(OUTPUT_DIR, filename)
#     image.save(path)
#     return path

import torch, os, uuid
from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler
from agent import build_prompt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "..", "outputs", "images")
os.makedirs(OUT_DIR, exist_ok=True)

MODEL = "runwayml/stable-diffusion-v1-5"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PIPE = None

TEMPLATE_SIZES = {
    "banner": (960, 320),
    "poster": (512, 768),
    "instagram": (640, 640)
}

def get_pipe():
    global PIPE
    if PIPE is None:
        dtype = torch.float16 if DEVICE == "cuda" else torch.float32
        PIPE = StableDiffusionPipeline.from_pretrained(MODEL, torch_dtype=dtype)
        PIPE.scheduler = EulerDiscreteScheduler.from_config(PIPE.scheduler.config)
        PIPE = PIPE.to(DEVICE)
        PIPE.enable_attention_slicing()
    return PIPE

def generate_design(product, use_case, platform, style,
                    template='sale_poster', width=None, steps=None,
                    guidance_scale=6.5, negative_prompt=None,
                    seed=None, profile='balanced', exact=False):
    pipe = get_pipe()

    # Determine platform from template when applicable
    tpl = (template or '').lower()
    if tpl in ('sale_poster', 'event_poster'):
        tpl_platform = 'poster'
    elif tpl == 'website_banner' or platform == 'banner':
        tpl_platform = 'banner'
    else:
        tpl_platform = platform or 'instagram'

    prompt = build_prompt(product, use_case, tpl_platform, style, template=tpl)

    # performance profile
    is_gpu = DEVICE == 'cuda'
    p = (profile or 'balanced').lower()
    if p == 'fast':
        steps = int(steps or 10)
        # small default sizes on fast
        default_w = 320
    elif p == 'high' and is_gpu:
        steps = int(steps or 40)
        default_w = 1024
    else:
        steps = int(steps or 20)
        default_w = 640

    # template sizes override when exact requested or when width not provided
    if exact or not width:
        if tpl_platform == 'banner':
            w, h = TEMPLATE_SIZES.get('banner')
        elif tpl_platform == 'poster':
            w, h = TEMPLATE_SIZES.get('poster')
        else:
            w, h = TEMPLATE_SIZES.get('instagram')
    else:
        w = int(width)
        # compute reasonable height per platform
        if tpl_platform == 'banner':
            h = max(8, w // 3)
        elif tpl_platform == 'poster':
            h = max(8, int(w * 1.5))
        else:
            h = w

    # ensure multiples of 8
    def _m8(x):
        return max(8, (int(x) + 7) // 8 * 8)

    width = _m8(w)
    height = _m8(h)

    # negative prompt defaults
    if not negative_prompt:
        negative_prompt = "text, letters, watermark, logo, low quality, blurry"

    # deterministic seed if none provided
    import hashlib
    if seed is None:
        digest = hashlib.sha256(f"{product}|{use_case}|{tpl_platform}|{style}|{tpl}|{profile}|{width}|{steps}|{guidance_scale}".encode('utf-8')).hexdigest()
        seed_i = int(digest[:16], 16) % (2 ** 31)
    else:
        try:
            seed_i = int(seed)
        except Exception:
            seed_i = 0

    gen = torch.Generator(device=DEVICE).manual_seed(seed_i)

    with torch.inference_mode():
        img = pipe(
            prompt,
            width=width,
            height=height,
            num_inference_steps=int(steps),
            guidance_scale=float(guidance_scale),
            negative_prompt=negative_prompt,
            generator=gen,
        ).images[0]

    name = f"{uuid.uuid4()}.png"
    path = os.path.join(OUT_DIR, name)
    img.save(path)
    return path
