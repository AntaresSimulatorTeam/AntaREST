import multiprocessing
import sys
import time
from multiprocessing import Process
from pathlib import Path

import requests

from antarest import __version__

import uvicorn
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from antarest.core.utils.utils import get_local_path
from antarest.main import fastapi_app, get_arguments

RESOURCE_PATH = get_local_path() / "resources"


def run_server(config_file: Path) -> None:
    app, _ = fastapi_app(
        config_file,
        mount_front=True,
        auto_upgrade_db=True,
    )
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    config_file, display_version, no_front, auto_upgrade_db = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    # Adding an icon
    icon = QIcon("icon.png")

    # Adding item on the menu bar
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    # Creating the options
    menu = QMenu()
    option1 = QAction("Geeks for Geeks")
    option2 = QAction("GFG")
    menu.addAction(option1)
    menu.addAction(option2)

    # To quit the app
    quit = QAction("Quit")
    quit.triggered.connect(app.quit)
    menu.addAction(quit)

    # Adding options to the System Tray
    tray.setContextMenu(menu)

    server = Process(
        target=run_server,
        args=(config_file,),
    )
    server.start()

    countdown = 30
    server_started = False
    while countdown > 0:
        try:
            res = requests.get("http://localhost:8080")
            if res.status_code == 200:
                server_started = True
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
        countdown -= 1

    app.exec_()

    server.kill()
