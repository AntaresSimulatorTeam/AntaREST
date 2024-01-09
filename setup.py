from pathlib import Path

from setuptools import setup, find_packages

excluded_dirs = {"alembic", "conf", "docs", "examples", "resources", "scripts", "tests", "venv", "webapp"}

setup(
    name="AntaREST",
    version="2.16.2",
    description="Antares Server",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="RTE, Antares Web Team",
    author_email="andrea.sgattoni@rte-france.com",
    url="https://github.com/AntaresSimulatorTeam/api-iso-antares",
    packages=find_packages(exclude=excluded_dirs),
    license="Apache Software License",
    platforms=[
        "linux-x86_64",
        "macosx-10.14-x86_64",
        "macosx-10.15-x86_64",
        "macosx-11-x86_64",
        "macosx-12-x86_64",
        "macosx-13-x86_64",
        "win-amd64",
    ],
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: Apache License :: 2.0",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
