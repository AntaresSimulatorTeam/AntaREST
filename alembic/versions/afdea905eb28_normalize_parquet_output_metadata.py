"""Normalize parquet output metadata and replace the variables blob.

Revision ID: afdea905eb28
Revises: 0974bca4078d

Legacy variable lists are preserved relationally, but flagged for archive-backed
reconstruction: the old blob has neither units nor reliable column indices.
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "afdea905eb28"
down_revision = "0974bca4078d"
branch_labels = None
depends_on = None

ELEMENTS = {
    "parquet_area": ("area_id",),
    "parquet_link": ("area_1_id", "area_2_id"),
    "parquet_cluster": ("area_id", "cluster_id"),
    "parquet_binding_constraint": ("constraint_id",),
}
CLUSTERS = {
    "thermal_clusters": "thermal_cluster",
    "renewable_clusters": "renewable_cluster",
    "short_term_storages": "short_term_storage",
}
NAMING = {"fk": "fk_%(table_name)s_%(column_0_name)s", "pk": "pk_%(table_name)s"}


def _logs_fk(create):
    if create:
        with op.batch_alter_table("output_v2_logs", naming_convention=NAMING) as batch:
            batch.create_foreign_key(
                "fk_output_v2_logs_study_id",
                "output_v2_metadata",
                ["study_id", "output_id"],
                ["study_id", "output_name"],
                ondelete="CASCADE",
            )
    else:
        fk = sa.inspect(op.get_bind()).get_foreign_keys("output_v2_logs")[0]
        with op.batch_alter_table("output_v2_logs", naming_convention=NAMING) as batch:
            batch.drop_constraint(
                fk["name"] or "fk_output_v2_logs_study_id", type_="foreignkey"
            )


def _metadata_table(name, normalized):
    columns = [
        sa.Column("study_id", sa.String(), nullable=False),
        sa.Column("output_name", sa.String(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("synthesis", sa.Boolean(), nullable=False),
        sa.Column("by_year", sa.Boolean(), nullable=False),
        sa.Column("nb_years", sa.Integer(), nullable=False),
        sa.Column("start_month", sa.Integer(), nullable=False),
        sa.Column("january_first_weekday", sa.Integer(), nullable=False),
        sa.Column("leap_year", sa.Boolean(), nullable=False),
        sa.Column("start_day", sa.Integer(), nullable=False),
        sa.Column("end_day", sa.Integer(), nullable=False),
        sa.Column("first_weekday", sa.Integer(), nullable=False),
    ]
    if normalized:
        columns += [
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("mc_years", sa.String(), nullable=False),
            sa.Column("metadata_version", sa.Integer(), nullable=False),
            sa.UniqueConstraint(
                "study_id", "output_name", name="uq_output_v2_study_name"
            ),
        ]
    else:
        columns += [sa.PrimaryKeyConstraint("study_id", "output_name")]
    return op.create_table(name, *columns)


def _reflect(name):
    return sa.Table(name, sa.MetaData(), autoload_with=op.get_bind())


def _preserve_legacy_variables(output_id, content):
    """Normalize the information we have; the application rebuilds missing data."""
    conn = op.get_bind()
    variables = _reflect("parquet_variable")
    tables = {name: _reflect(name) for name in ELEMENTS}
    catalogues = {}

    def save(aggregation, kind, ids, names):
        catalogue = catalogues.setdefault((aggregation, kind), {})
        columns = []
        for name in names:
            if name not in catalogue:
                catalogue[name] = len(catalogue)
                conn.execute(
                    variables.insert().values(
                        output_id=output_id,
                        scenario_aggregation=aggregation,
                        element_type=kind,
                        column=catalogue[name],
                        name=name,
                        unit=name if kind in CLUSTERS.values() else None,
                        statistic_type=None,
                    )
                )
            columns.append(catalogue[name])
        table = tables[
            "parquet_cluster" if kind in CLUSTERS.values() else "parquet_" + kind
        ]
        conn.execute(
            table.insert().values(
                output_id=output_id,
                scenario_aggregation=aggregation,
                element_type=kind,
                frequency="",
                mc_year=0,
                columns=",".join(map(str, columns)),
                positions=",".join(map(str, range(len(columns)))),
                **ids,
            )
        )

    for key, aggregation in (("mc_ind", "mc-ind"), ("mc_all", "mc-all")):
        values = content.get(
            key, content.get("mcInd" if key == "mc_ind" else "mcAll", {})
        )
        for area in values.get("areas", []):
            save(
                aggregation,
                "area",
                {"area_id": area["name"]},
                area.get("variables", []),
            )
            for plural, kind in CLUSTERS.items():
                camel = "".join(
                    part.title() if i else part
                    for i, part in enumerate(plural.split("_"))
                )
                for cluster in area.get(plural, area.get(camel, [])):
                    save(
                        aggregation,
                        kind,
                        {"area_id": area["name"], "cluster_id": cluster["name"]},
                        cluster["variables"],
                    )
        for link in values.get("links", []):
            save(
                aggregation,
                "link",
                {
                    "area_1_id": link.get("area_1_name", link.get("area1Name")),
                    "area_2_id": link.get("area_2_name", link.get("area2Name")),
                },
                link.get("variables", []),
            )


def upgrade():
    conn = op.get_bind()
    old = _reflect("output_v2_metadata")
    new = _metadata_table("_output_v2_metadata", True)
    names = [c.name for c in old.columns]
    conn.execute(
        new.insert().from_select(
            names + ["mc_years", "metadata_version"],
            sa.select(*[old.c[n] for n in names], sa.literal(""), sa.literal(0)),
        )
    )
    # Detach referencing tables before replacing the parent, including on SQLite
    # with foreign_keys enabled. Keep logs and legacy variable rows in temp tables.
    legacy = _reflect("output_v2_variables")
    backup = op.create_table(
        "_legacy_output_variables",
        sa.Column("study_id", sa.String()),
        sa.Column("output_id", sa.String()),
        sa.Column("variables_list", sa.String()),
    )
    conn.execute(
        backup.insert().from_select(
            ["study_id", "output_id", "variables_list"],
            sa.select(legacy.c.study_id, legacy.c.output_id, legacy.c.variables_list),
        )
    )
    op.drop_table("output_v2_variables")
    _logs_fk(False)
    op.drop_table("output_v2_metadata")
    op.rename_table("_output_v2_metadata", "output_v2_metadata")
    _logs_fk(True)
    op.create_table(
        "parquet_variable",
        sa.Column("output_id", sa.Integer(), primary_key=True),
        sa.Column("scenario_aggregation", sa.String(16), primary_key=True),
        sa.Column("element_type", sa.String(32), primary_key=True),
        sa.Column("column", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("unit", sa.String()),
        sa.Column("statistic_type", sa.String()),
        sa.ForeignKeyConstraint(
            ["output_id"], ["output_v2_metadata.id"], ondelete="CASCADE"
        ),
    )
    for name, identifiers in ELEMENTS.items():
        op.create_table(
            name,
            sa.Column("output_id", sa.Integer(), primary_key=True),
            sa.Column("scenario_aggregation", sa.String(16), primary_key=True),
            sa.Column("element_type", sa.String(32), primary_key=True),
            sa.Column("frequency", sa.String(16), primary_key=True),
            sa.Column("mc_year", sa.Integer(), primary_key=True),
            *[sa.Column(i, sa.String(), primary_key=True) for i in identifiers],
            sa.Column("columns", sa.String(), nullable=False),
            sa.Column("positions", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(
                ["output_id"], ["output_v2_metadata.id"], ondelete="CASCADE"
            ),
        )
        op.create_index(f"ix_{name}_output_id", name, ["output_id"])
    metadata = _reflect("output_v2_metadata")
    rows = conn.execute(
        sa.select(metadata.c.id, backup.c.variables_list).join(
            backup,
            sa.and_(
                metadata.c.study_id == backup.c.study_id,
                metadata.c.output_name == backup.c.output_id,
            ),
        )
    )
    for output_id, content in rows:
        _preserve_legacy_variables(output_id, json.loads(content))
    op.drop_table("_legacy_output_variables")


def _variables_list(output_id):
    conn = op.get_bind()
    table = _reflect("parquet_variable")
    variables = {
        (r.scenario_aggregation, r.element_type, r.column): r
        for r in conn.execute(sa.select(table).where(table.c.output_id == output_id))
    }
    result = {}
    for aggregation, key in (("mc-ind", "mc_ind"), ("mc-all", "mc_all")):
        areas, links = {}, {}
        for name in ("parquet_area", "parquet_link", "parquet_cluster"):
            table = _reflect(name)
            for row in conn.execute(
                sa.select(table).where(
                    table.c.output_id == output_id,
                    table.c.scenario_aggregation == aggregation,
                )
            ):
                if name == "parquet_link":
                    obj = links.setdefault(
                        (row.area_1_id, row.area_2_id),
                        {
                            "area_1_name": row.area_1_id,
                            "area_2_name": row.area_2_id,
                            "variables": set(),
                        },
                    )
                else:
                    obj = areas.setdefault(
                        row.area_id,
                        {
                            "name": row.area_id,
                            "variables": set(),
                            **{kind: {} for kind in CLUSTERS},
                        },
                    )
                    if name == "parquet_cluster":
                        plural = next(
                            k for k, v in CLUSTERS.items() if v == row.element_type
                        )
                        obj = obj[plural].setdefault(
                            row.cluster_id, {"name": row.cluster_id, "variables": set()}
                        )
                for index in row.columns.split(",") if row.columns else []:
                    variable = variables[aggregation, row.element_type, int(index)]
                    if name == "parquet_cluster":
                        value = variable.unit or " "
                    else:
                        value = (
                            f"{variable.name} {variable.statistic_type}".upper().strip()
                            if variable.statistic_type
                            else variable.name
                        )
                    obj["variables"].add(value)
        for area in areas.values():
            for kind in CLUSTERS:
                area[kind] = [area[kind][k] for k in sorted(area[kind])]
        result[key] = {
            "areas": [areas[k] for k in sorted(areas)],
            "links": [links[k] for k in sorted(links)],
        }
    return json.dumps(result, default=lambda value: sorted(value))


def downgrade():
    conn = op.get_bind()
    old = _reflect("output_v2_metadata")
    blobs = [
        (row.study_id, row.output_name, _variables_list(row.id))
        for row in conn.execute(sa.select(old))
    ]
    for name in ELEMENTS:
        op.drop_table(name)
    op.drop_table("parquet_variable")
    new = _metadata_table("_output_v2_metadata", False)
    names = [c.name for c in new.columns]
    conn.execute(new.insert().from_select(names, sa.select(*[old.c[n] for n in names])))
    _logs_fk(False)
    op.drop_table("output_v2_metadata")
    op.rename_table("_output_v2_metadata", "output_v2_metadata")
    _logs_fk(True)
    variables = op.create_table(
        "output_v2_variables",
        sa.Column("study_id", sa.String(36), primary_key=True),
        sa.Column("output_id", sa.String(), primary_key=True),
        sa.Column("variables_list_version", sa.Integer(), nullable=False),
        sa.Column("variables_list", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_id", "output_id"],
            ["output_v2_metadata.study_id", "output_v2_metadata.output_name"],
            ondelete="CASCADE",
        ),
    )
    for study_id, output_id, content in blobs:
        conn.execute(
            variables.insert().values(
                study_id=study_id,
                output_id=output_id,
                variables_list_version=1,
                variables_list=content,
            )
        )
