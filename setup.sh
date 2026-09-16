#!/bin/bash
# Setup for the Hebrew lecture transcription pipeline.
# Safe to run more than once - it skips anything already installed.
#
#   bash setup.sh
#
set -u

BOLD=$'\033[1m'; DIM=$'\033[2m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; OFF=$'\033[0m'
say()  { printf "%s\n" "$*"; }
ok()   { printf "  ${GREEN}OK${OFF}   %s\n" "$*"; }
skip() { printf "  ${DIM}--${OFF}   %s\n" "$*"; }
work() { printf "  ${YELLOW}..${OFF}   %s\n" "$*"; }
bad()  { printf "  ${RED}!!${OFF}   %s\n" "$*"; }

say ""
say "${BOLD}Hebrew lecture transcription - setup${OFF}"
say "${DIM}Transcribes recorded lectures locally. Nothing is uploaded anywhere.${OFF}"
say ""

# ---------------------------------------------------------------- 1. platform
if [ "$(uname)" != "Darwin" ]; then
  bad "This script is written for macOS. On Linux install ffmpeg and miniforge"
  bad "yourself, then re-run from step 3."
  exit 1
fi
ok "macOS $(sw_vers -productVersion), $(uname -m)"

# ---------------------------------------------------------------- 2. homebrew
if command -v brew >/dev/null 2>&1; then
  ok "Homebrew"
else
  bad "Homebrew is missing. Install it first:"
  say ""
  say '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  say ""
  exit 1
fi

# ---------------------------------------------------------------- 3. ffmpeg
if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg"
else
  work "installing ffmpeg (pulls the audio out of lecture videos)"
  brew install ffmpeg || { bad "ffmpeg install failed"; exit 1; }
  ok "ffmpeg"
fi

# ---------------------------------------------------------------- 4. conda
CONDA=""
for c in "$HOME/miniforge3/bin/conda" \
         "/opt/homebrew/Caskroom/miniforge/base/bin/conda" \
         "$(command -v conda 2>/dev/null)"; do
  [ -x "$c" ] && { CONDA="$c"; break; }
done

if [ -n "$CONDA" ]; then
  ok "conda  ${DIM}($CONDA)${OFF}"
else
  work "installing miniforge (a small Python distribution)"
  brew install --cask miniforge || { bad "miniforge install failed"; exit 1; }
  CONDA="/opt/homebrew/Caskroom/miniforge/base/bin/conda"
  [ -x "$CONDA" ] || { bad "cannot find conda after install"; exit 1; }
  ok "conda"
fi

# ---------------------------------------------------------------- 5. the env
if "$CONDA" env list | grep -qE '^transcribe\s'; then
  skip "conda env 'transcribe' already exists"
else
  work "creating the 'transcribe' environment (about a minute)"
  "$CONDA" create -n transcribe -y python=3.11 >/dev/null || { bad "env create failed"; exit 1; }
  ok "conda env 'transcribe'"
fi

work "installing faster-whisper"
"$CONDA" run -n transcribe pip install -q --upgrade faster-whisper >/dev/null 2>&1 \
  || { bad "faster-whisper install failed"; exit 1; }
ok "faster-whisper"

# ---------------------------------------------------------------- 6. the notes folder
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HOME/.lecture-vault"

if [ -f "$CONFIG" ] && [ -d "$(cat "$CONFIG")" ]; then
  VAULT="$(cat "$CONFIG")"
  skip "notes folder already set: $VAULT"
else
  say ""
  say "${BOLD}Where should your notes live?${OFF}"
  say "${DIM}A folder for transcripts and notes. If you use Obsidian, open this folder"
  say "as a vault afterwards. Keep it OFF Google Drive - Drive's streaming files"
  say "confuse Obsidian.${OFF}"
  say ""
  printf "  path [%s]: " "$HOME/Desktop/Lectures"
  read -r VAULT
  VAULT="${VAULT:-$HOME/Desktop/Lectures}"
  VAULT="${VAULT/#\~/$HOME}"
  mkdir -p "$VAULT" || { bad "could not create $VAULT"; exit 1; }
  printf "%s" "$VAULT" > "$CONFIG"
  ok "notes folder: $VAULT"
fi

# ---------------------------------------------------------------- 7. templates
if [ -f "$VAULT/_instructions.md" ]; then
  skip "_instructions.md already there (not overwriting)"
else
  cp "$SCRIPT_DIR/vault-template/_instructions.md" "$VAULT/" 2>/dev/null && ok "_instructions.md (fill this in - it is yours to write)"
  cp "$SCRIPT_DIR/vault-template/_instructions.EXAMPLE.md" "$VAULT/" 2>/dev/null && ok "_instructions.EXAMPLE.md (a worked example to read first)"
fi
if [ -f "$VAULT/CLAUDE.md" ]; then
  skip "CLAUDE.md already there (not overwriting)"
else
  cp "$SCRIPT_DIR/vault-template/CLAUDE.md" "$VAULT/" 2>/dev/null && ok "CLAUDE.md"
fi

# ---------------------------------------------------------------- 8. the command
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/lecture" <<EOF
#!/bin/sh
exec "$CONDA" run -n transcribe --no-capture-output python "$SCRIPT_DIR/transcribe.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/lecture"
ok "the 'lecture' command"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *)
    say ""
    bad "~/.local/bin is not on your PATH. Add it:"
    say ""
    say "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
    say ""
    ;;
esac

# ---------------------------------------------------------------- 9. the model
say ""
printf "Download the Hebrew speech model now? About 1.5 GB, one time. [Y/n] "
read -r GETMODEL
case "${GETMODEL:-y}" in
  [Nn]*) skip "skipped - it will download on your first transcription" ;;
  *)
    work "downloading (this takes a few minutes)"
    "$CONDA" run -n transcribe python -c "
import huggingface_hub
huggingface_hub.snapshot_download('ivrit-ai/whisper-large-v3-turbo-ct2')
" >/dev/null 2>&1 && ok "model downloaded" || bad "download failed - it will retry on first use"
    ;;
esac

# ---------------------------------------------------------------- done
say ""
say "${BOLD}${GREEN}Done.${OFF}"
say ""
say "  1. Make a folder per course inside:  ${BOLD}$VAULT${OFF}"
say "     Name it however you like, e.g.  71811 - Immunology"
say ""
say "  2. Transcribe a lecture:"
say "     ${BOLD}lecture --latest --course 71811${OFF}      ${DIM}(newest file in ~/Downloads)${OFF}"
say "     ${BOLD}lecture ~/Downloads/talk.mp4 --course 71811${OFF}"
say ""
say "  3. See your courses:   ${BOLD}lecture --list${OFF}"
say ""
say "${DIM}Course vocabulary packs for some HUJI courses are in course-packs/ -"
say "copy the relevant one into your course folder as _style.md.${OFF}"
say ""
