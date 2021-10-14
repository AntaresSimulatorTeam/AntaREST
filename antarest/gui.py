from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QSplashScreen,
    QLabel,
    QSizePolicy,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

from antarest import __version__

try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin

    myappid = f'com.rte-france.antares.web.{__version__.replace(".","_")}'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


import sys
import time
import multiprocessing
from pathlib import Path

import requests
import uvicorn

from multiprocessing import Process

from antarest.core.utils.utils import get_local_path
from antarest.main import fastapi_app, get_arguments

RESOURCE_PATH = get_local_path() / "resources"


class ErrorWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(ErrorWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(
            QIcon(str(RESOURCE_PATH / "webapp" / "favicon.ico"))
        )
        self.setMinimumSize(400, 200)
        self.label = QLabel("Failed to start embeded server!")
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()
        )
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(
            QIcon(str(RESOURCE_PATH / "webapp" / "favicon.ico"))
        )
        self.setMinimumSize(1280, 720)
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://localhost:8080"))
        self.setCentralWidget(self.browser)

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()
        )
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


def run_server(config_file: Path):
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

    app = QApplication(sys.argv)
    splash_pix = QPixmap(str(RESOURCE_PATH / "splash_loading.png"))
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()
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

    if not server_started:
        window = ErrorWindow()
    else:
        window = MainWindow()

    window.center()
    window.show()
    splash.close()

    app.exec_()

    server.kill()
