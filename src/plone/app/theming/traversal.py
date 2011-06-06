from plone.resource.traversal import ResourceTraverser

from plone.app.theming.interfaces import THEME_RESOURCE_NAME

class ThemeTraverser(ResourceTraverser):
    """The theme traverser.

    Allows traveral to /++theme++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """

    name = THEME_RESOURCE_NAME
