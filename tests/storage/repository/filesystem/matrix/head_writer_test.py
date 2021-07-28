from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import (
    AreaHeadWriter,
    LinkHeadWriter,
)


def test_area():
    writer = AreaHeadWriter(area="de", freq="hourly")
    assert (
        writer.build(var=3, start=2, end=4)
        == "DE\tarea\tde\thourly\n\tVARIABLES\tBEGIN\tEND\n\t3\t2\t4\n\n"
    )


def test_link():
    writer = LinkHeadWriter(src="de", dest="fr", freq="hourly")
    assert (
        writer.build(var=3, start=2, end=4)
        == "DE\tlink\tva\thourly\nFR\tVARIABLES\tBEGIN\tEND\n\t3\t2\t4\n\n"
    )
