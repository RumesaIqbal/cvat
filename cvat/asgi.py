# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

"""
ASGI config for CVAT project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.core.handlers.asgi import ASGIHandler

import cvat.utils.remote_debugger as debug

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cvat.settings.development")

application = get_asgi_application()


if debug.is_debugging_enabled():

    class DebuggerApp(ASGIHandler):
        """
        Support for VS code debugger
        """

        def __init__(self) -> None:
            super().__init__()
            self.__debugger = debug.RemoteDebugger()

        async def handle(self, *args, **kwargs):
            self.__debugger.attach_current_thread()
            return await super().handle(*args, **kwargs)

    application = DebuggerApp()


class CVATASGI:
    """
    Entry point that sends websocket connections to the annotation
    statistics endpoint and everything else to the Django ASGI handler.
    """

    def __init__(self, http_app):
        self.http_app = http_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Imported lazily: this module is loaded by uvicorn before Django
            # finishes setting up, so importing the database-backed handler
            # eagerly fails with AppRegistryNotReady.
            from cvat.apps.test.asgi import handle_websocket

            await handle_websocket(scope, receive, send)
        else:
            await self.http_app(scope, receive, send)


application = CVATASGI(application)
