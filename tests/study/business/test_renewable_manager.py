from antarest.study.business.renewable_manager import RenewableFormFields, TsMode


class TestRenewableFormFields:

    def test_renewable_form_fields__construct(self):
        # Test nominal use case
        form = RenewableFormFields.construct(
            group="Wind",
            ts_mode=TsMode.ProductionFactor,
            name="Cluster1",
            unit_count=10,
            enabled=True,
            nominal_capacity=500.0
        )

        assert form.group == "Wind"
        assert form.ts_mode == TsMode.ProductionFactor
        assert form.name == "Cluster1"
        assert form.unit_count == 10
        assert form.enabled is True
        assert form.nominal_capacity == 500.0

    def test_renewable_form_fields__json_obj(self):
        """
        Construct a `RenewableFormFields` from a JSON object
        which attribute names are in _camelCase_.
        """
        json_obj = {
            "name": "oleron",
            "group": "wind offshore",
            "nominalCapacity": 1000.000000,
            "unitCount": 2,
            "tsMode": "production-factor",
            "enabled": True
        }
        form = RenewableFormFields(**json_obj)
        assert form.name == json_obj["name"]
        assert form.group == json_obj["group"]
        assert form.nominal_capacity == json_obj["nominalCapacity"]
        assert form.unit_count == json_obj["unitCount"]
        assert form.ts_mode == json_obj["tsMode"]
        assert form.enabled is True

