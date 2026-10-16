# Canva Chart Narration Pipeline Spec

This spec sets the rules the app follows. For each slide, the app takes the slide image and a target length in seconds, and makes a narrated MP3 that runs within 3 seconds of that target. Every later stage builds against these rules.

## 1. Model prompt (verbatim)

The app sends this prompt and the slide image to a vision model. A vision model is an AI model that reads images as well as text. The app reads the model id from a setting in the local `.env` file and never hardcodes it. At run time the app fills in one value, `{target_words}`, from section 2.

```
You are writing a spoken voiceover for the presentation slide in the attached image.
Start with the chart, graph or main picture. In plain words, say what changed, what the trend is, or what is being compared, and use the numbers you can read on it.
After that, cover the slide's title and written text.
Write about {target_words} words in total.
Write short, natural spoken sentences as one paragraph.
Do not say "this slide", "as you can see" or "in this image".
Do not read out axis labels, legend entries or every number one by one.
Return only the script text, with nothing before or after it.
```

## 2. Word count formula

| Item | Value |
|---|---|
| Formula | target words = target seconds × 2.65 words per second |
| Rate | 2.65 words per second, measured in Stage 1: 424 words over 160.06 seconds of MP3 audio, 8 passages, voice `en-US-AriaNeural`, rate `+0%`. Each MP3 length was read with mutagen. |
| Rounding | Round to the nearest whole word. Exact halves round up. |
| Worked example | 30 seconds × 2.65 = 79.5 → **80 words** |
| Second example | 10 seconds × 2.65 = 26.5 → **27 words** |
| Gap | gap = measured MP3 length (seconds) − target seconds |

A positive gap means the audio is too long. A negative gap means it is too short.

Why retries are needed: in Stage 1 the per-passage rate ran from 2.29 to 2.87 words per second. An 80-word script can therefore run anywhere from about 28 to 35 seconds, so the first attempt can miss the window.

## 3. Retry order and limit

The app retries when the gap is more than 3.0 seconds in either direction. Each retry is one action, done in this order:

| Order | Step | Detail |
|---|---|---|
| 1 | edge-tts rate nudge | The script stays the same. The app moves the edge-tts speaking rate by 10 points and makes the MP3 again. Gap over +3.0 s: speak faster (`+10%`). Gap under −3.0 s: speak slower (`-10%`). The rate never moves more than 20 points from `+0%`, so this step runs at most 2 times. |
| 2 | Model rewrite | Runs only if the audio still misses after the rate nudges. The rate resets to `+0%`, because the 2.65 rate was measured at `+0%`. The app sends the script back with the rewrite prompt below. New target words = current word count − round(gap × 2.65). |

Rewrite prompt (verbatim):

```
Rewrite this voiceover script in about {target_words} words.
Keep the chart or main picture first. Keep the same facts and numbers.
Return only the script text.

Script: {script}
```

| Rule | Value |
|---|---|
| Retry limit | 4 retries after the first attempt: up to 2 rate nudges, then up to 2 model rewrites |
| Limit reached without a timing pass | The run is marked **failed**. The app keeps the last script and MP3 in the log and shows no download button. It shows: "Couldn't fit this narration within 3 seconds of {target} seconds. Last attempt: {measured} seconds." |

## 4. Pass / fail rules

| Rule | Value |
|---|---|
| Timing pass | The gap is from −3.0 to +3.0 seconds, including exactly ±3.0 |
| How length is measured | `mutagen.mp3.MP3(path).info.length` on the saved MP3 file, rounded to 0.1 seconds |
| Not allowed | Estimating the length from the word count or from the target words |
| Failed runs | Every failed run is logged and shown in the results table. A failed run is never dropped, hidden or quietly re-run past the retry limit. |

The results table has these columns: `slide_id`, `target_seconds`, `target_words`, `final_words`, `measured_seconds`, `gap_seconds`, `retries_used`, `timing_verdict`.

## 5. Download button rule

| Rule | Value |
|---|---|
| When the download button appears | Only after the latest MP3 passes timing under section 4 |
| Before a timing pass | The audio player can play the current attempt. The download button stays hidden. |
| After a timing pass | The app shows the download button for that exact MP3, with the measured length and the target side by side |
| Retry limit reached without a pass | The run is marked failed. The download button never appears. The failure message from section 3 is shown. |
