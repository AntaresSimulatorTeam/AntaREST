from PyInstaller.utils.hooks import collect_submodules

# We need to import the zip files to create empty studies inside the Desktop app
hiddenimports = collect_submodules("antares.study.version")
