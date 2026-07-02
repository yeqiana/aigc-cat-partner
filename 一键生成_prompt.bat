@echo off
chcp 65001 >nul
python tools\generate_prompt.py --input examples\minimal_input.sample.json
pause
