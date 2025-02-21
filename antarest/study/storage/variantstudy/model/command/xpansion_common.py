from typing import Any

from antarest.core.exceptions import AreaNotFound, CandidateAlreadyExistsError, LinkNotFound, XpansionFileNotFoundError
from antarest.study.business.model.xpansion_model import XpansionCandidateInternal
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def assert_xpansion_candidate_name_is_not_already_taken(candidates: dict[str, Any], candidate_name: str) -> None:
    for candidate in candidates.values():
        if candidate["name"] == candidate_name:
            raise CandidateAlreadyExistsError(f"The candidate '{candidate_name}' already exists")


def assert_link_profile_are_files(file_study: FileStudy, xpansion_candidate_dto: XpansionCandidateInternal) -> None:
    existing_files = file_study.tree.get(["user", "expansion", "capa"])
    for attr in [
        "link_profile",
        "already_installed_link_profile",
        "direct_link_profile",
        "indirect_link_profile",
        "already_installed_direct_link_profile",
        "already_installed_indirect_link_profile",
    ]:
        if link_file := getattr(xpansion_candidate_dto, attr, None):
            if link_file not in existing_files:
                raise XpansionFileNotFoundError(f"The '{attr}' file '{link_file}' does not exist")


def assert_link_exist(file_study: FileStudy, xpansion_candidate_dto: XpansionCandidateInternal) -> None:
    area1, area2 = xpansion_candidate_dto.link.split(" - ")
    area_from, area_to = sorted([area1, area2])
    if area_from not in file_study.config.areas:
        raise AreaNotFound(area_from)
    if area_to not in file_study.config.get_links(area_from):
        raise LinkNotFound(f"The link from '{area_from}' to '{area_to}' not found")


def assert_candidate_is_correct(
    existing_candidates: dict[str, Any], file_study: FileStudy, candidate: XpansionCandidateInternal
) -> None:
    assert_xpansion_candidate_name_is_not_already_taken(existing_candidates, candidate.name)
    assert_link_profile_are_files(file_study, candidate)
    assert_link_exist(file_study, candidate)
