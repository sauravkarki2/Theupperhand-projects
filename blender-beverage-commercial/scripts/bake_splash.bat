@echo off
REM ---------------------------------------------------------------------
REM  Headless splash bake. Double-click to run.
REM  Bakes in a SEPARATE Blender process so your interactive session is
REM  never blocked and cannot be crashed by the bake.
REM ---------------------------------------------------------------------
setlocal

set "BLEND=C:\Users\Public\New.blend"
set "SCRIPT=%~dp0bake_splash_headless.py"

REM Locate blender.exe: PATH first, then the usual install roots.
set "BLENDER="
where blender.exe >nul 2>&1 && set "BLENDER=blender.exe"

if not defined BLENDER (
  for /d %%V in ("C:\Program Files\Blender Foundation\Blender *") do (
    if exist "%%V\blender.exe" set "BLENDER=%%V\blender.exe"
  )
)
if not defined BLENDER (
  for /d %%V in ("%ProgramFiles%\Blender Foundation\Blender *") do (
    if exist "%%V\blender.exe" set "BLENDER=%%V\blender.exe"
  )
)

if not defined BLENDER (
  echo Could not find blender.exe.
  echo Edit this file and set BLENDER to its full path.
  pause
  exit /b 1
)

echo Using Blender: %BLENDER%
echo Blend file   : %BLEND%
echo.
echo Close the interactive Blender first if it has this file open.
pause

"%BLENDER%" -b "%BLEND%" -P "%SCRIPT%" -- --free

echo.
echo Bake finished. Reopen the .blend to pick up the cache.
pause
