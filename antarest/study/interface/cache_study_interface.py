from typing import Any, Dict, Optional

from antarest.core.interfaces.cache import ICache
from antarest.study.interface.study_interface import StudyInterface, StudyInterfaceFactory


class CacheStudyInterface(StudyInterface):
    """
    Implementation which preferrably reads from cache,
    but delegates to a possibly slower implementation if
    data is not in cache.

    All cache management details are implemented here.
    """

    def __init__(self, study_id: str, cache: ICache, delegate_factory: StudyInterfaceFactory):
        self._study_id = study_id
        self._cache = cache
        self._delegate_factory = delegate_factory
        self._delegate: Optional[StudyInterface] = None

    def _get_delegate(self) -> StudyInterface:
        if self._delegate is None:
            self._delegate = self._delegate_factory.create(self._study_id)
        return self._delegate

    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        cache_id = f"{self._study_id}-areas-ui"
        from_cache = self._cache.get(cache_id)
        if from_cache is not None:
            return from_cache
        ui_info = self._get_delegate().get_all_areas_ui_info()
        self._cache.put(cache_id, ui_info)
        return ui_info
