# -*- coding: utf-8 -*-
from plone.app.theming.interfaces import IThemeSettings
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from zope.component import getUtility


class CustomCSSView(BrowserView):
    """
    Renders custom CSS stored in registry
    """

    def __call__(self):

        registry = getUtility(IRegistry)
        theme_settings = registry.forInterface(IThemeSettings, False)
        self.request.response.setHeader('Content-Type', 'text/css')
        custom_css = theme_settings.custom_css
        return custom_css
