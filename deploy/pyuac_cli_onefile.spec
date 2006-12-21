a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'),
              os.path.join(HOMEPATH,'support\\useUnicode.py'),
              '..\\src\\pyuac_cli.py'],
              pathex=['.'])
pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts + [('u', '', 'OPTION')],
          a.binaries,
          name='pyuac_cli.exe',
          debug=0,
          strip=0,
          upx=0,
          console=1)
