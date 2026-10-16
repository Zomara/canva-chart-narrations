# Canva Chart Narrations

A Zero University mock scenario. The final goal is a Streamlit app: you upload a slide deck, a model reads the slide text and images (including charts), writes a narration transcript, and turns it into an MP3 of a target length.

## Stage 1: Calibration

`calibrate.py` reads the passages CSV, creates one MP3 per passage with a single edge-tts voice, and reads each file's real duration with mutagen. It writes the per-passage results to `calibration.csv`. Later stages use this words-per-second rate to size a script to a requested length (e.g. 10 seconds is about 26 words).

**Voice:** `en-US-AriaNeural`

### Run it

```bash
python -m venv .venv
.venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python calibrate.py
```

### Terminal output

```text
Voice: en-US-AriaNeural | Passages: 8

id          words  chars  seconds  words/s
p01            25    157     8.98     2.79
p02            59    329    21.48     2.75
p03            22    129     9.60     2.29
p04            80    460    29.76     2.69
p05            31    210    13.49     2.30
p06            71    385    27.77     2.56
p07            47    282    17.95     2.62
p08            89    482    31.03     2.87

Total: 424 words in 160.06s -> 2.65 words/s (159 wpm)
Saved 8 MP3s to audio/ and results to calibration.csv
Skipped: 0
```

### Passages tested

All passages come from `canva_calibration_passages_97f1f7285cd742e080a8c2ebfa213883.csv`. Each one is quoted in full below, followed by its measured duration.

**p01** (25 words, 8.98 s, `audio/p01.mp3`)

> Revenue climbed steadily through the quarter, then jumped sharply in March as the new plan launched, lifting monthly totals to their highest point this year.

**p02** (59 words, 21.48 s, `audio/p02.mp3`)

> This funnel shows how visitors move from the pricing page to a paid plan. About ten thousand people viewed pricing in February. Just under four thousand started a free trial, and roughly nine hundred went on to pay. The biggest drop happens between the trial and the first payment, so that step is where the team will focus next.

**p03** (22 words, 9.60 s, `audio/p03.mp3`)

> This pie chart splits new sign-ups by source. Organic search brings in almost half, with referrals and paid ads sharing the rest.

**p04** (80 words, 29.76 s, `audio/p04.mp3`)

> This chart combines two measures from the support team. The bars show how many tickets arrived each week, and the line shows the average time to a first reply. Ticket volume stayed between roughly eleven and thirteen hundred a week for the whole period. Even so, reply times fell from about nine hours in early February to under four hours by mid March. The team handled the same workload much faster, mostly because common questions now get an instant answer.

**p05** (31 words, 13.49 s, `audio/p05.mp3`)

> This slide walks through three regions. Growth was strongest in Asia Pacific, where sign-ups nearly doubled between January and March, while Europe held flat and North America dipped slightly before recovering.

**p06** (71 words, 27.77 s, `audio/p06.mp3`)

> Here the stacked bars break down average monthly spend per team account. In January the typical account paid $48, mostly on seats. By March that rose to $61, and nearly all of the extra came from the new add-ons shown in green. Seat spending barely moved. So the growth is not coming from bigger teams, it is coming from teams buying more features on top of the plan they already have.

**p07** (47 words, 17.95 s, `audio/p07.mp3`)

> Costs stayed under control all year. The bar chart shows spending on each team holding within budget, with only marketing rising slightly in the final quarter. That increase paid for the spring campaign, and it still left the company around four percent under its total annual plan.

**p08** (89 words, 31.03 s, `audio/p08.mp3`)

> The map on this slide shades each country by how many templates were used in the last six weeks. Darker colours mean more use. The United States and India stand out as the two darkest areas, but the fastest change is in Brazil and Indonesia, where usage grew by more than half since the start of February. Australia is smaller in total, yet it has the highest use per person of any market. If we want feedback on new templates, these four countries are the clearest places to start.

### Failed passages and exclusions

None. All 8 passages generated audio and returned a valid duration, so no passage was skipped or excluded.

The script records a separate reason for each passage it skips. It skips a passage when the text is empty, when audio generation or the duration read fails, or when the MP3 has zero duration. Each reason is printed under `Skipped:` in the terminal output.

## Stage 2

## Stage 3

## Stage 4
