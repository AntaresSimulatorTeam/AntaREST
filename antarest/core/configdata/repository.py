from typing import List, Optional

from sqlalchemy import exists

from antarest.core.configdata.model import ConfigData
from antarest.core.utils.fastapi_sqlalchemy import db


class ConfigDataRepository:
    def save(self, configdata: ConfigData) -> ConfigData:
        configdata = db.session.merge(configdata)
        db.session.add(configdata)
        db.session.commit()
        return configdata

    def get_many(self, keys: List[str]) -> List[ConfigData]:
        configdata_list: List[ConfigData] = db.session.query(
            exists().where(ConfigData.key in keys)
        ).all()
        return configdata_list

    def get(self, key: str) -> Optional[ConfigData]:
        configdata: ConfigData = db.session.query(ConfigData).get(key)
        if configdata is not None:
            db.session.refresh(configdata)
        return configdata
