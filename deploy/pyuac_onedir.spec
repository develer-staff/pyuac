a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'),
              os.path.join(HOMEPATH,'support\\useUnicode.py'),
              '..\\src\\pyuac.py'],
             pathex=['..\\src', '.'])

a_cli = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'),
                  os.path.join(HOMEPATH,'support\\useUnicode.py'),
                  '..\\src\\pyuac_cli.py'],
                  pathex=['..\\src', '.'])

pyz = PYZ(a.pure)
pyz_cli = PYZ(a_cli.pure)

exe = EXE(pyz,
          a.scripts + [('u', '', 'OPTION')],
          exclude_binaries=1,
          name='pyuac.exe',
          debug=1,
          strip=0,
          upx=0,
          console=1 )

exe_cli = EXE(pyz_cli,
              a_cli.scripts + [('u', '', 'OPTION')],
              exclude_binaries=1,
              name='pyuac_cli.exe',
              debug=1,
              strip=0,
              upx=0,
              console=1 )

coll = COLLECT(exe,
               exe_cli,
               a.binaries + [('pyuac_auth.ui', '..\\src\\pyuac_auth.ui', 'DATA'),
                             ('pyuac_browse.ui', '..\\src\\pyuac_browse.ui', 'DATA'),
                             ('pyuac_edit.ui', '..\\src\\pyuac_edit.ui', 'DATA')],
               strip=0,
               upx=0,
               name='distpyuac_onedir')
