from typing import Any

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QSplashScreen,
    QLabel,
    QSizePolicy,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem

from antarest import __version__

try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin  # type: ignore

    myappid = f'com.rte-france.antares.web.{__version__.replace(".","_")}'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


import sys
import time
import multiprocessing
from pathlib import Path

import requests
import uvicorn  # type: ignore

from multiprocessing import Process

from antarest.core.utils.utils import get_local_path
from antarest.main import fastapi_app, get_arguments

RESOURCE_PATH = get_local_path() / "resources"


class ErrorWindow(QMainWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(ErrorWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(
            QIcon(str(RESOURCE_PATH / "webapp" / "favicon.ico"))
        )
        self.setMinimumSize(400, 200)
        self.label = QLabel("Failed to start embeded server!")
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)

    def center(self) -> None:
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()  # type: ignore
        )
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())


class MainWindow(QMainWindow):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(
            QIcon(str(RESOURCE_PATH / "webapp" / "favicon.ico"))
        )
        self.setMinimumSize(1280, 720)
        self.browser = QWebEngineView()
        self.browser.page().profile().downloadRequested.connect(  # type: ignore
            self.on_downloadRequested
        )
        self.browser.setUrl(QUrl("http://localhost:8080"))
        self.setCentralWidget(self.browser)

    @QtCore.pyqtSlot("QWebEngineDownloadItem*")
    def on_downloadRequested(self, download: QWebEngineDownloadItem) -> None:
        old_path = download.url().path()  # download.path()
        suffix = download.mimeType().split("/")[-1]
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save File", f"{old_path}.{suffix}"
        )
        if path:
            download.setPath(path)
            download.accept()

    def center(self) -> None:
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()  # type: ignore
        )
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())


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

    app = QApplication(sys.argv)
    splash_pix = QPixmap(str(RESOURCE_PATH / "splash_loading.png"))
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
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

    window: QMainWindow
    if not server_started:
        window = ErrorWindow()
        window.center()
    else:
        window = MainWindow()
        window.center()

    window.show()
    splash.close()

    app.exec_()

    server.kill()
