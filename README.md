# Soccer Coach Clip Analysis Demo

This workspace contains a RocketRide demo workflow for coach-driven soccer clip analysis. The workflow is split into three `.pipe` files because RocketRide pipelines have one source node each.

## Pipelines

- `.github/demo.pipe` is the coach chat workflow. A Deep Agent orchestrator receives the coach question, calls vector-search tools for clip and tactics context, delegates to passing, positioning, speed, defending, and tactics subagents as needed, then returns one coach-facing summary.
- `clip_index.pipe` indexes detailed text summaries from `video-data/clip-summaries` into the local Chroma collection `soccer_clip_summaries_demo`.
- `tactics_upload.pipe` exposes a Dropper node for uploaded coaching tactics and stores them in the local Chroma collection `coach_tactics_demo`.

Both indexing and chat search use `embedding_transformer` with the `miniLM` profile, so the stored vectors and query vectors are compatible.

## Demo Setup

1. Configure RocketRide in the VS Code extension so it can populate `ROCKETRIDE_URI` and `ROCKETRIDE_APIKEY`.
2. Create a local `.env` from `env.example` and set `ROCKETRIDE_GMI_CLOUD_APIKEY`.
3. Make sure Chroma is available at `localhost:8330`, or change the `chroma` nodes in all three pipeline files to your Chroma host.
4. Run `clip_index.pipe` once to index the real clip summaries.
5. Run `tactics_upload.pipe` and upload `video-data/sample-uploads/possession_and_rest_defense_tactics.txt` through the Dropper UI.
6. Run `.github/demo.pipe` and ask the Coach Chat node: `I want to see clips where we failed to trigger the 6-second press`.

Expected behavior: the orchestrator should retrieve clips such as `clip_020_025_turnover_press_failure` or `clip_045_050_transition_press_lapse`, use the uploaded possession tactics when relevant, delegate to the specialist subagents that match the question, and answer with the clip timestamp, skill scores, a combined score, and a concise coaching summary.

## Validate The Wiring

Run this local structural check before starting the RocketRide pipelines:

```powershell
python check.py
```