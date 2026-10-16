# Canva Chart Narrations

A mock scenario set in a fictional Canva context. The end goal is a Streamlit app: upload slides, a vision model reads the text and charts, writes a narration script of a target length, and edge-tts turns it into an MP3. There is no real Canva integration.

## Files

| File | Purpose |
|---|---|
| `calibrate.py` | Generates one MP3 per passage and reads each file's real duration with mutagen |
| `calibration.csv` | Per-passage words, characters, seconds and words/s |
| `audio/` | The calibration MP3s |
| `PIPELINE_SPEC.md` | The rules the app follows: prompt, length formula, retries, pass/fail, download button |
| `Magic Studio Slide Narration Pipeline Spec.md` | Example spec from another project, used as a style reference |

## Fixed numbers (from calibration)

- Voice `en-US-AriaNeural`, rate `+0%`
- 2.65 words/s (424 words / 160.06 s, 8 passages); the per-passage range is 2.29–2.87
- Timing tolerance ±3.0 s, measured with mutagen

## Rules

- `PIPELINE_SPEC.md` is the plan file. Code must follow it, or the spec gets updated first.
- Do not name a model provider unless the brief specifies one; read the model id from `.env`.
- Never send `key_visual_point` to the narration model.
- Never commit `.env` or API keys.
