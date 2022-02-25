from PyInstaller.utils.hooks import collect_submodules
# Pandas keeps Python extensions loaded with dynamic imports here.
hiddenimports = collect_submodules('pandas._libs')
