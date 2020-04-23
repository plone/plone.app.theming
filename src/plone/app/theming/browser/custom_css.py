# -*- coding: utf-8 -*-
from plone.app.theming.interfaces import IThemeSettings
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from zope.component import getUtility
from plone.app.caching.operations.utils import formatDateTime


class CustomCSSView(BrowserView):
    """
    Renders custom CSS stored in registry
    """

    def __call__(self):

        registry = getUtility(IRegistry)
        theme_settings = registry.forInterface(IThemeSettings, False)
        self.request.response.setHeader(
            'Content-Type',
            'text/css; charset=utf-8',
        )
        self.request.response.setHeader(
            'Last-Modified',
            formatDateTime(theme_settings.custom_css_timestamp),
        )
        custom_css = theme_settings.custom_css
        return custom_css
