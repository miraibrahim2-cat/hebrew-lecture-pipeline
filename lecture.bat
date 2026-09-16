@echo off
REM Windows wrapper for the transcriber.
REM Run from a Miniforge Prompt, after: conda activate transcribe
REM
REM   lecture.bat --latest --course 71811
REM   lecture.bat --list
REM
REM If you get "python is not recognized", you are in a plain CMD window.
REM Open "Miniforge Prompt" from the Start menu instead.

python "%~dp0transcribe.py" %*
