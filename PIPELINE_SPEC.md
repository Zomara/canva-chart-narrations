# Canva Chart Narration Pipeline Spec

This spec sets the rules the app follows. For each slide, the app takes the slide image and a target length in seconds, and makes a narrated MP3 that runs within 3 seconds of that target. Every later stage builds against these rules.

## 1. Model prompt (verbatim)

The app sends this prompt and the slide image to a vision model. A vision model is an AI model that reads images as well as text. The app reads the model id from a setting in the local `.env` file and never hardcodes it.

Below is every word the model receives, exactly as sent, for a 30-second target:

```
You are writing a spoken voiceover for the presentation slide in the attached image.
Describe the chart, graph or picture first, before anything else on the slide. Use the numbers you can read on it.
After that, cover the slide's title and written text.
Write about 80 words in total.
Write short, natural spoken sentences as one paragraph.
Do not say "this slide", "as you can see" or "in this image".
Do not read out axis labels, legend entries or every number one by one.
Return only the script text, with nothing before or after it.
```

Only one part ever changes: the number on line 4 ("80"). The app sets it to the target words from section 2. For example, a 10-second target sends "Write about 27 words in total." Every other word stays exactly as shown.

Each test slide also has a `key_visual_point`: the one chart fact the narration must state. The app never sends that value, or any instruction about it, to the narration model. It is used only for the coverage check in section 4.

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

The app retries when the gap is more than 3.0 seconds in either direction. It stops as soon as an attempt passes. Otherwise it runs these retries in this exact order:

| Retry | Action | Adjustment |
|---|---|---|
| 1 | edge-tts rate nudge | The script stays the same. The rate moves exactly **10 points** from `+0%`: gap over +3.0 s → `+10%` (faster); gap under −3.0 s → `-10%` (slower). The app makes the MP3 again. |
| 2 | edge-tts rate nudge | The script stays the same. The rate moves exactly **10 more points** in the direction the new gap points. This gives `+20%`, `-20%` or back to `+0%`. The app makes the MP3 again. |
| 3 | Model rewrite | The rate resets to `+0%`. The app sizes the rewrite from the **first attempt**, the latest MP3 measured at `+0%`, using the rewrite formula below. It never uses the gaps from retries 1 and 2, because a sped-up or slowed-down MP3 hides the script's real length. The app sends the script with the rewrite prompt below. |
| 4 | Model rewrite | Rate stays `+0%`. Same as retry 3, but sized from **retry 3**, now the latest MP3 measured at `+0%`. |

### Rewrite formula

```
new target words = round(script words × target seconds ÷ measured seconds)
```

- **script words** = the number of words in the script that was actually spoken in the latest `+0%` MP3. This is the model's real output, counted by the app, not the number it was asked for.
- **measured seconds** = that MP3's length, measured with mutagen.
- Rounding: nearest whole word, exact halves round up.

Why it does not use 2.65: a slide misses its target because its script does not speak at 2.65 words per second (numbers, long words and punctuation change the pace). The formula uses this slide's own measured pace instead: script words ÷ measured seconds. 2.65 still sets the first attempt (section 2).

### Worked example: one slide through all five attempts

Target 30 s → first attempt 80 words (section 2). This slide's script speaks slower than average and runs 40.0 s at `+0%`. The rewrite model returns a few more words than asked, as models often do.

| Attempt | Rate | Script words | Measured | Gap | Result | What the next step uses |
|---|---|---|---|---|---|---|
| First | `+0%` | 80 | 40.0 s | +10.0 | fail | Gap over +3.0 → speed up |
| Retry 1 | `+10%` | 80 | 36.4 s | +6.4 | fail | Gap still over +3.0 → speed up again |
| Retry 2 | `+20%` | 80 | 33.3 s | +3.3 | fail | Nudges used up → rewrite, sized from the **first attempt** (80 words, 40.0 s at `+0%`), not from this +3.3 |
| Retry 3 | `+0%` | asked round(80 × 30 ÷ 40.0) = 60, model returned **68** | 34.0 s | +4.0 | fail | Rewrite, sized from **retry 3** (68 words, 34.0 s at `+0%`) |
| Retry 4 | `+0%` | asked round(68 × 30 ÷ 34.0) = 60, model returned **61** | 30.5 s | +0.5 | **pass** | Download button appears |

If retry 3 had used the +3.3 gap from retry 2, the rewrite would have asked for about 71 words (35.5 s) and missed by more.

Rewrite prompt (verbatim):

```
Rewrite this voiceover script in about {target_words} words.
Keep the chart, graph or picture first. Keep the same facts and numbers.
Return only the script text.

Script: {script}
```

| Rule | Value |
|---|---|
| Retry limit | Hard cap of **4 retries** after the first attempt (5 MP3s at most). After retry 4 the pipeline stops, even if a further retry might have passed. |
| Limit reached without a timing pass | The run is marked **failed**. The app keeps the last script and MP3 in the log and shows no download button. It shows: "Couldn't fit this narration within 3 seconds of {target} seconds. Last attempt: {measured} seconds." |

## 4. Pass / fail rules

| Rule | Value |
|---|---|
| Allowed difference | **3.0 seconds** between the target duration and the measured MP3 duration |
| Timing pass | The gap is from −3.0 to +3.0 seconds, including exactly ±3.0 |
| Timing fail | The gap is more than 3.0 seconds in either direction |
| How length is measured | `mutagen.mp3.MP3(path).info.length` on the saved MP3 file, rounded to 0.1 seconds |
| Not allowed | Estimating the length from the word count or from the target words |
| Failed runs | Every failed run is logged and shown in the results table. A failed run is never dropped, hidden or quietly re-run past the retry limit. |

### Coverage rule

| Rule | Value |
|---|---|
| When it is judged | Once, after the final attempt (pass or fail on timing). It is a separate, text-only check and never part of the narration prompt. |
| Inputs | The final script and the slide's `key_visual_point`. The slide image is not used. |
| Evidence | The check must quote the exact sentence from the script that states the key point. No quote means FAIL. |
| Coverage pass | All three match: **fact** (same subject and measure), **direction** (same up / down / flat / bigger-than), and **numbers** (every number in `key_visual_point` appears with the same value). The format may differ ("$48" = "forty-eight dollars"). Rounding to a different value fails. |
| Pass example | Key point "Sales doubled after March". Script: "Sales doubled once March began." → PASS |
| Fail examples | "Sales changed over the year" (no direction or amount) → FAIL. "Sales rose about 50% after March" (wrong number) → FAIL. |
| On coverage FAIL | No retry: the narration model is never told the key point. The row is marked `coverage_verdict = FAIL` and the run is still logged and shown. |

The results table has these columns: `slide_id`, `target_seconds`, `target_words`, `final_words`, `measured_seconds`, `gap_seconds`, `retries_used`, `timing_verdict`, `coverage_verdict`, `coverage_quote`.

## 5. Download button rule

| Rule | Value |
|---|---|
| When the download button appears | Only after the latest MP3 passes timing under section 4 |
| Before a timing pass | The audio player can play the current attempt. The download button stays hidden. |
| After a timing pass | The app shows the download button for that exact MP3, with the measured length and the target side by side |
| Retry limit reached without a pass | The run is marked failed. The download button never appears. The failure message from section 3 is shown. |
| Coverage FAIL with a timing pass | The download button still appears. The results table marks the row `coverage_verdict = FAIL`. |
