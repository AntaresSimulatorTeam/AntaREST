import logging
import time

from antarest.core.interfaces.service import IService
from antarest.core.tasks.service import ITaskService
from antarest.scheduler.model import ScheduledAction
from antarest.scheduler.repository import ScheduledActionsRepository

logger = logging.getLogger(__name__)


class SchedulerService(IService):
    def __init__(
        self,
        task_service: ITaskService,
        repository: ScheduledActionsRepository,
    ):
        super(SchedulerService, self).__init__()
        self.task_service = task_service
        self.repository = repository

    def _loop(self) -> None:
        while True:
            try:
                action = self.repository.get_first_scheduled_action()
                if action:
                    self.process_action(action)
            except Exception as e:
                logger.error("Failed to process scheduled action", exc_info=e)
            finally:
                time.sleep(1)

    def process_action(self, action: ScheduledAction) -> None:
        raise NotImplementedError
