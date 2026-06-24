# AI Video Evolver

> An evolvable, self-improving scaffold for end-to-end AI video generation
> agents, built on top of the SEMAS framework.

This package demonstrates how to model an AI video generation pipeline as a
multi-agent system whose prompts, tools, and workflow topology can evolve based
on downstream quality metrics.

## What it models

```text
Input prompt / script
       │
       ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Scriptwriter │────▶│ Prompt Engineer  │────▶│ Asset Generator │
│   agent      │     │     agent        │     │    agent        │
└─────────────┘     └──────────────────┘     └─────────────────┘
                                                      │
                       ┌─────────────┐               │
                       │    Critic   │◀──────────────┘
                       │   agent     │
                       └──────┬──────┘
                              │
                              ▼
                       Feedback loop
```

- **Scriptwriter**: turns a high-level idea into scene descriptions.
- **Prompt Engineer**: turns scene descriptions into video model prompts.
- **Asset Generator**: calls a video/image generation backend (stubbed by
  default; plug in Runway / Pika / ComfyUI).
- **Editor**: adds captions, transitions, and post-processing (FFmpeg stubs).
- **Critic**: scores the result on prompt adherence, temporal coherence,
  aesthetics, and safety.

## Install

From the repo root:

```bash
pip install -e ./ai_video_evolver
```

Or just run in-place (SEMAS must be importable from the repo root):

```bash
cd C:/aicoding/semas_framework
python -m ai_video_evolver.demo
```

## Quick start

Run the deterministic demo:

```bash
python -m ai_video_evolver.demo
```

Run the full evolution runner on a sample task:

```bash
python -m ai_video_evolver.run_video_evolution ai_video_evolver/examples/sample_task.yaml
```

Run tests:

```bash
python -m pytest tests/test_ai_video_evolver.py -q
```

## Replacing stubs with real models

1. Edit `ai_video_evolver/tools/video_api_client.py` and implement
   `generate_video_from_prompt` using your backend.
2. Edit `ai_video_evolver/evaluator/metrics.py` to call real quality models
   (CLIP, FVD, etc.).
3. Provide API keys via environment variables or a config file.

## Architecture

- `agents/` — YAML genome definitions for each role.
- `tools/` — Python tool sources used by the agents.
- `topologies/` — `TopologyGenome` definitions for the workflow.
- `evaluator/` — Domain metrics for video quality.
- `executor.py` — `ExecutorFn` that runs the topology.
- `mutator.py` — Deterministic mutators for offline demo/CI.
- `run_video_evolution.py` — High-level evolution runner.
- `demo.py` — Minimal runnable example.
