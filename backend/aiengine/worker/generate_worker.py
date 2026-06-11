"""Self-contained text-to-image worker for the Nucleus AI engine.

Runs under the MANAGED runtime (or NUCLEUS_AIENGINE_PYTHON), never the Flask
process — this is the only Nucleus code that imports torch. It deliberately
imports nothing from backend/: the full model spec travels inside the job.

Modes:
  --check                  print a JSON capability report and exit
  (default)                read ONE json job line from stdin, generate, exit

Job line:
  {"prompt": str, "style": "tile"|"scene"|null, "width": int, "height": int,
   "seed": int|null, "out_path": str,
   "spec": {"repo_id": str, "pipeline_class": str, "dtype": str,
            "num_inference_steps": int, "guidance_scale": float}}

Output (NDJSON on stdout):
  {"event": "progress", "pct": 0.0-1.0, "desc": str}
  {"event": "result", "ok": true, "path": str, "seconds": float}
  {"event": "result", "ok": false, "error": str}
"""
import json
import sys
import time

# Baked style presets — the only two behaviors the skin lab uses (vendored
# from assetFarm's tileset_tile / environment recipes).
STYLES = {
    'tile': {
        'width': 512, 'height': 512,
        'prefix': 'seamless tileable texture, game tileset, repeating pattern, ',
    },
    'scene': {
        'width': 1536, 'height': 768,
        'prefix': 'game environment, scenic, detailed background, ',
    },
}

PROBE_PIPELINES = ('AutoPipelineForText2Image', 'Flux2KleinPipeline',
                   'ZImagePipeline')


def emit(obj):
    sys.stdout.write(json.dumps(obj) + '\n')
    sys.stdout.flush()


def check():
    report = {'ok': True, 'python': sys.version.split()[0]}
    try:
        import torch
        report['torch'] = torch.__version__
        report['cuda'] = torch.cuda.is_available()
        report['cudaDeviceName'] = (torch.cuda.get_device_name(0)
                                    if report['cuda'] else None)
    except Exception as e:
        report.update(ok=False, torch=None, cuda=False, error=f'torch: {e}')
        emit(report)
        return
    try:
        import diffusers
        report['diffusersVersion'] = diffusers.__version__
        report['pipelines'] = {name: hasattr(diffusers, name)
                               for name in PROBE_PIPELINES}
    except Exception as e:
        report.update(ok=False, diffusersVersion=None,
                      error=f'diffusers: {e}')
    emit(report)


def generate(job):
    import torch
    import diffusers

    spec = job['spec']
    style = STYLES.get(job.get('style') or '')
    prompt = job['prompt']
    if style:
        prompt = style['prefix'] + prompt
    width = int(job.get('width') or (style or STYLES['tile'])['width'])
    height = int(job.get('height') or (style or STYLES['tile'])['height'])
    steps = int(spec.get('num_inference_steps') or 4)

    emit({'event': 'progress', 'pct': 0.0,
          'desc': f'loading {spec["repo_id"]}…'})
    t0 = time.perf_counter()

    pipeline_cls = getattr(diffusers, spec['pipeline_class'])
    dtype = getattr(torch, spec.get('dtype') or 'float16', torch.float16)
    pipe = pipeline_cls.from_pretrained(spec['repo_id'], torch_dtype=dtype)
    if torch.cuda.is_available():
        pipe.enable_model_cpu_offload()
    pipe.set_progress_bar_config(disable=True)

    load_s = time.perf_counter() - t0
    emit({'event': 'progress', 'pct': 0.05,
          'desc': f'model loaded in {load_s:.1f}s'})
    gen_t0 = time.perf_counter()

    def on_step(_pipeline, step_index, _timestep, callback_kwargs):
        done = step_index + 1
        elapsed = time.perf_counter() - gen_t0
        eta = elapsed / done * (steps - done)
        emit({'event': 'progress', 'pct': 0.05 + 0.9 * done / steps,
              'desc': f'step {done}/{steps} | {elapsed:.1f}s / ~{elapsed + eta:.1f}s'})
        return callback_kwargs

    generator = None
    if job.get('seed') is not None:
        generator = torch.Generator(device='cpu').manual_seed(int(job['seed']))

    result = pipe(
        prompt=prompt,
        width=width,
        height=height,
        guidance_scale=float(spec.get('guidance_scale') or 0.0),
        num_inference_steps=steps,
        generator=generator,
        callback_on_step_end=on_step,
    )
    image = result.images[0]
    out_path = job['out_path']
    image.save(out_path, format='PNG')
    emit({'event': 'result', 'ok': True, 'path': out_path,
          'seconds': round(time.perf_counter() - t0, 1)})


def main():
    if '--check' in sys.argv:
        check()
        return
    try:
        job = json.loads(sys.stdin.readline())
    except (json.JSONDecodeError, ValueError) as e:
        emit({'event': 'result', 'ok': False, 'error': f'bad job line: {e}'})
        sys.exit(1)
    try:
        generate(job)
    except Exception as e:
        emit({'event': 'result', 'ok': False,
              'error': f'{type(e).__name__}: {e}'})
        sys.exit(1)


if __name__ == '__main__':
    main()
