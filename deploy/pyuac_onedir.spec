a = Analysis([os.path.join(HOMEPATH, 'support', '_mountzlib.py'),
              os.path.join(HOMEPATH, 'support', 'useUnicode.py'),
              os.path.join('..', 'src', 'pyuac.py')],
              pathex=[os.path.join('..', 'src'), '.'])

a_cli = Analysis([os.path.join(HOMEPATH, 'support', '_mountzlib.py'),
              os.path.join(HOMEPATH, 'support', 'useUnicode.py'),
              os.path.join('..', 'src', 'pyuac_cli.py')],
              pathex=[os.path.join('..', 'src'), '.'])

pyz = PYZ(a.pure)
pyz_cli = PYZ(a_cli.pure)

if os.name == 'nt':
    pyuac_name = 'pyuac.exe'
    pyuac_cli_name = 'pyuac_cli.exe'
else:
    pyuac_name = 'pyuac'
    pyuac_cli_name = 'pyuac_cli'

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('buildpyuac_onedir', pyuac_name),
          debug=False,
          strip=False,
          upx=False,
          console=True )

exe_cli = EXE(pyz_cli,
          a_cli.scripts,
          exclude_binaries=1,
          name=os.path.join('buildpyuac_onedir', pyuac_cli_name),
          debug=False,
          strip=False,
          upx=False,
          console=True )

coll = COLLECT( exe, exe_cli,
               a.binaries + [('pyuac_auth.ui', os.path.join('..', 'src', 'pyuac_auth.ui'), 'DATA'),
                             ('pyuac_browse.ui', os.path.join('..', 'src', 'pyuac_browse.ui'), 'DATA'),
                             ('pyuac_edit.ui', os.path.join('..', 'src', 'pyuac_edit.ui'), 'DATA')
                             ('time_calculator.ui', os.path.join('..', 'src', 'time_calculator.ui'), 'DATA')],
               strip=False,
               upx=False,
               name='distpyuac_onedir')
