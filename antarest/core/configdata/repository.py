from operator import and_
from typing import Optional

from antarest.core.configdata.model import ConfigData
from antarest.core.utils.fastapi_sqlalchemy import db


class ConfigDataRepository:
    def save(self, configdata: ConfigData) -> ConfigData:
        configdata = db.session.merge(configdata)
        db.session.add(configdata)
        db.session.commit()
        return configdata

    def get(self, key: str, owner: int) -> Optional[ConfigData]:
        configdata: ConfigData = (
            db.session.query(ConfigData)
            .filter(and_(ConfigData.owner == owner, ConfigData.key == key))
            .first()
        )
        return configdata
