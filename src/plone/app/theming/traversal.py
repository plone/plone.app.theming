import urllib

from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.registry.interfaces import IRegistry
from plone.resource.traversal import ResourceTraverser
from plone.resource.utils import queryResourceDirectory

from zope.component import getUtility

from interfaces import IThemeSettings


class ThemeTraverser(ResourceTraverser):
    """The theme traverser.

    Allows traveral to /++theme++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """

    name = THEME_RESOURCE_NAME

    def __init__(self, context, request=None):
        self.context = context

    def current_theme(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IThemeSettings)
        return settings.currentTheme

    def traverse(self, name, remaining):
        type = self.name

        if name == '':
            name = self.current_theme()

        # Note: also fixes possible unicode problems
        name = urllib.quote(name)

        res = queryResourceDirectory(type, name)
        if res is not None:
            return res

        raise NotFound
