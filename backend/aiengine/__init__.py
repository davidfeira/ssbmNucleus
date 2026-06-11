"""Vendored local-diffusion engine + provider plumbing for the AI Studios.

Host half (this package, imported by the Flask process — never imports torch):
  paths           on-disk layout (managed runtime, config, ledgers)
  registry        the model catalog (specs, VRAM/disk estimates, tier fit)
  hardware        GPU / disk detection
  settings_store  storage/ai_studio.json (tier routing, disabled models)
  routing         task tier -> (provider, model) resolution
  telemetry       storage/ai_runs.jsonl generation ledger
  models_admin    HF cache scan / download / delete
  installer       managed Python runtime + torch/diffusers install
  runner          spawns the generate worker, NDJSON protocol

Worker half (worker/generate_worker.py): self-contained script executed by the
managed runtime (or NUCLEUS_AIENGINE_PYTHON); the only code that touches torch.
"""
