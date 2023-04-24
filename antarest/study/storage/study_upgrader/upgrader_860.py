import glob
from pathlib import Path


def upgrade_860(study_path: Path) -> None:
    # Liste des trucs à faire
    """

    Add directories input/st-storage/clusters and input/st-storage/series
    For each area, add directory input/st-storage/clusters/<area id>/list.ini

    This file contains the multiple sections whose name is ignored. Each section contains these properties:
        name [str]
        group [str]. Possible values: "PSP_open", "PSP_closed", "Pondage", "Battery", "Other_1", ... , "Other_5". Default Other_1
        efficiency [double] in range 0-1
        reservoircapacity [double] > 0
        initiallevel [double] in range 0-1
        withdrawalnominalcapacity [double] in range 0-1
        injectionnominalcapacity [double] in range 0-1
        storagecycle [int] in range 24-168

    For each short-term-storage object, add the corresponding time-series in directory input/st-storage/series/<area id>/<STS id>. All of these files contain 8760 rows and 1 column.
        PMAX-injection.txt All entries must be in range 0-1
        PMAX-withdrawal.txt All entries must be in range 0-1
        inflow.txt All entries must be > 0
        lower-rule-curve.txt All entries must be in range 0-1
        upper-rule-curve.txt All entries must be in range 0-1

    In files input/thermal/cluster/area/list.ini add properties nh3, nox, pm2_5, pm5, pm10, nmvoc, op1, op2, op3, op4, op5 [double]. These properties are emission factors similar to the existing one for CO2.
    """



    #study_path.joinpath("input", "st-storage", "clusters").mkdir(parents=True)
    #study_path.joinpath("input", "st-storage", "series").mkdir(parents=True)
    areas = glob.glob(str(study_path / "input" / "links" / "*"))
    for folder in areas:
        area_name = Path(folder).stem
        print(area_name)
    return
