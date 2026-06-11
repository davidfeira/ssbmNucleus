"""The model catalog — vendored and trimmed from assetFarm's registry.

Image models only. Local entries run in the generate worker (diffusers);
API entries are OpenRouter image models billed per call. `tier_fit` says
which task tiers a model produces acceptable results for: 'standard' is
seamless material swatches, 'strong' is coherent scene work (stage
backdrops) that 1-step turbo models can't compose.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelSpec:
    id: str
    repo_id: str                 # HF repo (local) or OpenRouter slug (api)
    kind: str                    # 'local' | 'api'
    pipeline_class: str = ''
    dtype: str = 'float16'
    vram_estimate_gb: float = 0.0
    disk_estimate_gb: float = 0.0
    num_inference_steps: int = 1
    guidance_scale: float = 0.0
    description: str = ''
    speed_blurb: str = ''        # static hint shown until measured stats exist
    tier_fit: frozenset = field(default_factory=frozenset)
    cost_per_image_usd: float = 0.0


MODELS = {
    'sd-turbo': ModelSpec(
        id='sd-turbo',
        repo_id='stabilityai/sd-turbo',
        kind='local',
        pipeline_class='AutoPipelineForText2Image',
        dtype='float16',
        vram_estimate_gb=3.0,
        disk_estimate_gb=2.5,
        num_inference_steps=1,
        guidance_scale=0.0,
        description='SD-Turbo — 1-step 512px drafts and texture tiles',
        speed_blurb='fastest',
        tier_fit=frozenset({'standard'}),
    ),
    'flux-klein-4b': ModelSpec(
        id='flux-klein-4b',
        repo_id='black-forest-labs/FLUX.2-klein-4B',
        kind='local',
        pipeline_class='Flux2KleinPipeline',
        dtype='bfloat16',
        vram_estimate_gb=13.0,
        disk_estimate_gb=13.0,
        num_inference_steps=4,
        guidance_scale=1.0,
        description='FLUX.2 Klein 4B — sharper materials, handles scenes',
        speed_blurb='slower',
        tier_fit=frozenset({'standard', 'strong'}),
    ),
    'z-image-turbo': ModelSpec(
        id='z-image-turbo',
        repo_id='Tongyi-MAI/Z-Image-Turbo',
        kind='local',
        pipeline_class='ZImagePipeline',
        dtype='bfloat16',
        vram_estimate_gb=16.0,
        disk_estimate_gb=17.0,
        num_inference_steps=8,
        guidance_scale=1.0,
        description='Z-Image Turbo 6B — best local quality, scene-capable',
        speed_blurb='slowest',
        tier_fit=frozenset({'standard', 'strong'}),
    ),
    # --- API models (no local VRAM, billed per call) ---
    'gemini-image': ModelSpec(
        id='gemini-image',
        repo_id='google/gemini-2.5-flash-image',
        kind='api',
        description='Nano Banana (Gemini 2.5 Flash Image) — fast, cheap API tier',
        tier_fit=frozenset({'standard', 'strong'}),
        cost_per_image_usd=0.04,
    ),
    'gemini-image-pro': ModelSpec(
        id='gemini-image-pro',
        repo_id='google/gemini-3-pro-image-preview',
        kind='api',
        description='Nano Banana Pro (Gemini 3 Pro Image) — top tier',
        tier_fit=frozenset({'standard', 'strong'}),
        cost_per_image_usd=0.15,
    ),
    'gpt-image-mini': ModelSpec(
        id='gpt-image-mini',
        repo_id='openai/gpt-5-image-mini',
        kind='api',
        description='GPT-5 Image Mini — cheaper OpenAI image tier',
        tier_fit=frozenset({'standard', 'strong'}),
        cost_per_image_usd=0.04,
    ),
}

# Resolver preference order per tier (filtered by what's usable at runtime).
TIER_LOCAL_PREFERENCE = {
    'standard': ['sd-turbo', 'flux-klein-4b', 'z-image-turbo'],
    'strong': ['z-image-turbo', 'flux-klein-4b'],
}
DEFAULT_API_MODEL = 'gemini-image'


def find(model):
    """Look a model up by registry id OR repo/OpenRouter slug ('google/...').
    Returns the ModelSpec or None."""
    if not model:
        return None
    spec = MODELS.get(model)
    if spec:
        return spec
    return next((s for s in MODELS.values() if s.repo_id == model), None)


def local_models():
    return [s for s in MODELS.values() if s.kind == 'local']


def api_models():
    return [s for s in MODELS.values() if s.kind == 'api']
