# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import contextlib
import multiprocessing
import platform
import time
import webbrowser
from dataclasses import dataclass
from multiprocessing import Process
from pathlib import Path
from threading import Thread
from typing import Tuple

import httpx
import uvicorn
from PyQt5.QtGui import QIcon, QCursor
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


def start_server(config_file: Path) -> Process:
    server = multiprocessing.Process(
        target=run_server,
        args=(config_file,),
    )
    server.start()
    return server


def open_app() -> None:
    webbrowser.open("http://localhost:8080")


@dataclass(frozen=True)
class AntaresSystrayApp:
    """
    Used to keep ownership of root Qt objects.
    QMenu can only be owned by QWidgets, but we don't have one.
    """
    app: QApplication
    menu: QMenu


def create_systray_app() -> AntaresSystrayApp:
    """
    Creates the small application that allows to open
    the browser or shutdown the server.
    """
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    # Adding an icon
    icon = QIcon(str(RESOURCE_PATH / "webapp" / "logo16.png"))
    # Adding item on the menu bar
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("AntaresWebServer")

    # Creating the options
    menu = QMenu()
    open_app_action = menu.addAction("Open application")
    open_app_action.triggered.connect(open_app)
    # To quit the app
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(app.quit)

    # Adding options to the System Tray
    def handle_action(reason: int) -> None:
        """
        - shows context menu also on left click
        - open browser on double click
        """
        if reason == QSystemTrayIcon.Trigger:
            tray.contextMenu().popup(QCursor.pos())
        if reason == QSystemTrayIcon.DoubleClick:
            open_app()
    tray.setContextMenu(menu)
    tray.activated.connect(handle_action)

    tray.setVisible(True)

    return AntaresSystrayApp(app, menu)


def monitor_server_process(server, app) -> None:
    """
    Quits the application when server process ends.
    """
    server.join()
    app.quit()


def setup_exit_application_on_server_end(server: Process, app: QApplication) -> None:
    Thread(target=monitor_server_process, args=(server, app)).start()


def wait_for_server_start() -> None:
    for _ in range(30, 0, -1):
        with contextlib.suppress(httpx.ConnectError):
            res = httpx.get("http://localhost:8080")
            if res.status_code == 200:
                break
        time.sleep(1)


def notification_popup(message: str) -> None:
    if platform.system() == "Windows":
        # noinspection PyPackageRequirements
        from win10toast import ToastNotifier  # type: ignore

        toaster = ToastNotifier()
        toaster.show_toast(
            "AntaresWebServer",
            message,
            icon_path=RESOURCE_PATH / "webapp" / "favicon.ico",
            threaded=True,
        )
    else:
        from plyer import notification  # type: ignore

        notification.notify(
            title="AntaresWebServer",
            message=message,
            app_name="AntaresWebServer",
            app_icon=str(RESOURCE_PATH / "webapp" / "favicon.ico"),
            timeout=600,
        )


def main() -> None:
    multiprocessing.freeze_support()

    arguments = parse_arguments()
    notification_popup("Antares Web Server starting...")
    systray_app = create_systray_app()
    server = start_server(arguments.config_file)
    setup_exit_application_on_server_end(server, systray_app.app)
    wait_for_server_start()
    notification_popup("Antares Web Server started, you can manage the application within the systray app")
    systray_app.app.exec_()
    server.kill()


if __name__ == "__main__":
    main()
