from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView

import sys
import time
from pathlib import Path

import requests
import uvicorn

from antarest import __version__
from multiprocessing import Process

from antarest.main import fastapi_app, get_arguments


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setBaseSize(1024, 800)
        self.setMinimumSize(1024, 800)
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://localhost:8080"))
        self.setCentralWidget(self.browser)


def front(server_process: Process):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec_()

    server_process.kill()


def run_server(config_file: Path):
    app, _ = fastapi_app(
        config_file,
        mount_front=True,
        auto_upgrade_db=True,
    )
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    config_file, display_version, no_front, auto_upgrade_db = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()

    server = Process(
        target=run_server,
        args=(
            config_file,
        ),
    )
    server.start()
    countdown = 10
    while countdown > 0:
        try:
            res = requests.get("http://localhost:8080")
            if res.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
        countdown -= 1
    front(server)



