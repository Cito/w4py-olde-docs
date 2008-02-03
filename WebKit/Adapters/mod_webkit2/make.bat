@echo off

rem Batch file for generating the mod_webkit Apache 2.2 DSO module
rem using the free Microsoft Visual C++ 2008 Express Edition
rem (download at http://www.microsoft.com/express/download/).

rem Set environment variables

set VC=%ProgramFiles%\Microsoft Visual Studio 9.0\VC
set APACHE=%ProgramFiles%\Apache Software Foundation\Apache2.2

call "%VC%\vcvarsall"

Set PATH=%Apache%\bin;%PATH%
Set INCLUDE=%Apache%\include;%INCLUDE%
Set LIB=%Apache%\lib;%LIB%

rem Compile and link mod_webkit

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
