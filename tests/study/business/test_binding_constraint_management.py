import pytest

from antarest.study.business.binding_constraint_management import ClusterInfoDTO, ConstraintTermDTO, LinkInfoDTO


class TestLinkInfoDTO:
    @pytest.mark.parametrize(
        "area1, area2, expected",
        [
            ("Area 1", "Area 2", "area 1%area 2"),
            ("de", "fr", "de%fr"),
            ("fr", "de", "de%fr"),
            ("FR", "de", "de%fr"),
        ],
    )
    def test_constraint_id(self, area1: str, area2: str, expected: str) -> None:
        info = LinkInfoDTO(area1=area1, area2=area2)
        assert info.calc_term_id() == expected


class TestClusterInfoDTO:
    @pytest.mark.parametrize(
        "area, cluster, expected",
        [
            ("Area 1", "Cluster X", "area 1.cluster x"),
            ("de", "Nuclear", "de.nuclear"),
            ("GB", "Gas", "gb.gas"),
        ],
    )
    def test_constraint_id(self, area: str, cluster: str, expected: str) -> None:
        info = ClusterInfoDTO(area=area, cluster=cluster)
        assert info.calc_term_id() == expected


class TestConstraintTermDTO:
    def test_constraint_id__link(self):
        term = ConstraintTermDTO(
            id="foo",
            weight=3.14,
            offset=123,
            data=LinkInfoDTO(area1="Area 1", area2="Area 2"),
        )
        assert term.calc_term_id() == term.data.calc_term_id()

    def test_constraint_id__cluster(self):
        term = ConstraintTermDTO(
            id="foo",
            weight=3.14,
            offset=123,
            data=ClusterInfoDTO(area="Area 1", cluster="Cluster X"),
        )
        assert term.calc_term_id() == term.data.calc_term_id()

    def test_constraint_id__other(self):
        term = ConstraintTermDTO(
            id="foo",
            weight=3.14,
            offset=123,
        )
        assert term.calc_term_id() == "foo"
