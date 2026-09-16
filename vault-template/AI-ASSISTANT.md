# Lecture notes vault

Transcripts and study notes, one folder per course. Lectures are in Hebrew with
English technical terms used inline.

## The pipeline

1. Download the lecture recording (Panopto, Moodle, wherever it lives)
2. `lecture --latest --course <number>`
   - takes .mp4/.mov/.m4a directly; ffmpeg extracts the audio
   - writes `<course>/transcripts/<name>.txt` and `.srt`
   - runs offline on the CPU at roughly 4x realtime
3. Hand the transcript to an AI assistant. Two ways:

   **If it can read local files** (Claude Code, Gemini CLI, Cursor, Copilot in an
   editor): open this folder and say *"convert the new <course> lecture"*.

   **If it is a web chat** (ChatGPT, Gemini, Claude.ai): run
   `lecture --prompt --course <number>` — it prints the instructions, the course
   vocabulary and the transcript as one block, ready to paste.

## When asked to convert a lecture

(This section is for the assistant, whichever one you use.)

Read these in order before writing anything:

1. **`_instructions.md`** — the user's own rules for what notes should look like.
   These override any default. If it is still the blank template, ask how they
   want notes structured before producing a full set.
2. **`<course>/_style.md`** — what is specific to that course: vocabulary, the
   mis-transcription table, and how that subject wants to be organised.
3. The transcript in `<course>/transcripts/`.
4. The running note, so the new lecture connects rather than repeats.

Then produce two things: the lecture note in `<course>/lectures/`, and an append
to the running note linking it.

## Things that go wrong

- **Whisper mangles Hebrew technical terms inconsistently.** The same term can
  appear three ways in one transcript. Normalise every variant to one spelling
  using the mis-transcription table, or a semester of notes becomes unsearchable.
- **Follow the lecturer's order**, not a textbook's, unless `_instructions.md`
  says otherwise. The notes should run alongside the recording.
- **Flag contradictions, do not silently fix them.** If a transcript says
  something that contradicts itself, mark it and say to check the slide.
- **Never write a note into the wrong course folder.** `--course` is required
  for exactly this reason.

## Growing the vocabulary

When a transcript produces a new mangling, add it to that course's `_style.md`
twice: the correct form to the terminology list, and the wrong-to-right pair to
the mis-transcription table. The terminology list feeds Whisper (which uses only
the first ~223 tokens, so put the most important terms first) and is also used at
write time to keep spelling consistent.
