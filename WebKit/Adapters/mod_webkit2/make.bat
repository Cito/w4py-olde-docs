@echo off

rem Batch file for generating the mod_webkit Apache 2.2 DSO module.
rem You can either use the full Microsoft Visual Studio 2008
rem or the free Microsoft Visual C++ 2008 Express Edition
rem (download at http://www.microsoft.com/express/download/).
rem Creating a 64bit module with the Express Edition also requires
rem the Windows SDK and some tweaking of the configuration.

rem Set environment variables

rem VC will be under %ProgramFiles(x86)% on a 64bit system
set VC=%ProgramFiles%\Microsoft Visual Studio 9.0\VC
set APACHE=%ProgramFiles%\Apache Software Foundation\Apache2.2

rem You can use x86_amd64 or amd64 to build a 64bit module
set BUILD=x86

call "%VC%\vcvarsall" %BUILD%

set PATH=%Apache%\bin;%PATH%
set INCLUDE=%Apache%\include;%INCLUDE%
set LIB=%Apache%\lib;%LIB%

rem Compile and link mod_webkit

rem You should add /D WIN64 for a 64bit module
cl /W3 /O2 /EHsc /LD /MT ^
    /D WIN32 /D _WINDOWS /D _MBCS /D _USRDLL ^
    /D MOD_WEBKIT_EXPORTS /D NDEBUG ^
    mod_webkit.c marshal.c ^
    /link libhttpd.lib libapr-1.lib libaprutil-1.lib ws2_32.lib

rem Remove all intermediate results

del /Q *.exp *.ilk *.lib *.obj *.pdb

rem Install mod_webkit

copy mod_webkit.dll "%Apache%\modules\mod_webkit.so"

rem Wait for keypress before leaving

echo.
pause
