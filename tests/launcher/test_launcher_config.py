import pytest

from antarest.launcher.model import LauncherConfigDTO, make_other_options_from_launcher_config
from antarest.study.model import STUDY_VERSION_9_1, STUDY_VERSION_9_2, STUDY_VERSION_9_3


def mkconfig(**kwargs):
    """Shortcut to create a LauncherConfigDTO with defaults."""
    return LauncherConfigDTO(
        **{
            "id": "id123",
            "name": "test",
            "linear_solver": "xpress",
            "use_optim_1_basis_next_week": True,
            "use_optim_1_basis_optim_2": True,
            "linear_solver_param": None,
            "linear_solver_param_optim_1": None,
            "linear_solver_param_optim_2": None,
            "min_antares_version": STUDY_VERSION_9_2,
            **kwargs,
        }
    )


def test_basic_xpress_solver_only():
    config = mkconfig()
    assert make_other_options_from_launcher_config(config) == "--solver=xpress"


def test_xpress_nobasis_flags():
    config = mkconfig(
        use_optim_1_basis_next_week=False,
        use_optim_1_basis_optim_2=False,
    )
    result = make_other_options_from_launcher_config(config)
    # order should be deterministic
    assert result == "--solver=xpress --nobasis1 --nobasis2"


def test_xpress_single_nobasis1():
    config = mkconfig(use_optim_1_basis_next_week=False)
    assert make_other_options_from_launcher_config(config) == "--solver=xpress --nobasis1"


def test_xpress_with_common_params():
    config = mkconfig(
        linear_solver_param=[("THREADS", 4), ("FEASTOL", 1)],
    )
    result = make_other_options_from_launcher_config(config)
    assert '--param-optim1="THREADS 4 FEASTOL 1"' in result
    assert '--param-optim2="THREADS 4 FEASTOL 1"' in result


def test_xpress_combined_common_and_specific_params():
    config = mkconfig(
        linear_solver_param=[("THREADS", 4)],
        linear_solver_param_optim_1=[("PRESOLVE", 1)],
        linear_solver_param_optim_2=[("MIPRELSTOP", 0.01)],
    )
    result = make_other_options_from_launcher_config(config)
    assert '--param-optim1="THREADS 4 PRESOLVE 1"' in result, "common + optim1 combined"
    assert '--param-optim2="THREADS 4 MIPRELSTOP 0.01"' in result, "common + optim2 combined"


def test_presolve_detected_in_optim2_only():
    config = mkconfig(linear_solver_param_optim_2=[("PRESOLVE", 100), ("THREADS", 2)])
    result = make_other_options_from_launcher_config(config)
    assert result == '--solver=xpress --param-optim2="PRESOLVE 100 THREADS 2"'


def test_valid_config_minimal():
    cfg = LauncherConfigDTO(name="default", linear_solver="xpress")
    assert cfg.linear_solver == "xpress"
    assert cfg.use_optim_1_basis_next_week is True
    assert cfg.use_optim_1_basis_optim_2 is True


def test_name_cannot_be_empty():
    with pytest.raises(ValueError, match="name cannot be empty"):
        LauncherConfigDTO(name="   ", linear_solver="xpress")


def test_min_version_must_not_exceed_max():
    with pytest.raises(ValueError, match="min_antares_version cannot be greater"):
        LauncherConfigDTO(
            name="valid",
            linear_solver="xpress",
            min_antares_version=STUDY_VERSION_9_3,
            max_antares_version=STUDY_VERSION_9_2,
        )


def test_invalid_key_in_solver_params():
    with pytest.raises(ValueError, match="Invalid key"):
        LauncherConfigDTO(
            name="valid",
            linear_solver="xpress",
            linear_solver_param=[("INVALID-KEY!", "1")],
        )


def test_invalid_value_in_solver_params():
    with pytest.raises(ValueError, match="Invalid value"):
        LauncherConfigDTO(
            name="valid",
            linear_solver="xpress",
            linear_solver_param=[("KEY", "1.2.3")],
        )


def test_optim_params_before_9_2_not_allowed():
    with pytest.raises(ValueError, match="not supported before Antares version 9.2"):
        LauncherConfigDTO(
            name="valid",
            linear_solver="xpress",
            min_antares_version=STUDY_VERSION_9_1,
            linear_solver_param_optim_1=[("PRESOLVE", "1")],
        )
