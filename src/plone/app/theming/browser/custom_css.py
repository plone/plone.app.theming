# -*- coding: utf-8 -*-
from plone.app.theming.interfaces import IThemeSettings
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from zope.component import getUtility

import dateutil
import time
import wsgiref

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
        dt = theme_settings.custom_css_timestamp
        # If the datetime object is timezone-naive, it is assumed to be local time.
        if dt.tzinfo is not None:
            dt = dt.astimezone(dateutil.tz.tzlocal())
        # Format a Python datetime object as an RFC1123 date.
        self.request.response.setHeader(
            'Last-Modified',
            wsgiref.handlers.format_date_time(time.mktime(dt.timetuple())),
        )
        return theme_settings.custom_css
