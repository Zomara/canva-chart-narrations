"""Stage 1: calibration.

Generate one MP3 per passage with a single edge-tts voice, then read each file's
real duration with mutagen. The output CSV relates text length to spoken time so
later stages can size a script to a target duration.

Usage:
    python calibrate.py [passages.csv] [--voice en-US-AriaNeural] [--out audio]
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3

DEFAULT_VOICE = "en-US-AriaNeural"
TEXT_COLUMNS = ("passage text", "text", "passage", "script", "narration")
ID_COLUMNS = ("passage id", "id", "passage_id", "name")


def load_passages(csv_path: Path) -> list[tuple[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = {name.lower().strip(): name for name in reader.fieldnames or []}
        text_col = next((fields[c] for c in TEXT_COLUMNS if c in fields), None)
        if text_col is None:
            sys.exit(f"No text column found in {csv_path}. Expected one of {TEXT_COLUMNS}, got {list(fields)}")
        id_col = next((fields[c] for c in ID_COLUMNS if c in fields), None)

        passages = []
        for i, row in enumerate(reader, start=1):
            pid = (row[id_col].strip() if id_col and row[id_col] else f"p{i:02d}")
            passages.append((pid, (row[text_col] or "").strip()))
        return passages


async def synthesize(text: str, voice: str, path: Path) -> None:
    await edge_tts.Communicate(text, voice).save(str(path))


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", default="canva_calibration_passages_97f1f7285cd742e080a8c2ebfa213883.csv", type=Path)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--out", default="audio", type=Path)
    parser.add_argument("--results", default="calibration.csv", type=Path)
    args = parser.parse_args()

    passages = load_passages(args.csv)
    args.out.mkdir(exist_ok=True)
    print(f"Voice: {args.voice} | Passages: {len(passages)}\n")
    print(f"{'id':<10}{'words':>7}{'chars':>7}{'seconds':>9}{'words/s':>9}")

    rows, skipped = [], []
    for pid, text in passages:
        if not text:
            skipped.append((pid, "Passage text is empty, so there is nothing to speak."))
            continue
        mp3_path = args.out / f"{pid}.mp3"
        try:
            await synthesize(text, args.voice, mp3_path)
            seconds = MP3(mp3_path).info.length
        except Exception as e:
            skipped.append((pid, f"Audio generation or duration read failed: {type(e).__name__}: {e}"))
            continue
        if seconds <= 0:
            skipped.append((pid, "MP3 was created but has zero duration."))
            continue
        words, chars = len(text.split()), len(text)
        rows.append({"id": pid, "words": words, "chars": chars,
                     "seconds": round(seconds, 3), "words_per_sec": round(words / seconds, 3),
                     "file": mp3_path.as_posix()})
        print(f"{pid:<10}{words:>7}{chars:>7}{seconds:>9.2f}{words / seconds:>9.2f}")

    with args.results.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    total_words = sum(r["words"] for r in rows)
    total_secs = sum(r["seconds"] for r in rows)
    print(f"\nTotal: {total_words} words in {total_secs:.2f}s -> "
          f"{total_words / total_secs:.2f} words/s ({60 * total_words / total_secs:.0f} wpm)")
    print(f"Saved {len(rows)} MP3s to {args.out}/ and results to {args.results}")
    print(f"Skipped: {len(skipped)}")
    for pid, reason in skipped:
        print(f"  {pid}: {reason}")


if __name__ == "__main__":
    asyncio.run(main())
