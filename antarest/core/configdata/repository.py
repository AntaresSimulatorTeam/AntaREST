import json
from operator import and_
from typing import Optional

from antarest.core.configdata.model import ConfigData
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON
from antarest.core.utils.fastapi_sqlalchemy import db


class ConfigDataRepository:
    def save(self, configdata: ConfigData) -> ConfigData:
        configdata = db.session.merge(configdata)
        db.session.add(configdata)
        db.session.commit()
        return configdata

    def get(
        self, key: str, owner: Optional[int] = None
    ) -> Optional[ConfigData]:
        configdata: ConfigData = (
            db.session.query(ConfigData)
            .filter(
                and_(
                    ConfigData.owner == owner or DEFAULT_ADMIN_USER.id,
                    ConfigData.key == key,
                )
            )
            .first()
        )
        return configdata

    def get_json(
        self, key: str, owner: Optional[int] = None
    ) -> Optional[JSON]:
        configdata = self.get(key, owner)
        if configdata:
            data: JSON = json.loads(configdata.value)
            return data
        return None

    def put_json(
        self, key: str, data: JSON, owner: Optional[int] = None
    ) -> None:
        configdata = ConfigData(
            key=key,
            value=json.dumps(data),
            owner=owner or DEFAULT_ADMIN_USER.id,
        )
        configdata = db.session.merge(configdata)
        db.session.add(configdata)
        db.session.commit()
