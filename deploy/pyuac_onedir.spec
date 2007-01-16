a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'),
              os.path.join(HOMEPATH,'support\\useUnicode.py'),
              '..\\src\\pyuac.py'],
              pathex=['..\\src\\', '.'])

a_cli = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'),
              os.path.join(HOMEPATH,'support\\useUnicode.py'),
              '..\\src\\pyuac_cli.py'],
              pathex=['..\\src\\', '.'])

pyz = PYZ(a.pure)
pyz_cli = PYZ(a_cli.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name='buildpyuac_onedir/pyuac.exe',
          debug=False,
          strip=False,
          upx=False,
          console=True )

exe_cli = EXE(pyz_cli,
          a_cli.scripts,
          exclude_binaries=1,
          name='buildpyuac_onedir/pyuac_cli.exe',
          debug=False,
          strip=False,
          upx=False,
          console=True )

coll = COLLECT( exe, exe_cli,
               a.binaries + [('pyuac_auth.ui', '..\\src\\pyuac_auth.ui', 'DATA'),
                             ('pyuac_browse.ui', '..\\src\\pyuac_browse.ui', 'DATA'),
                             ('pyuac_edit.ui', '..\\src\\pyuac_edit.ui', 'DATA')],
               strip=False,
               upx=False,
               name='distpyuac_onedir')
