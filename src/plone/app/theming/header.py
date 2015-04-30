# -*- coding: utf-8 -*-
from plone.app.theming.utils import isThemeEnabled


def setHeader(object, event):
    """Set a header X-Theme-Enabled in the request if theming is enabled.

    This is useful for checking in things like the portal_css/portal_
    javascripts registries.
    """

    request = event.request

    if isThemeEnabled(request):
        request.environ['HTTP_X_THEME_ENABLED'] = True
