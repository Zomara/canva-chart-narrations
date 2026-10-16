# Magic Studio Slide Narration Pipeline Spec

This spec defines how the Slide narration app turns one slide image and a target length in seconds into a narrated MP3 file that runs within 3 seconds of that target.

## 1. Model prompt (verbatim)

The app sends this text to the vision model through OpenRouter, along with the slide image. A vision model is an AI model that reads images as well as text. The app reads the model id from the `OPENROUTER_MODEL` setting in the local environment file and never hardcodes it. At run time the app fills in one value, `{target_words}`. Each sample slide in `canva_create_sample_slides.csv` has a `key_visual_point` column. The app never puts that value in the prompt and uses it only to score the finished script in section 4.

```
You are writing a spoken voiceover for the presentation slide in the attached image.
Start with what the chart, graph or main picture shows. Say the main change, trend or comparison in plain words, using the numbers you can read on it.
Only after that, cover the slide's title and written text.
Write about {target_words} words in total.
Write in short, natural spoken sentences, as one paragraph.
Do not say "this slide", "as you can see" or "in this image".
Do not read out axis labels, legends or every number one by one.
Return only the script text, with nothing before or after it.
```

## 2. Length formula

| Item | Value |
|---|---|
| Formula | target words = target seconds × 2.45 words per second |
| Rate | 2.45 words per second. This is the average from the edge-tts calibration run: 5 test scripts, voice `en-AU-NatashaNeural`, rate `+0%` |
| Rounding | Round to the nearest whole word. Exact halves round up. |
| Worked example | 30 seconds × 2.45 words per second = 73.5 → **74 words** |
| Gap | gap = MP3 length measured by mutagen (seconds), target seconds |

A positive gap means the audio runs too long. A negative gap means it runs too short.

## 3. Retry order and limit

The app runs a retry each time the gap is more than 3.0 seconds either way. Each retry is one action.

| Order | Step | Detail |
|---|---|---|
| 1 | edge-tts rate nudge | The script stays the same. The app changes the edge-tts speaking rate by 10 points and makes the MP3 again. If the gap is over +3.0 s, the rate goes faster (`+10%`). If the gap is under, 3.0 s, the rate goes slower (`-10%`). The rate never moves more than 20 points from `+0%`, so this step can run at most 2 times. |
| 2 | Model rewrite | This step runs only if the audio still misses after the rate nudges. The rate resets to `+0%`. The app sends the script back with the rewrite prompt below. It sets new target words to the current word count, round(gap × 2.45). |

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
| Limit reached with no timing pass | The app marks the run **failed**. It keeps the last script and MP3 in the log. It shows no download button. It shows this message: "Couldn't fit this narration within 3 seconds of {target} seconds. Last attempt: {measured} seconds." |

## 4. Pass / fail rule

| Rule | Value |
|---|---|
| Timing pass | The gap is between, 3.0 and +3.0 seconds, including exactly 3.0 |
| How length is measured | The app reads the length with `mutagen.mp3.MP3(path).info.length` on the saved MP3 file. It rounds the result to 0.1 seconds. |
| Not allowed | Estimating the length from the word count or from the target words |
| Coverage pass | The script states the slide's `key_visual_point`: the same fact, with the same direction and the same numbers. For example, "sales doubled after March" passes. "Sales changed over the year" fails. |
| Coverage check | The script is compared against `key_visual_point` after the run. The model never sees that value. |
| Failing runs | The app logs every failed run and shows it in the results table. It never drops, hides or quietly re-runs a failed run past the retry limit. |

The results table has these columns: `slide_id`, `target_length_seconds`, `measured_seconds`, `gap_seconds`, `retries_used`, `timing_verdict`, `coverage_verdict`.

## 5. Download rule

| Rule | Value |
|---|---|
| When the download appears | Only after the latest MP3 passes timing under section 4 |
| Before the timing pass | The audio player can play the current attempt. The app hides the download button. |
| After the timing pass | The app shows the download button for that exact MP3, with the measured length and the target side by side |
| Retry limit reached with no pass | The run is marked failed. The download button never appears. The failure message from section 3 is shown. |
| Coverage failure with a timing pass | The download still appears. The results table marks the row `coverage_verdict = FAIL`. |