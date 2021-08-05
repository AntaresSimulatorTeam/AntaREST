import platform
import sys
import time
from pathlib import Path

import requests
import uvicorn

from antarest import __version__
from cefpython3 import cefpython as cef
from multiprocessing import Process

from antarest.main import fastapi_app, get_arguments


def front(server_process: Process):
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    cef.CreateBrowserSync(
        url="http://localhost:8080/", window_title="Antares Web"
    )
    cef.MessageLoop()
    cef.Shutdown()
    server_process.close()


def check_versions():
    ver = cef.GetVersion()
    print("[hello_world.py] CEF Python {ver}".format(ver=ver["version"]))
    print("[hello_world.py] Chromium {ver}".format(ver=ver["chrome_version"]))
    print("[hello_world.py] CEF {ver}".format(ver=ver["cef_version"]))
    print(
        "[hello_world.py] Python {ver} {arch}".format(
            ver=platform.python_version(), arch=platform.architecture()[0]
        )
    )
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


def run_server(config_file: Path, auto_upgrade_db: bool):
    app, _ = fastapi_app(
        config_file,
        mount_front=True,
        auto_upgrade_db=auto_upgrade_db,
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
            auto_upgrade_db,
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
