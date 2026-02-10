@echo off
echo Starting AWB Batch Processor...
python src/main.py -f batch_input.txt --consolidate
echo.
echo Pipeline finished.
pause
