@echo off
chcp 65001 >nul
cd /d %~dp0
python tools\generate_batch_plan.py --input examples\batch_plan.sample.json
pause
