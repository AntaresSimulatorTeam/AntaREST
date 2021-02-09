from typing import Optional, List

from sqlalchemy.engine import Engine  # type: ignore

from antarest.common.persistence import session_scope
from antarest.storage.model import Metadata


class StudyMetadataRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def save(self, metadata: Metadata) -> Metadata:
        with session_scope(self.engine) as sess:
            sess.add(metadata)
            sess.commit()
            return metadata

    def get(self, id: int) -> Optional[Metadata]:
        with session_scope(self.engine) as sess:
            metadata: Metadata = sess.query(Metadata).get(id)
            return metadata

    def get_all(self) -> List[Metadata]:
        with session_scope(self.engine) as sess:
            metadatas: List[Metadata] = sess.query(Metadata).all()
            return metadatas

    def delete(self, id: int) -> None:
        with session_scope(self.engine) as sess:
            u: Metadata = sess.query(Metadata).get(id)
            sess.delete(u)
