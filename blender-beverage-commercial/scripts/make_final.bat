@echo off
REM ---------------------------------------------------------------------
REM  MR LEMON - full pipeline: bake splash, render sequence, encode MP4.
REM  Runs in a SEPARATE headless Blender so your interactive session is
REM  never blocked and cannot be crashed by it.
REM
REM  SAFE TO RE-RUN: the render is resumable (Overwrite off + Placeholders
REM  on), so a second run continues where a crash stopped.
REM ---------------------------------------------------------------------
setlocal

set "BLEND=C:\Users\Public\New.blend"
set "OUT=C:\Users\Public\mrlemon_render"
set "HERE=%~dp0"

set "BLENDER="
where blender.exe >nul 2>&1 && set "BLENDER=blender.exe"
if not defined BLENDER (
  for /d %%V in ("C:\Program Files\Blender Foundation\Blender *") do (
    if exist "%%V\blender.exe" set "BLENDER=%%V\blender.exe"
  )
)
if not defined BLENDER (
  echo Could not find blender.exe. Edit this file and set BLENDER manually.
  pause & exit /b 1
)

echo Blender : %BLENDER%
echo Blend   : %BLEND%
echo Output  : %OUT%
echo.
echo Close the interactive Blender before continuing.
echo This will run for HOURS. It is resumable - safe to stop and re-run.
pause

echo.
echo === STAGE 1+2 : bake then render ===
"%BLENDER%" -b "%BLEND%" -P "%HERE%make_final_headless.py"

echo.
echo === STAGE 3 : encode ===
"%BLENDER%" -b -P "%HERE%encode_sequence_headless.py" -- --dir "%OUT%" --preset all

echo.
echo Pipeline finished. MP4s are in %OUT%
pause
