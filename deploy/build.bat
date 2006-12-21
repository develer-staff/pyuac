rmdir /S /Q distpyuac_onedir
del warndistpyuac_onedir.txt
del pyuac.exe
del pyuac_cli.exe

python pyinstaller/configure.py
python pyinstaller/Build.py pyuac_onedir.spec

rem "c:\Programmi\Inno Setup 5\ISCC.exe" pyuac.iss
