from datetime import timedelta
from typing import Any, Dict, List, Optional, Sequence, Set, Union

from pydantic import BaseModel, StrictBool, StrictInt, StrictStr, ValidationError, field_validator, model_validator


class LoadConfig(BaseModel):
    authjwt_token_location: Optional[Set[StrictStr]] = {"headers"}
    authjwt_secret_key: Optional[StrictStr] = None
    authjwt_public_key: Optional[StrictStr] = None
    authjwt_private_key: Optional[StrictStr] = None
    authjwt_algorithm: Optional[StrictStr] = "HS256"
    authjwt_decode_algorithms: Optional[List[StrictStr]] = None
    authjwt_decode_leeway: Optional[Union[StrictInt, timedelta]] = 0
    authjwt_encode_issuer: Optional[StrictStr] = None
    authjwt_decode_issuer: Optional[StrictStr] = None
    authjwt_decode_audience: Optional[Union[StrictStr, Sequence[StrictStr]]] = None
    authjwt_denylist_enabled: Optional[StrictBool] = False
    authjwt_denylist_token_checks: Optional[Set[StrictStr]] = {"access", "refresh"}
    authjwt_header_name: Optional[StrictStr] = "Authorization"
    authjwt_header_type: Optional[StrictStr] = "Bearer"
    authjwt_access_token_expires: Optional[Union[StrictBool, StrictInt, timedelta]] = timedelta(minutes=15)
    authjwt_refresh_token_expires: Optional[Union[StrictBool, StrictInt, timedelta]] = timedelta(days=30)
    # option for create cookies
    authjwt_access_cookie_key: Optional[StrictStr] = "access_token_cookie"
    authjwt_refresh_cookie_key: Optional[StrictStr] = "refresh_token_cookie"
    authjwt_access_cookie_path: Optional[StrictStr] = "/"
    authjwt_refresh_cookie_path: Optional[StrictStr] = "/"
    authjwt_cookie_max_age: Optional[StrictInt] = None
    authjwt_cookie_domain: Optional[StrictStr] = None
    authjwt_cookie_secure: Optional[StrictBool] = False
    authjwt_cookie_samesite: Optional[StrictStr] = None
    # option for double submit csrf protection
    authjwt_cookie_csrf_protect: Optional[StrictBool] = True
    authjwt_access_csrf_cookie_key: Optional[StrictStr] = "csrf_access_token"
    authjwt_refresh_csrf_cookie_key: Optional[StrictStr] = "csrf_refresh_token"
    authjwt_access_csrf_cookie_path: Optional[StrictStr] = "/"
    authjwt_refresh_csrf_cookie_path: Optional[StrictStr] = "/"
    authjwt_access_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
    authjwt_refresh_csrf_header_name: Optional[StrictStr] = "X-CSRF-Token"
    authjwt_csrf_methods: Optional[Set[StrictStr]] = {"POST", "PUT", "PATCH", "DELETE"}

    @field_validator("authjwt_access_token_expires")
    def validate_access_token_expires(
        cls, v: Optional[Union[StrictBool, StrictInt, timedelta]]
    ) -> Optional[Union[StrictBool, StrictInt, timedelta]]:
        if v is True:
            raise ValueError("The 'authjwt_access_token_expires' only accept value False (bool)")
        return v

    @field_validator("authjwt_refresh_token_expires")
    def validate_refresh_token_expires(
        cls, v: Optional[Union[StrictBool, StrictInt, timedelta]]
    ) -> Optional[Union[StrictBool, StrictInt, timedelta]]:
        if v is True:
            raise ValueError("The 'authjwt_refresh_token_expires' only accept value False (bool)")
        return v

    @field_validator("authjwt_cookie_samesite")
    def validate_cookie_samesite(cls, v: Optional[StrictStr]) -> Optional[StrictStr]:
        if v not in ["strict", "lax", "none"]:
            raise ValueError("The 'authjwt_cookie_samesite' must be between 'strict', 'lax', 'none'")
        return v

    @model_validator(mode="before")
    def check_type_validity(cls, values: Dict[str, Any]) -> Dict[str, Any]:
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

    class Config:
        str_min_length = 1
        str_strip_whitespace = True
