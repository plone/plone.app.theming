# -*- coding: utf-8 -*-
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import theming_policy
from plone.resource.traversal import ResourceTraverser
from plone.resource.utils import queryResourceDirectory
from zExceptions import NotFound
import urllib


class ThemeTraverser(ResourceTraverser):
    """The theme traverser.

    Allows traveral to /++theme++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """

    name = THEME_RESOURCE_NAME

    def __init__(self, context, request=None):
        self.context = context

    def current_theme(self):
        return theming_policy(self.request).getCurrentTheme()

    def traverse(self, name, remaining):
        if name == '':
            name = self.current_theme()

        # Note: also fixes possible unicode problems
        name = urllib.quote(name)

        res = queryResourceDirectory(self.name, name)
        if res is not None:
            return res

        raise NotFound
