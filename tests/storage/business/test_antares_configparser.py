import textwrap
from pathlib import Path
from typing import cast

from antarest.study.storage.antares_configparser import (
    AntaresConfigParser,
    AntaresSectionProxy,
)


def test_configparser(tmp_path: Path):
    config = AntaresConfigParser()
    config["general"] = {}
    general_section = cast(AntaresSectionProxy, config["general"])
    general_section["mode"] = "Economy"
    general_section["horizon"] = None  # converted to ""
    general_section["nbyears"] = 2  # converted to str
    general_section["leapyear"] = False  # converted to "false"
    general_section["pi"] = 3.1415926535_8979323846  # converted to str

    config.add_section("output")
    config.set("output", "synthesis", True)

    config_path = tmp_path.joinpath("config.ini")
    with config_path.open(mode="w", encoding="utf-8") as f:
        config.write(f)

    actual = config_path.read_text(encoding="utf-8")
    expected = textwrap.dedent(
        """\
        [general]
        mode = Economy
        horizon = 
        nbyears = 2
        leapyear = false
        pi = 3.141592653589793

        [output]
        synthesis = true
        """
    )
    assert actual.strip() == expected.strip()

    config = AntaresConfigParser()
    config.read(config_path)
    general_section = cast(AntaresSectionProxy, config["general"])
    assert general_section["mode"] == "Economy"
    assert general_section["horizon"] == ""
    assert general_section.getint("nbyears") == 2
    assert general_section.getboolean("leapyear") is False
    assert general_section.getfloat("pi") == 3.1415926535_8979323846
    assert config.getboolean("output", "synthesis") is True
