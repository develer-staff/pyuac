rmdir /S /Q buildpyuac_onefile
del warnpyuac_onefile.txt

python pyinstaller/configure.py
python pyinstaller/Build.py pyuac_onefile.spec

rem "c:\Programmi\Inno Setup 5\ISCC.exe" pyuac.iss
