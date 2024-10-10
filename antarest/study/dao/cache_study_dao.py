from typing import Any, Dict, Optional

from antarest.core.interfaces.cache import ICache
from antarest.study.dao.study_dao import StudiesDAO, StudyDAO


class CacheStudyDAO(StudyDAO):
    """
    Implementation which preferably reads from cache,
    but delegates to a possibly slower implementation if
    data is not in cache.

    All cache management details are implemented here.
    """

    def __init__(self, study_id: str, cache: ICache, delegate_factory: StudiesDAO):
        self._study_id = study_id
        self._cache = cache
        self._delegate_factory = delegate_factory
        self._delegate: Optional[StudyDAO] = None

    def _get_delegate(self) -> StudyDAO:
        if self._delegate is None:
            self._delegate = self._delegate_factory.get_study(self._study_id)
        return self._delegate

    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        cache_id = f"{self._study_id}-areas-ui"
        from_cache = self._cache.get(cache_id)
        if from_cache is not None:
            return from_cache
        ui_info = self._get_delegate().get_all_areas_ui_info()
        self._cache.put(cache_id, ui_info)
        return ui_info


class CacheStudiesDAO(StudiesDAO):
    def __init__(self, cache: ICache, delegate_factory: StudiesDAO):
        self._cache = cache
        self._delegate_factory = delegate_factory

    def get_study(self, study_id: str) -> StudyDAO:
        return CacheStudyDAO(study_id, self._cache, self._delegate_factory)
