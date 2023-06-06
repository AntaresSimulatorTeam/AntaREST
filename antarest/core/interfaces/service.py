import threading
from abc import abstractmethod, ABC


class IService(ABC):
    """
    A base class for long running processing services.

    Processing may be started either in a background thread or in current thread.
    Implementations must implement the `_loop` method.
    """

    def start(self, threaded: bool = True) -> None:
        """
        Starts the processing loop.

        Args:
            threaded: if True, the loop is started in a daemon thread,
                      else in this thread
        """
        if threaded:
            thread = threading.Thread(
                target=self._loop,
                name=self.__class__.__name__,
                daemon=True,
            )
            thread.start()
        else:
            self._loop()

    @abstractmethod
    def _loop(self) -> None:
        raise NotImplementedError
