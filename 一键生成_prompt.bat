@echo off
chcp 65001 >nul
python tools\generate_prompt.py --input examples\generic_suspense_series.sample.json
pause
