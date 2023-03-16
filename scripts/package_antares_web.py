#!/usr/bin/env python3

import os
import shutil
import urllib.request
from pathlib import Path

ANTARES_SOLVER_VERSION = "8.4"
ANTARES_SOLVER_FULL_VERSION = f"{ANTARES_SOLVER_VERSION}.1"
ANTARES_SOLVER_FULL_VERSION_INT = ANTARES_SOLVER_FULL_VERSION.replace(".", "")

if os.name == "nt":
    ANTARES_SOLVER_FOLDER_NAME = f"rte-antares-{ANTARES_SOLVER_FULL_VERSION}-installer-64bits"
    ANTARES_SOLVER_ZIPFILE_NAME = f"{ANTARES_SOLVER_FOLDER_NAME}.zip"
else:
    ANTARES_SOLVER_FOLDER_NAME = f"antares-{ANTARES_SOLVER_FULL_VERSION}-Ubuntu-20.04"
    ANTARES_SOLVER_ZIPFILE_NAME = f"{ANTARES_SOLVER_FOLDER_NAME}.tar.gz"

LINK = f"https://github.com/AntaresSimulatorTeam/Antares_Simulator/releases/download/v{ANTARES_SOLVER_FULL_VERSION}/{ANTARES_SOLVER_ZIPFILE_NAME}"
DESTINATION = Path("../dist/AntaresWeb/antares_solver")

print(f"Downloading AntaresSimulator from {LINK}")
urllib.request.urlretrieve(LINK, ANTARES_SOLVER_ZIPFILE_NAME)

print(f"Unzipping {ANTARES_SOLVER_ZIPFILE_NAME} and move Antares solver to {DESTINATION}")
if os.name == "nt":
    shutil.unpack_archive(ANTARES_SOLVER_ZIPFILE_NAME, ANTARES_SOLVER_FOLDER_NAME)
else:
    shutil.unpack_archive(ANTARES_SOLVER_ZIPFILE_NAME)

DESTINATION.mkdir(parents=True, exist_ok=True)

if os.name == "nt":
    shutil.move(f"{ANTARES_SOLVER_FOLDER_NAME}/bin/antares-{ANTARES_SOLVER_VERSION}-solver.exe", DESTINATION)
    shutil.move(f"{ANTARES_SOLVER_FOLDER_NAME}/bin/sirius_solver.dll", DESTINATION)
    shutil.move(f"{ANTARES_SOLVER_FOLDER_NAME}/bin/zlib1.dll", DESTINATION)
else:
    shutil.move(f"{ANTARES_SOLVER_FOLDER_NAME}/bin/antares-{ANTARES_SOLVER_VERSION}-solver", DESTINATION)
    shutil.move(f"{ANTARES_SOLVER_FOLDER_NAME}/bin/libsirius_solver.so", DESTINATION)

print("Copy basic configuration files")
shutil.copytree("../resources/deploy", "../dist", dirs_exist_ok=True)

if os.name == "nt":
    with open("../dist/config.yaml", "r+") as f:
        content = f.read().replace("700: path/to/700", f"{ANTARES_SOLVER_FULL_VERSION_INT}: ./AntaresWeb/antares_solver/antares-{ANTARES_SOLVER_VERSION}-solver.exe")
        f.seek(0)
        f.write(content)
else:
    with open("../dist/config.yaml", "r+") as f:
        content = f.read().replace("700: path/to/700", f"{ANTARES_SOLVER_FULL_VERSION_INT}: ./AntaresWeb/antares_solver/antares-{ANTARES_SOLVER_VERSION}-solver")
        f.seek(0)
        f.write(content)

print("Creating shortcuts")
if os.name == "nt":
    shutil.copy("../resources/AntaresWebServerShortcut.lnk", "../dist")
else:
    os.symlink("../dist/AntaresWeb/AntaresWebServer", "../dist/AntaresWebServer")

print("Unzipping example study")
os.chdir("../dist/examples/studies")
sh
