@echo off
taskkill /IM NutriCoach.exe /F >nul 2>&1
timeout /t 2 >nul
copy /Y "C:\Users\Siviglino\Desktop\NutriCoach\dist\NutriCoach.exe" "C:\Program Files\NutriCoach\NutriCoach.exe" >nul
echo COPIED
