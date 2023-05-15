from pathlib import Path


def upgrade_860(study_path: Path) -> None:
    study_path.joinpath("input", "st-storage", "clusters").mkdir(parents=True)
    study_path.joinpath("input", "st-storage", "series").mkdir(parents=True)
    list_areas = (
        study_path.joinpath("input", "areas", "list.txt")
        .read_text(encoding="utf-8")
        .splitlines(keepends=False)
    )
    if len(list_areas) != 0:  # filter out empty studies
        for folder in list_areas:
            folder_path = study_path.joinpath(
                "input", "st-storage", "clusters", f"{Path(folder).stem}"
            )
            folder_path.mkdir(parents=True)
            (folder_path / "list.ini").touch()
