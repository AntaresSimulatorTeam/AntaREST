# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# We need to analyze all alembic files to be sure the migration phase works fine
migrations_dir = Path('alembic/versions')
migration_files = [str(f) for f in migrations_dir.iterdir() if f.is_file() and f.suffix == '.py']

binaries = [('./alembic.ini', './alembic.ini')]  + collect_dynamic_libs('tables')

antares_web_server_a = Analysis(['antarest/gui.py', 'alembic/env.py'] + migration_files,
             pathex=[],
             binaries=binaries,
             datas=[('./resources', './resources'), ('./alembic', './alembic')],
             hiddenimports=[
                 'cmath',
                 'antarest.dbmodel',
                 'plyer.platforms.win',
                 'plyer.platforms.win.notification',
                 'pythonjsonlogger.jsonlogger',
             ],
             hookspath=['extra-hooks'],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
antares_web_server_pyz = PYZ(antares_web_server_a.pure, antares_web_server_a.zipped_data,
             cipher=block_cipher)
antares_web_server_exe = EXE(antares_web_server_pyz,
          antares_web_server_a.scripts, 
          [],
          exclude_binaries=True,
          name='AntaresWebServer',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='resources/webapp/favicon.ico')


antares_tool_a = Analysis(['antarest/tools/cli.py'],
             pathex=[],
             binaries=[],
             datas=[('./resources', './resources')],
             hiddenimports=['cmath', 'sqlalchemy.sql.default_comparator', 'sqlalchemy.ext.baked'],
             hookspath=['extra-hooks'],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
antares_tool_pyz = PYZ(antares_tool_a.pure, antares_tool_a.zipped_data,
             cipher=block_cipher)
antares_tool_exe = EXE(antares_tool_pyz,
          antares_tool_a.scripts, 
          [],
          exclude_binaries=True,
          name='AntaresTool',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )


coll = COLLECT(antares_web_server_exe,
               antares_web_server_a.binaries,
               antares_web_server_a.zipfiles,
               antares_web_server_a.datas,
               antares_tool_exe,
               antares_tool_a.binaries,
               antares_tool_a.zipfiles,
               antares_tool_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='AntaresWeb')
