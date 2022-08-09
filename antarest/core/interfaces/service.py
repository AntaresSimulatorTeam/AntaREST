import threading
from abc import abstractmethod, ABC


class IService(ABC):
    def __init__(self) -> None:
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def start(self, threaded: bool = False) -> None:
        if threaded:
            self.thread.start()
        else:
            self._loop()

    @abstractmethod
    def _loop(self) -> None:
        raise NotImplementedError
