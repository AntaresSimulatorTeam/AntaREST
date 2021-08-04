from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [
    "sqlalchemy.sql.default_comparator",
    "jinja2",
] + collect_submodules("uvicorn")
