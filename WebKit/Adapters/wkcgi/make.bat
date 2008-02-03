@echo off

rem Batch file for generating the wkcgi.exe CGI executable
rem using the free Microsoft Visual C++ 2008 Express Edition
rem (download at http://www.microsoft.com/express/download/).

rem Set environment variables

set VC=%ProgramFiles%\Microsoft Visual Studio 9.0\VC
set APACHE=%ProgramFiles%\Apache Software Foundation\Apache2.2

call "%VC%\vcvarsall"

rem Compile and link wkcgi

cl /W3 /O2 /EHsc /wd4996 ^
    /D WIN32 /D _CONSOLE /D _MBCS  ^
    wkcgi.c ^
    ..\common\wkcommon.c ..\common\marshal.c ^
    ..\common\environ.c ..\common\parsecfg.c ^
    /link wsock32.lib /subsystem:console


rem Remove all intermediate results

del /Q *.exp *.ilk *.lib *.obj *.pdb

rem Wait for keypress before leaving

echo.
pause
