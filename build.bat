@ECHO OFF
echo "python x86 must install at C:\Python35-32"
echo "python x64 must install at C:\Python35"
echo "require python x86/x64 module PyInstaller, PyQt5, lxml"
pause

echo "Build x64"
del /Q /S build
del dist\btReload_x64.exe 
C:\Python35\python.exe -m PyInstaller btReload.spec
ren dist\btReload.exe btReload_x64.exe

echo "Build x86"
del /Q /S build
del dist\btReload.exe 
C:\Python35-32\python.exe -m PyInstaller btReload.spec