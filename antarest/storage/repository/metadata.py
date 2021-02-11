from typing import Optional, List

from sqlalchemy.orm import Session  # type: ignore

from antarest.storage.model import Metadata


class StudyMetadataRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, metadata: Metadata) -> Metadata:
        self.session.add(metadata)
        self.session.commit()
        return metadata

    def get(self, id: int) -> Optional[Metadata]:
        metadata: Metadata = self.session.query(Metadata).get(id)
        return metadata

    def get_all(self) -> List[Metadata]:
        metadatas: List[Metadata] = self.session.query(Metadata).all()
        return metadatas

    def delete(self, id: int) -> None:
        u: Metadata = self.session.query(Metadata).get(id)
        self.session.delete(u)
        self.session.commit()
