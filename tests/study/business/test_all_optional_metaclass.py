# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import typing as t

import pytest
from pydantic import BaseModel, Field, ValidationError

from antarest.study.business.all_optional_meta import AllOptionalMetaclass

# ==============================================
# Classic way to use default and optional values
# ==============================================


class ClassicModel(BaseModel):
    mandatory: float = Field(ge=0, le=1)
    mandatory_with_default: float = Field(ge=0, le=1, default=0.2)
    mandatory_with_none: float = Field(ge=0, le=1, default=None)
    optional: t.Optional[float] = Field(ge=0, le=1)
    optional_with_default: t.Optional[float] = Field(ge=0, le=1, default=0.2)
    optional_with_none: t.Optional[float] = Field(ge=0, le=1, default=None)


class ClassicSubModel(ClassicModel):
    pass


class TestClassicModel:
    """
    Test that default and optional values work as expected.
    """

    @pytest.mark.parametrize("cls", [ClassicModel, ClassicSubModel])
    def test_classes(self, cls: t.Type[BaseModel]) -> None:
        assert cls.__fields__["mandatory"].required is True
        assert cls.__fields__["mandatory"].allow_none is False
        assert cls.__fields__["mandatory"].default is None
        assert cls.__fields__["mandatory"].default_factory is None  # undefined

        assert cls.__fields__["mandatory_with_default"].required is False
        assert cls.__fields__["mandatory_with_default"].allow_none is False
        assert cls.__fields__["mandatory_with_default"].default == 0.2
        assert cls.__fields__["mandatory_with_default"].default_factory is None  # undefined

        assert cls.__fields__["mandatory_with_none"].required is False
        assert cls.__fields__["mandatory_with_none"].allow_none is True
        assert cls.__fields__["mandatory_with_none"].default is None
        assert cls.__fields__["mandatory_with_none"].default_factory is None  # undefined

        assert cls.__fields__["optional"].required is False
        assert cls.__fields__["optional"].allow_none is True
        assert cls.__fields__["optional"].default is None
        assert cls.__fields__["optional"].default_factory is None  # undefined

        assert cls.__fields__["optional_with_default"].required is False
        assert cls.__fields__["optional_with_default"].allow_none is True
        assert cls.__fields__["optional_with_default"].default == 0.2
        assert cls.__fields__["optional_with_default"].default_factory is None  # undefined

        assert cls.__fields__["optional_with_none"].required is False
        assert cls.__fields__["optional_with_none"].allow_none is True
        assert cls.__fields__["optional_with_none"].default is None
        assert cls.__fields__["optional_with_none"].default_factory is None  # undefined

    @pytest.mark.parametrize("cls", [ClassicModel, ClassicSubModel])
    def test_initialization(self, cls: t.Type[ClassicModel]) -> None:
        # We can build a model without providing optional or default values.
        # The initialized value will be the default value or `None` for optional values.
        obj = cls(mandatory=0.5)
        assert obj.mandatory == 0.5
        assert obj.mandatory_with_default == 0.2
        assert obj.mandatory_with_none is None
        assert obj.optional is None
        assert obj.optional_with_default == 0.2
        assert obj.optional_with_none is None

        # We must provide a value for mandatory fields.
        with pytest.raises(ValidationError):
            cls()

    @pytest.mark.parametrize("cls", [ClassicModel, ClassicSubModel])
    def test_validation(self, cls: t.Type[ClassicModel]) -> None:
        # We CANNOT use `None` as a value for a field with a default value.
        with pytest.raises(ValidationError):
            cls(mandatory=0.5, mandatory_with_default=None)

        # We can use `None` as a value for optional fields with default value.
        cls(mandatory=0.5, optional_with_default=None)

        # We can validate a model with valid values.
        cls(
            mandatory=0.5,
            mandatory_with_default=0.2,
            mandatory_with_none=0.2,
            optional=0.5,
            optional_with_default=0.2,
            optional_with_none=0.2,
        )

        # We CANNOT validate a model with invalid values.
        with pytest.raises(ValidationError):
            cls(mandatory=2)

        with pytest.raises(ValidationError):
            cls(mandatory=0.5, mandatory_with_default=2)

        with pytest.raises(ValidationError):
            cls(mandatory=0.5, mandatory_with_none=2)

        with pytest.raises(ValidationError):
            cls(mandatory=0.5, optional=2)

        with pytest.raises(ValidationError):
            cls(mandatory=0.5, optional_with_default=2)

        with pytest.raises(ValidationError):
            cls(mandatory=0.5, optional_with_none=2)


# ==========================
# Using AllOptionalMetaclass
# ==========================


class AllOptionalModel(BaseModel, metaclass=AllOptionalMetaclass):
    mandatory: float = Field(ge=0, le=1)
    mandatory_with_default: float = Field(ge=0, le=1, default=0.2)
    mandatory_with_none: float = Field(ge=0, le=1, default=None)
    optional: t.Optional[float] = Field(ge=0, le=1)
    optional_with_default: t.Optional[float] = Field(ge=0, le=1, default=0.2)
    optional_with_none: t.Optional[float] = Field(ge=0, le=1, default=None)


class AllOptionalSubModel(AllOptionalModel):
    pass


class InheritedAllOptionalModel(ClassicModel, metaclass=AllOptionalMetaclass):
    pass


class TestAllOptionalModel:
    """
    Test that AllOptionalMetaclass works with base classes.
    """

    @pytest.mark.parametrize("cls", [AllOptionalModel, AllOptionalSubModel, InheritedAllOptionalModel])
    def test_classes(self, cls: t.Type[BaseModel]) -> None:
        assert cls.__fields__["mandatory"].required is False
        assert cls.__fields__["mandatory"].allow_none is True
        assert cls.__fields__["mandatory"].default is None
        assert cls.__fields__["mandatory"].default_factory is None  # undefined

        assert cls.__fields__["mandatory_with_default"].required is False
        assert cls.__fields__["mandatory_with_default"].allow_none is True
        assert cls.__fields__["mandatory_with_default"].default == 0.2
        assert cls.__fields__["mandatory_with_default"].default_factory is None  # undefined

        assert cls.__fields__["mandatory_with_none"].required is False
        assert cls.__fields__["mandatory_with_none"].allow_none is True
        assert cls.__fields__["mandatory_with_none"].default is None
        assert cls.__fields__["mandatory_with_none"].default_factory is None  # undefined

        assert cls.__fields__["optional"].required is False
        assert cls.__fields__["optional"].allow_none is True
        assert cls.__fields__["optional"].default is None
        assert cls.__fields__["optional"].default_factory is None  # undefined

        assert cls.__fields__["optional_with_default"].required is False
        assert cls.__fields__["optional_with_default"].allow_none is True
        assert cls.__fields__["optional_with_default"].default == 0.2
        assert cls.__fields__["optional_with_default"].default_factory is None  # undefined

        assert cls.__fields__["optional_with_none"].required is False
        assert cls.__fields__["optional_with_none"].allow_none is True
        assert cls.__fields__["optional_with_none"].default is None
        assert cls.__fields__["optional_with_none"].default_factory is None  # undefined

    @pytest.mark.parametrize("cls", [AllOptionalModel, AllOptionalSubModel, InheritedAllOptionalModel])
    def test_initialization(self, cls: t.Type[AllOptionalModel]) -> None:
        # We can build a model without providing values.
        # The initialized value will be the default value or `None` for optional values.
        # Note that the mandatory fields are not required anymore, and can be `None`.
        obj = cls()
        assert obj.mandatory is None
        assert obj.mandatory_with_default == 0.2
        assert obj.mandatory_with_none is None
        assert obj.optional is None
        assert obj.optional_with_default == 0.2
        assert obj.optional_with_none is None

        # If we convert the model to a dictionary, without `None` values,
        # we should have a dictionary with default values only.
        actual = obj.dict(exclude_none=True)
        expected = {
            "mandatory_with_default": 0.2,
            "optional_with_default": 0.2,
        }
        assert actual == expected

    @pytest.mark.parametrize("cls", [AllOptionalModel, AllOptionalSubModel, InheritedAllOptionalModel])
    def test_validation(self, cls: t.Type[AllOptionalModel]) -> None:
        # We can use `None` as a value for all fields.
        cls(mandatory=None)
        cls(mandatory_with_default=None)
        cls(mandatory_with_none=None)
        cls(optional=None)
        cls(optional_with_default=None)
        cls(optional_with_none=None)

        # We can validate a model with valid values.
        cls(
            mandatory=0.5,
            mandatory_with_default=0.2,
            mandatory_with_none=0.2,
            optional=0.5,
            optional_with_default=0.2,
            optional_with_none=0.2,
        )

        # We CANNOT validate a model with invalid values.
        with pytest.raises(ValidationError):
            cls(mandatory=2)

        with pytest.raises(ValidationError):
            cls(mandatory_with_default=2)

        with pytest.raises(ValidationError):
            cls(mandatory_with_none=2)

        with pytest.raises(ValidationError):
            cls(optional=2)

        with pytest.raises(ValidationError):
            cls(optional_with_default=2)

        with pytest.raises(ValidationError):
            cls(optional_with_none=2)


# The `use_none` keyword argument is set to `True` to allow the use of `None`
# as a default value for the fields of the model.


class UseNoneModel(BaseModel, metaclass=AllOptionalMetaclass, use_none=True):
    mandatory: float = Field(ge=0, le=1)
    mandatory_with_default: float = Field(ge=0, le=1, default=0.2)
    mandatory_with_none: float = Field(ge=0, le=1, default=None)
    optional: t.Optional[float] = Field(ge=0, le=1)
    optional_with_default: t.Optional[float] = Field(ge=0, le=1, default=0.2)
    optional_with_none: t.Optional[float] = Field(ge=0, le=1, default=None)


class UseNoneSubModel(UseNoneModel):
    pass


class InheritedUseNoneModel(ClassicModel, metaclass=AllOptionalMetaclass, use_none=True):
    pass


class TestUseNoneModel:
    @pytest.mark.parametrize("cls", [UseNoneModel, UseNoneSubModel, InheritedUseNoneModel])
    def test_classes(self, cls: t.Type[BaseModel]) -> None:
        assert cls.__fields__["mandatory"].required is False
        assert cls.__fields__["mandatory"].allow_none is True
        assert cls.__fields__["mandatory"].default is None
        assert cls.__fields__["mandatory"].default_factory is None  # undefined

        assert cls.__fields__["mandatory_with_default"].required is False
        assert cls.__fields__["mandatory_with_default"].allow_none is True
        assert cls.__fields__["mandatory_with_default"].default is None
        assert cls.__fields__["mandatory_with_default"].default_factory is None  # undefined

        assert cls.__fields__["mandatory_with_none"].required is False
        assert cls.__fields__["mandatory_with_none"].allow_none is True
        assert cls.__fields__["mandatory_with_none"].default is None
        assert cls.__fields__["mandatory_with_none"].default_factory is None  # undefined

        assert cls.__fields__["optional"].required is False
        assert cls.__fields__["optional"].allow_none is True
        assert cls.__fields__["optional"].default is None
        assert cls.__fields__["optional"].default_factory is None  # undefined

        assert cls.__fields__["optional_with_default"].required is False
        assert cls.__fields__["optional_with_default"].allow_none is True
        assert cls.__fields__["optional_with_default"].default is None
        assert cls.__fields__["optional_with_default"].default_factory is None  # undefined

        assert cls.__fields__["optional_with_none"].required is False
        assert cls.__fields__["optional_with_none"].allow_none is True
        assert cls.__fields__["optional_with_none"].default is None
        assert cls.__fields__["optional_with_none"].default_factory is None  # undefined

    @pytest.mark.parametrize("cls", [UseNoneModel, UseNoneSubModel, InheritedUseNoneModel])
    def test_initialization(self, cls: t.Type[UseNoneModel]) -> None:
        # We can build a model without providing values.
        # The initialized value will be the default value or `None` for optional values.
        # Note that the mandatory fields are not required anymore, and can be `None`.
        obj = cls()
        assert obj.mandatory is None
        assert obj.mandatory_with_default is None
        assert obj.mandatory_with_none is None
        assert obj.optional is None
        assert obj.optional_with_default is None
        assert obj.optional_with_none is None

        # If we convert the model to a dictionary, without `None` values,
        # we should have an empty dictionary.
        actual = obj.dict(exclude_none=True)
        expected = {}
        assert actual == expected

    @pytest.mark.parametrize("cls", [UseNoneModel, UseNoneSubModel, InheritedUseNoneModel])
    def test_validation(self, cls: t.Type[UseNoneModel]) -> None:
        # We can use `None` as a value for all fields.
        cls(mandatory=None)
        cls(mandatory_with_default=None)
        cls(mandatory_with_none=None)
        cls(optional=None)
        cls(optional_with_default=None)
        cls(optional_with_none=None)

        # We can validate a model with valid values.
        cls(
            mandatory=0.5,
            mandatory_with_default=0.2,
            mandatory_with_none=0.2,
            optional=0.5,
            optional_with_default=0.2,
            optional_with_none=0.2,
        )

        # We CANNOT validate a model with invalid values.
        with pytest.raises(ValidationError):
            cls(mandatory=2)

        with pytest.raises(ValidationError):
            cls(mandatory_with_default=2)

        with pytest.raises(ValidationError):
            cls(mandatory_with_none=2)

        with pytest.raises(ValidationError):
            cls(optional=2)

        with pytest.raises(ValidationError):
            cls(optional_with_default=2)

        with pytest.raises(ValidationError):
            cls(optional_with_none=2)
