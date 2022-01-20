import multiprocessing
import sys
import time
import webbrowser
from multiprocessing import Process
from pathlib import Path

import requests
from plyer import notification  # type: ignore

from antarest import __version__

import uvicorn  # type: ignore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction

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


def open_app() -> None:
    webbrowser.open("http://localhost:8080")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    (
        config_file,
        display_version,
        no_front,
        auto_upgrade_db,
        module,
    ) = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()

    notification.notify(
        title="AntaresWebServer",
        message="Antares Web Server started, you can manage the application within the systray app",
        app_name="AntaresWebServer",
        app_icon=RESOURCE_PATH / "webapp" / "favicon.ico",
        timeout=600,
    )

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    # Adding an icon
    icon = QIcon(str(RESOURCE_PATH / "webapp" / "logo16.png"))

    # Adding item on the menu bar
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    # Creating the options
    menu = QMenu()
    openapp = QAction("Open application")
    menu.addAction(openapp)
    openapp.triggered.connect(open_app)  # type: ignore

    # To quit the app
    quit = QAction("Quit")
    quit.triggered.connect(app.quit)  # type: ignore
    menu.addAction(quit)

    # Adding options to the System Tray
    tray.setContextMenu(menu)
    app.processEvents()  # type: ignore

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
