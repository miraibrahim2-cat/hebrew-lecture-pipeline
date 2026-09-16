#!/usr/bin/env python
"""
Transcribe a lecture recording into your notes folder.

Runs offline on the CPU using the ivrit-ai Hebrew Whisper model, which also
handles English and mixed Hebrew/English lectures.

    transcribe.py RECORDING [RECORDING ...] --course 71204
    transcribe.py ~/Downloads/*.m4a --course immunology
    transcribe.py talk.mp4 --course 71204 --lang he     # skip detection
    transcribe.py --list                                 # show course names

Writes  <name>.txt  and  <name>.srt  into  <notes>/<course>/transcripts/.

Terminology listed at the bottom of the course's _style.md is fed to Whisper as
context, which sharply improves accuracy on course-specific words and on the
English terms that show up mid-Hebrew-sentence.

Run it inside the transcribe env:
    conda run -n transcribe python ~/lectures/transcribe.py ...
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"
MEDIA = {".m4a", ".mp3", ".mp4", ".mov", ".m4v", ".wav", ".aac", ".flac", ".webm", ".mkv"}
CONFIG = Path.home() / ".lecture-vault"

VAULT: Path | None = None       # resolved in main()


def resolve_vault(override: str | None) -> Path:
    """
    Where the notes live. Resolution order:
      1. --vault on the command line
      2. LECTURE_VAULT in the environment
      3. ~/.lecture-vault, a one-line file written by setup.sh
    """
    if override:
        return Path(override).expanduser()
    if os.environ.get("LECTURE_VAULT"):
        return Path(os.environ["LECTURE_VAULT"]).expanduser()
    if CONFIG.is_file():
        line = CONFIG.read_text(encoding="utf-8").strip()
        if line:
            return Path(line).expanduser()
    sys.exit(
        "I don't know where your notes folder is. Set it once:\n"
        f'    echo "/path/to/your/notes" > {CONFIG}\n'
        "or pass  --vault /path/to/your/notes"
    )


def courses() -> list[Path]:
    if not VAULT.is_dir():
        sys.exit(f"Notes folder not found at {VAULT}")
    return sorted(p for p in VAULT.iterdir()
                  if p.is_dir() and not p.name.startswith((".", "_")))


def find_course(name: str) -> Path:
    """Match a course by number (71204), by substring, or exactly."""
    all_courses = courses()
    for c in all_courses:
        if c.name == name:
            return c
    hits = [c for c in all_courses if name.lower() in c.name.lower()]
    if len(hits) == 1:
        return hits[0]
    if hits:
        sys.exit("'%s' matches several courses:\n  %s"
                 % (name, "\n  ".join(c.name for c in hits)))
    sys.exit("No course matching '%s'. Available:\n  %s"
             % (name, "\n  ".join(c.name for c in all_courses)))


def terminology(course: Path) -> str | None:
    """
    Pull the vocabulary list from the end of _style.md and turn it into an
    initial_prompt. Whisper uses this as preceding context, so it biases the
    decoder toward these spellings instead of guessing phonetically.
    """
    style = course / "_style.md"
    if not style.is_file():
        return None
    text = style.read_text(encoding="utf-8")
    marker = re.search(r"\*\*Terminology to expect\*\*[^\n]*\n", text)
    if not marker:
        return None
    tail = text[marker.end():]
    words = [w.strip(" -*\t") for w in re.split(r"[\n,;]+", tail)]
    words = [w for w in words if w and not w.startswith("#") and len(w) < 60
             and not w.startswith("_(")]          # ignore the "_(none yet)_" placeholder
    if not words:
        return None
    return ", ".join(words)


def build_prompt(course: Path, which: str | None) -> str:
    """
    Assemble everything a web-chat assistant needs into one pasteable block:
    the user's rules, the course specifics, and the transcript. For ChatGPT,
    Gemini, Claude.ai and anything else that cannot read local files.
    """
    tdir = course / "transcripts"
    if not tdir.is_dir():
        sys.exit(f"No transcripts yet in {tdir}")
    found = sorted((f for f in tdir.glob("*.txt")),
                   key=lambda f: f.stat().st_mtime, reverse=True)
    if which:
        found = [f for f in found if which.lower() in f.name.lower()] or found
    if not found:
        sys.exit(f"No transcripts found in {tdir}")
    transcript = found[0]

    parts = []
    instructions = VAULT / "_instructions.md"
    if instructions.is_file():
        body = instructions.read_text(encoding="utf-8")
        if "<!--" in body and "למילוי" in body:
            print("note: _instructions.md is still the blank template. The assistant\n"
                  "      will not know how you want notes written until you fill it in.\n",
                  file=sys.stderr)
        parts.append("=== HOW I WANT NOTES WRITTEN ===\n\n" + body)

    style = course / "_style.md"
    if style.is_file():
        parts.append("=== THIS COURSE ===\n\n" + style.read_text(encoding="utf-8"))

    parts.append("=== TRANSCRIPT ===\n\n" + transcript.read_text(encoding="utf-8"))
    parts.append("=== TASK ===\n\nConvert the transcript above into study notes, "
                 "following the rules in the first section and the course specifics "
                 "in the second. Apply the mis-transcription table so every term is "
                 "spelled consistently.")

    print(f"assembled from: {transcript.name}", file=sys.stderr)
    return "\n\n".join(parts)


def budget_report(prompt: str, model_name: str) -> str:
    """
    Whisper only accepts ~223 tokens of hotwords, and faster-whisper truncates the
    REST of the list silently. Hebrew tokenizes inefficiently, so a list that looks
    short can still overflow. Report it instead of losing terms quietly.
    """
    LIMIT = 223
    try:
        import huggingface_hub, tokenizers
        path = huggingface_hub.snapshot_download(model_name)
        tok = tokenizers.Tokenizer.from_file(os.path.join(path, "tokenizer.json"))
        n = len(tok.encode(" " + prompt.strip(), add_special_tokens=False).ids)
    except Exception:
        return ""                       # never let a diagnostic break a transcription
    if n <= LIMIT:
        return f"  ({n}/{LIMIT} tokens, all used)"
    # hotwords keeps the FRONT of the list, so find where the cut falls
    kept, total = 0, 0
    for term in prompt.split(", "):
        total += len(tok.encode(" " + term + ",", add_special_tokens=False).ids)
        if total > LIMIT:
            break
        kept += 1
    return (f"  ⚠ {n}/{LIMIT} tokens — only the first ~{kept} terms will be used; "
            f"put the most important ones first, or trim the list")


def to_wav(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-y",
         "-i", str(src), "-ar", "16000", "-ac", "1", str(dst)],
        check=True,
    )


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recordings", nargs="*", type=Path)
    ap.add_argument("--course", help="course number or name fragment")
    ap.add_argument("--vault", help="path to your notes folder (overrides ~/.lecture-vault)")
    ap.add_argument("--latest", action="store_true",
                    help="grab the newest recording in ~/Downloads instead of naming a file")
    ap.add_argument("--archive", action="store_true",
                    help="move the source recording to ~/lectures/archive once it has transcribed")
    ap.add_argument("--lang", default=None, help="force he/en instead of detecting")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--compute", default="int8",
                    help="int8 (fastest) | int8_float32 | float32 (most accurate)")
    ap.add_argument("--list", action="store_true", help="list courses and exit")
    ap.add_argument("--prompt", action="store_true",
                    help="print instructions + course style + newest transcript as one "
                         "block, to paste into ChatGPT / Gemini / any web chat")
    args = ap.parse_args()

    global VAULT
    VAULT = resolve_vault(args.vault)

    if args.list:
        for c in courses():
            terms = terminology(c)
            n = len(terms.split(", ")) if terms else 0
            print(f"  {c.name}   [{n} terms in _style.md]")
        return

    if args.prompt:
        if not args.course:
            sys.exit("--prompt needs --course, e.g.  lecture --prompt --course 71811")
        which = str(args.recordings[0]) if args.recordings else None
        print(build_prompt(find_course(args.course), which))
        return

    if args.latest:
        downloads = Path.home() / "Downloads"
        found = [f for f in downloads.iterdir()
                 if f.is_file() and f.suffix.lower() in MEDIA]
        if not found:
            sys.exit(f"No recordings found in {downloads}")
        newest = max(found, key=lambda f: f.stat().st_mtime)
        age = (time.time() - newest.stat().st_mtime) / 60
        size = newest.stat().st_size / 1048576
        print(f"latest : {newest.name}")
        print(f"         {size:,.0f} MB, downloaded {age:.0f} min ago")
        args.recordings = [newest]

    if not args.recordings:
        sys.exit("Give at least one recording, --latest, or --list to see courses.")
    if not args.course:
        sys.exit("--course is required so the transcript lands in the right folder.")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Install with: brew install ffmpeg")

    course = find_course(args.course)
    outdir = course / "transcripts"
    outdir.mkdir(parents=True, exist_ok=True)

    files = [f for f in args.recordings if f.is_file() and f.suffix.lower() in MEDIA]
    skipped = [f for f in args.recordings if f not in files]
    for s in skipped:
        print(f"skipping (not a readable media file): {s}", file=sys.stderr)
    if not files:
        sys.exit("Nothing to transcribe.")

    prompt = terminology(course)
    print(f"course : {course.name}")
    print(f"output : {outdir}")
    if prompt:
        n_terms = len(prompt.split(", "))
        fit = budget_report(prompt, args.model)
        print(f"terms  : {n_terms} from _style.md{fit}")
    else:
        print("terms  : none yet (add them under 'Terminology to expect' in _style.md)")

    from faster_whisper import WhisperModel

    print(f"loading {args.model} ({args.compute}) ...", flush=True)
    model = WhisperModel(args.model, device="cpu",
                         compute_type=args.compute, cpu_threads=0)

    for src in files:
        txt_path = outdir / f"{src.stem}.txt"
        srt_path = outdir / f"{src.stem}.srt"
        if txt_path.exists():
            print(f"\nskip (already transcribed): {txt_path.name}")
            continue

        print(f"\n{src.name}")
        started = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "audio.wav"
            try:
                to_wav(src, wav)
            except subprocess.CalledProcessError:
                print("  ffmpeg could not read this file - skipped", file=sys.stderr)
                continue

            segments, info = model.transcribe(
                str(wav),
                language=args.lang,               # None => detect
                # hotwords, NOT initial_prompt: initial_prompt only seeds the first
                # ~30s window, and with condition_on_previous_text=False it never
                # carries forward. hotwords is re-injected into every window.
                hotwords=prompt,
                vad_filter=True,                  # lecture halls have a lot of dead air
                beam_size=5,
                condition_on_previous_text=False, # stops runaway repetition on long audio
            )
            print(f"  language {info.language} ({info.language_probability:.2f})"
                  f"  ·  {info.duration/60:.1f} min of audio")

            lines, subs = [], []
            for i, seg in enumerate(segments, start=1):
                lines.append(seg.text.strip())
                subs.append(f"{i}\n{srt_time(seg.start)} --> {srt_time(seg.end)}\n"
                            f"{seg.text.strip()}\n")
                if i % 100 == 0:
                    done = seg.end / info.duration * 100
                    print(f"  ... {done:.0f}%  ({seg.end/60:.0f} min)", flush=True)

        header = (f"---\nsource: {src.name}\ncourse: {course.name}\n"
                  f"language: {info.language}\nduration_min: {info.duration/60:.1f}\n"
                  f"transcribed: {time.strftime('%Y-%m-%d %H:%M')}\n---\n\n")
        txt_path.write_text(header + "\n".join(lines), encoding="utf-8")
        srt_path.write_text("\n".join(subs), encoding="utf-8")

        mins = (time.time() - started) / 60
        rate = (info.duration / 60) / mins if mins else 0
        print(f"  wrote {txt_path.name} + {srt_path.name}"
              f"  ({mins:.1f} min, {rate:.1f}x realtime)")

        if args.archive:
            archive = Path.home() / "lectures" / "archive"
            archive.mkdir(parents=True, exist_ok=True)
            dest = archive / src.name
            n = 1
            while dest.exists():
                dest = archive / f"{src.stem} {n}{src.suffix}"
                n += 1
            try:
                shutil.move(str(src), str(dest))
                print(f"  moved source out of Downloads -> ~/lectures/archive/{dest.name}")
            except OSError as e:
                print(f"  could not archive the source: {e}", file=sys.stderr)

    print(f"\ndone - transcripts are in {outdir}")


if __name__ == "__main__":
    main()
