import contextlib
import multiprocessing
import platform
import time
import webbrowser
from multiprocessing import Process
from pathlib import Path

import requests
import uvicorn  # type: ignore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon

from antarest.core.utils.utils import get_local_path
from antarest.main import fastapi_app, parse_arguments

RESOURCE_PATH = get_local_path() / "resources"


def run_server(config_file: Path) -> None:
    app = fastapi_app(
        config_file,
        mount_front=True,
        auto_upgrade_db=True,
    )[0]
    # noinspection PyTypeChecker
    uvicorn.run(app, host="127.0.0.1", port=8080)


def open_app() -> None:
    webbrowser.open("http://localhost:8080")


def main() -> None:
    multiprocessing.freeze_support()
    arguments = parse_arguments()
    if platform.system() == "Windows":
        # noinspection PyPackageRequirements
        from win10toast import ToastNotifier  # type: ignore

        toaster = ToastNotifier()
        toaster.show_toast(
            "AntaresWebServer",
            "Antares Web Server started, you can manage the application within the systray app",
            icon_path=RESOURCE_PATH / "webapp" / "favicon.ico",
            threaded=True,
        )
    else:
        from plyer import notification  # type: ignore

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
    open_app_action = QAction("Open application")
    menu.addAction(open_app_action)
    open_app_action.triggered.connect(open_app)
    # To quit the app
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)
    # Adding options to the System Tray
    tray.setContextMenu(menu)
    app.processEvents()
    tray.setToolTip("AntaresWebServer")
    server = Process(
        target=run_server,
        args=(arguments.config_file,),
    )
    server.start()
    for _ in range(30, 0, -1):
        with contextlib.suppress(requests.ConnectionError):
            res = requests.get("http://localhost:8080")
            if res.status_code == 200:
                break
        time.sleep(1)
    app.exec_()
    server.kill()


if __name__ == "__main__":
    main()
