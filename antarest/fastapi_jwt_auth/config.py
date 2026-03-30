from collections.abc import Sequence
from datetime import timedelta
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationError,
    field_validator,
    model_validator,
)


class LoadConfig(BaseModel):
    authjwt_token_location: set[StrictStr] | None = {"headers"}
    authjwt_secret_key: StrictStr | None = None
    authjwt_public_key: StrictStr | None = None
    authjwt_private_key: StrictStr | None = None
    authjwt_algorithm: StrictStr | None = "HS256"
    authjwt_decode_algorithms: list[StrictStr] | None = None
    authjwt_decode_leeway: StrictInt | timedelta | None = 0
    authjwt_encode_issuer: StrictStr | None = None
    authjwt_decode_issuer: StrictStr | None = None
    authjwt_decode_audience: StrictStr | Sequence[StrictStr] | None = None
    authjwt_denylist_enabled: StrictBool | None = False
    authjwt_denylist_token_checks: set[StrictStr] | None = {"access", "refresh"}
    authjwt_header_name: StrictStr | None = "Authorization"
    authjwt_header_type: StrictStr | None = "Bearer"
    authjwt_access_token_expires: StrictBool | StrictInt | timedelta | None = timedelta(minutes=15)
    authjwt_refresh_token_expires: StrictBool | StrictInt | timedelta | None = timedelta(days=30)
    # option for create cookies
    authjwt_access_cookie_key: StrictStr | None = "access_token_cookie"
    authjwt_refresh_cookie_key: StrictStr | None = "refresh_token_cookie"
    authjwt_access_cookie_path: StrictStr | None = "/"
    authjwt_refresh_cookie_path: StrictStr | None = "/"
    authjwt_cookie_max_age: StrictInt | None = None
    authjwt_cookie_domain: StrictStr | None = None
    authjwt_cookie_secure: StrictBool | None = False
    authjwt_cookie_samesite: StrictStr | None = None
    # option for double submit csrf protection
    authjwt_cookie_csrf_protect: StrictBool | None = True
    authjwt_access_csrf_cookie_key: StrictStr | None = "csrf_access_token"
    authjwt_refresh_csrf_cookie_key: StrictStr | None = "csrf_refresh_token"
    authjwt_access_csrf_cookie_path: StrictStr | None = "/"
    authjwt_refresh_csrf_cookie_path: StrictStr | None = "/"
    authjwt_access_csrf_header_name: StrictStr | None = "X-CSRF-Token"
    authjwt_refresh_csrf_header_name: StrictStr | None = "X-CSRF-Token"
    authjwt_csrf_methods: set[StrictStr] | None = {"POST", "PUT", "PATCH", "DELETE"}

    @field_validator("authjwt_access_token_expires")
    def validate_access_token_expires(
        cls, v: StrictBool | StrictInt | timedelta | None
    ) -> StrictBool | StrictInt | timedelta | None:
        if v is True:
            raise ValueError("The 'authjwt_access_token_expires' only accept value False (bool)")
        return v

    @field_validator("authjwt_refresh_token_expires")
    def validate_refresh_token_expires(
        cls, v: StrictBool | StrictInt | timedelta | None
    ) -> StrictBool | StrictInt | timedelta | None:
        if v is True:
            raise ValueError("The 'authjwt_refresh_token_expires' only accept value False (bool)")
        return v

    @field_validator("authjwt_cookie_samesite")
    def validate_cookie_samesite(cls, v: StrictStr | None) -> StrictStr | None:
        if v not in ["strict", "lax", "none"]:
            raise ValueError("The 'authjwt_cookie_samesite' must be between 'strict', 'lax', 'none'")
        return v

    @model_validator(mode="before")
    def check_type_validity(cls, values: dict[str, Any]) -> dict[str, Any]:
        for _ in values.get("authjwt_csrf_methods", []):
            if _.upper() not in ["POST", "PUT", "PATCH", "DELETE"]:
                raise ValidationError(
                    f"The 'authjwt_csrf_methods' must be between http request methods and it's {_.upper()}"
                )

        for _ in values.get("authjwt_cookie_samesite", []):
            if _ not in ["strict", "lax", "none"]:
                raise ValidationError(
                    f"The 'authjwt_cookie_samesite' must be between 'strict', 'lax', 'none' and it's {_}"
                )

        for _ in values.get("authjwt_token_location", []):
            if _ not in ["headers", "cookies"]:
                raise ValidationError(
                    f"The 'authjwt_token_location' must be between 'headers' or 'cookies' and it's {_}"
                )

        return values

    model_config = ConfigDict(str_min_length=1, str_strip_whitespace=True)
