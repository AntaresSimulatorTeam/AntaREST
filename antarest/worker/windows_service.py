from pathlib import Path

import win32serviceutil
import win32service
import win32event
import servicemanager
from multiprocessing import Process

from antarest.core.config import Config
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest.main import init_db, create_worker


class Service(win32serviceutil.ServiceFramework):
    _svc_name_ = "TestService"
    _svc_display_name_ = "Test Service"
    _svc_description_ = "Tests Python service framework by receiving and echoing messages over a named pipe"

    def __init__(self, *args):
        super().__init__(*args)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.process.terminate()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.process = Process(target=self.main)
        self.process.start()
        self.process.run()

    def main(self):
        res = get_local_path() / "resources"
        config_file = Path("D:/ApplisRTE/AntaresWebWorker.yml")
        config = Config.from_yaml_file(res=res, file=config_file)
        configure_logger(config)
        init_db(config_file, config, False, None)
        worker = create_worker(config)
        worker.start()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Service)
