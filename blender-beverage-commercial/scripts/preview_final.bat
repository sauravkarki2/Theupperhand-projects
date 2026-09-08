@echo off
REM  Fast confidence pass: bake + render at 50%% / 128 samples, no motion blur.
REM  Use this FIRST to check the whole shot before committing to the long run.
setlocal
set "BLEND=C:\Users\Public\New.blend"
set "HERE=%~dp0"
set "BLENDER="
where blender.exe >nul 2>&1 && set "BLENDER=blender.exe"
if not defined BLENDER (
  for /d %%V in ("C:\Program Files\Blender Foundation\Blender *") do (
    if exist "%%V\blender.exe" set "BLENDER=%%V\blender.exe"
  )
)
if not defined BLENDER ( echo Could not find blender.exe. & pause & exit /b 1 )
"%BLENDER%" -b "%BLEND%" -P "%HERE%make_final_headless.py" -- --preview
pause
