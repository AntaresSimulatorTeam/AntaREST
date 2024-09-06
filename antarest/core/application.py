from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter, FastAPI


@dataclass(frozen=True)
class AppBuildContext:
    """
    Base elements of the application, for use at construction time:
    - app: the actual fastapi application, where middlewares, exception handlers, etc. may be added
    - api_root: the route under which all API and WS endpoints must be registered

    API routes should not be added straight to app, but under api_root instead,
    so that they are correctly prefixed if needed (/api for standalone mode).

    Warning: the inclusion of api_root must happen AFTER all subroutes
    have been registered, hence the build method.
    """

    app: FastAPI
    api_root: APIRouter

    def build(self) -> FastAPI:
        """
        Finalizes the app construction by including the API route.
        Must be performed AFTER all subroutes have been added.
        """
        self.app.include_router(self.api_root)
        return self.app


def create_app_ctxt(app: FastAPI, api_root: Optional[APIRouter] = None) -> AppBuildContext:
    if not api_root:
        api_root = APIRouter()
    return AppBuildContext(app, api_root)
