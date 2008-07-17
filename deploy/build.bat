rmdir /S /Q distpyuac_onedir
rmdir /S /Q buildpyuac_onedir
del warnpyuac_onedir.txt

python pyinstaller/configure.py
python pyinstaller/Build.py pyuac_onedir.spec

"c:\Programmi\Inno Setup 5\ISCC.exe" pyuac.iss
