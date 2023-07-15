import itertools
import statistics

from antarest.study.business.areas.table_group import TableGroup
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)


class TestTableGroup:
    def test_table_group__st_storage(self) -> None:
        # Let's define some Electrical Production Units
        prod_unit1a = TableGroup(
            properties={
                "group": "Battery",
                "name": "Siemens Battery",
                "injectionNominalCapacity": 150.0,
                "withdrawalNominalCapacity": 150.0,
                "reservoirCapacity": 600.0,
                "efficiency": 94,
            }
        )
        prod_unit2a = TableGroup(
            properties={
                "group": "PSP_Open",
                "name": "Grand'Maison",
                "injectionNominalCapacity": 1500.0,
                "withdrawalNominalCapacity": 1800.0,
                "reservoirCapacity": 20000.0,
                "efficiency": 78,
            }
        )
        prod_unit2b = TableGroup(
            properties={
                "group": "PSP_Open",
                "name": "Tignes",
                "injectionNominalCapacity": 3000.0,
                "withdrawalNominalCapacity": 3600.0,
                "reservoirCapacity": 40000.0,
                "efficiency": 82,
            }
        )

        # Sort Production Units by group name
        prod_units = [prod_unit1a, prod_unit2a, prod_unit2b]
        order_by = lambda g: g.properties["group"]
        prod_units.sort(key=order_by)

        # Group Production Units into Production Groups
        prod_network = TableGroup(
            properties={"name": "Short-Term Storage of Area FR"},
            operations={
                "injectionNominalCapacity": sum,
                "withdrawalNominalCapacity": sum,
                "reservoirCapacity": sum,
            },
        )
        for group_name, group_list in itertools.groupby(
            prod_units, key=order_by
        ):
            prod_group = TableGroup(
                properties={"name": group_name},
                operations={
                    "injectionNominalCapacity": sum,
                    "withdrawalNominalCapacity": sum,
                    "reservoirCapacity": sum,
                    "efficiency": statistics.mean,
                },
                elements={
                    transform_name_to_id(g.properties["name"]): g
                    for g in group_list
                },
            )
            group_id = transform_name_to_id(group_name)
            prod_network.elements[group_id] = prod_group

        # Calculate the sums and means
        prod_network.calc_operations()
        print(prod_network)

        actual = prod_network.dict(by_alias=True)
        expected = {
            "properties": {
                "group": "",
                "name": "Short-Term Storage of Area FR",
                "injectionNominalCapacity": 4650.0,
                "withdrawalNominalCapacity": 5550.0,
                "reservoirCapacity": 60600.0,
                "efficiency": "",
            },
            "elements": {
                "battery": {
                    "properties": {
                        "group": "",
                        "name": "Battery",
                        "injectionNominalCapacity": 150.0,
                        "withdrawalNominalCapacity": 150.0,
                        "reservoirCapacity": 600.0,
                        "efficiency": 94,
                    },
                    "elements": {
                        "siemens battery": {
                            "properties": {
                                "group": "Battery",
                                "name": "Siemens Battery",
                                "injectionNominalCapacity": 150.0,
                                "withdrawalNominalCapacity": 150.0,
                                "reservoirCapacity": 600.0,
                                "efficiency": 94,
                            },
                            "elements": {},
                        }
                    },
                },
                "psp_open": {
                    "properties": {
                        "group": "",
                        "name": "PSP_Open",
                        "injectionNominalCapacity": 4500.0,
                        "withdrawalNominalCapacity": 5400.0,
                        "reservoirCapacity": 60000.0,
                        "efficiency": 80,
                    },
                    "elements": {
                        "grand maison": {
                            "properties": {
                                "group": "PSP_Open",
                                "name": "Grand'Maison",
                                "injectionNominalCapacity": 1500.0,
                                "withdrawalNominalCapacity": 1800.0,
                                "reservoirCapacity": 20000.0,
                                "efficiency": 78,
                            },
                            "elements": {},
                        },
                        "tignes": {
                            "properties": {
                                "group": "PSP_Open",
                                "name": "Tignes",
                                "injectionNominalCapacity": 3000.0,
                                "withdrawalNominalCapacity": 3600.0,
                                "reservoirCapacity": 40000.0,
                                "efficiency": 82,
                            },
                            "elements": {},
                        },
                    },
                },
            },
        }
        assert actual == expected
