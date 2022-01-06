from typing import Optional

from antarest.core.maintenance.model import Maintenance
from antarest.core.utils.fastapi_sqlalchemy import db


class MaintenanceRepository:
    def save(self, maintenance: Maintenance) -> Maintenance:
        maintenance = db.session.merge(maintenance)
        db.session.add(maintenance)
        db.session.commit()
        return maintenance

    def get(self) -> Optional[Maintenance]:
        maintenance: Maintenance = db.session.get(Maintenance, "maintenanceid")
        if maintenance is not None:
            db.session.refresh(maintenance)
        return maintenance
