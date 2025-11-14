@echo off
REM Activate your virtual environment (if any)
call E:\pro-bill-backend\ven\Scripts\activate.bat

REM Run your Python email sending script

python "E:\pro-bill-backend\routes\run_email.py"

REM Optional: keep window open to see output
pause
