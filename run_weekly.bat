@echo off
chcp 65001 >nul
echo ============================================
echo  Weekly Agent
echo  %date% %time%
echo ============================================

set CLAUDE_CMD="C:\Users\danny\AppData\Roaming\npm\claude.cmd"
set BASE_DIR=C:\Users\danny\Desktop\Claude Code\Weekly Agent

cd /d "%BASE_DIR%"
if exist output\* del /q output\*

call %CLAUDE_CMD% -p --dangerously-skip-permissions "CLAUDE.md의 주간 워크플로우를 Step 1부터 Step 6까지 순서대로 전부 실행해줘. 모든 단계를 자동으로 진행하고 중간에 멈추지 마. 오류 발생 시 텔레그램으로 알림 보내고 다음 단계로 진행해."

if %errorlevel% neq 0 (
    echo [WARNING] Weekly Agent exited with error code %errorlevel%
) else (
    echo [OK] Weekly Agent completed successfully.
)

echo.
echo ============================================
echo  Weekly Agent finished at %time%
echo ============================================
pause
