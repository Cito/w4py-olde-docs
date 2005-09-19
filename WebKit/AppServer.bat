@echo off

rem WebKit application server launch script for Windows.

rem You may give the following Python parameters in advance,
rem followed by the parameters passed on to ThreadedAppServer:
rem   -O with optimization (.pyo instead of .pyc)
rem   -u unbuffered output (useful for debugging)
set PY_OPTS=
:getopt
if "%1"=="-O" goto setopt
if "%1"=="-u" goto setopt
goto continue
:setopt
set PY_OPTS=%PY_OPTS% %1
shift
goto getopt
:continue

rem Make the directory where this script lives the current directory:
if exist $~dpn0 cd /d %~dp0

rem As long as the app server returns a 3, it wants to be restarted:
:restart
python%PY_OPTS% Launch.py ThreadedAppServer %1 %2 %3 %4 %5 %6 %7 %8 %9
if errorlevel 3 goto restart
