from typing import Optional

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.scheduler.model import ScheduledAction


class ScheduledActionsRepository:
    def get_first_scheduled_action(self) -> Optional[ScheduledAction]:
        action: Optional[ScheduledAction] = db.session.query(
            ScheduledAction
        ).first()
        return action
