from typing import Optional, List

from sqlalchemy.orm import Session  # type: ignore

from antarest.storage.model import Study


class StudyMetadataRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, metadata: Study) -> Study:
        metadata.groups = [self.session.merge(g) for g in metadata.groups]
        metadata.owner = self.session.merge(metadata.owner)
        self.session.add(metadata)
        self.session.commit()
        return metadata

    def get(self, id: str) -> Optional[Study]:
        metadata: Study = self.session.query(Study).get(id)
        return metadata

    def get_all(self) -> List[Study]:
        metadatas: List[Study] = self.session.query(Study).all()
        return metadatas

    def delete(self, id: str) -> None:
        u: Study = self.session.query(Study).get(id)
        self.session.delete(u)
        self.session.commit()
