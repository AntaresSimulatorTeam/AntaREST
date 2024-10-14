# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

# We need to analyze all alembic files to be sure the migration phase works fine:
# alembic loads version files by their path, so we need to add them as "data" to the package,
# but all the dependencies they use need to be included also, wo we need to perform a
# dedicated analyse for this.
versions_dir = Path('alembic/versions')
versions_files = [str(f) for f in versions_dir.iterdir() if f.is_file() and f.suffix == '.py']
alembic_analysis = Analysis(["alembic/env.py"] + versions_files)

antares_web_server_a = Analysis(['antarest/gui.py'],
             pathex=[],
             binaries=[],
             datas=[('./resources', './resources'), ('./alembic', './alembic'), ('./alembic.ini', './')],
             hiddenimports=[
                 'cmath',
                 'antarest.dbmodel',
                 'plyer.platforms.win',
                 'plyer.platforms.win.notification',
                 'pythonjsonlogger.jsonlogger',
                 'tables',
             ],
             hookspath=['extra-hooks'],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

all_python = antares_web_server_a.pure + alembic_analysis.pure
all_zipped_data = antares_web_server_a.zipped_data + alembic_analysis.zipped_data

antares_web_server_pyz = PYZ(all_python, all_zipped_data,
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
