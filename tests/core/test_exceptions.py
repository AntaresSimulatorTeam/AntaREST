from antarest.core.exceptions import BindingConstraintDeletionNotAllowed


class TestBindingConstraintDeletionNotAllowed:
    def test_few_binding_constraints(self) -> None:
        object_id = "france"
        binding_ids = ["bc1", "bc2"]
        object_type = "Area"
        exception = BindingConstraintDeletionNotAllowed(object_id, binding_ids, object_type=object_type)
        message = str(exception)
        assert f"{object_type} '{object_id}'" in message
        assert "bc1" in message
        assert "bc2" in message
        assert "more..." not in message

    def test_many_binding_constraints(self) -> None:
        object_id = "france"
        binding_ids = [f"bc{i}" for i in range(1, 50)]
        object_type = "Area"
        exception = BindingConstraintDeletionNotAllowed(object_id, binding_ids, object_type=object_type)
        message = str(exception)
        assert f"{object_type} '{object_id}'" in message
        assert "bc1" in message
        assert "bc2" in message
        assert "more..." in message
