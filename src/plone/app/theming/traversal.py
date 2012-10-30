import urllib
from zope.interface import implements
from plone.resource.traversal import ResourceTraverser

from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.browser import BrowserPage
from zope.security import checkPermission

from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory

from zope.component import getUtility

from interfaces import IThemeSettings
from plone.app.theming.interfaces import FRAGMENTS_DIRECTORY
from plone.app.theming.utils import isThemeEnabled, getCurrentTheme

from zExceptions import NotFound
from zExceptions import Unauthorized

from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.CMFCore.utils import getToolByName


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


class FragmentView(BrowserPage):
    """View class for template-based views defined in the theme.
    When you traverse to ``..../@@theme-fragment/foobar`` to render the view
    defined in ``fragments/foobar.pt`` in the theme, this becomes the ``view``.
    """

    def __init__(self, context, request, name, permission, template):
        super(FragmentView, self).__init__(context, request)
        self.__name__ = name
        self.permission = permission
        self.template = template

    def __call__(self, *args, **kwargs):
        if not checkPermission(self.permission, self.context):
            raise Unauthorized()

        portal_url = getToolByName(self.context, 'portal_url')

        zpt = ZopePageTemplate(self.__name__, text=self.template)
        boundNames = {
                'context': self.context,
                'request': self.request,
                'view': self,
                'portal_url': portal_url(),
                'portal': portal_url.getPortalObject(),
            }
        zpt = zpt.__of__(self.context)
        try:
            return zpt._exec(boundNames, args, kwargs)
        except NotFound, e:
            # We don't want 404's for these - they are programming errors
            raise Exception(e)


class ThemeFragment(BrowserPage):
    """Implements the ``@@theme-fragment`` traversal view. This allows you to
    traverse to ``.../@@theme-fragment/foobar`` to render as a view the template
    found in ``fragments/foobar.pt`` in the currently active theme, either
    in a URL (publish traversal) or in TAL (path traversal).

    Will raise ``KeyError`` (path traversal) or ``NotFound`` (publish
    traversal) if:

    * No valid theme is active
    * The theme is currently disabled
    * No ``.pt`` file exists
    * The ``.pt`` file is configured in a ``views.cfg`` file to be limited
      to a specific type of context (by interface or class), and the current
      context does not confirm to this type

    Will raise ``Unauthorized`` if the ``.pt`` file is configured in a
    ``views.cfg`` file to require a specific permission, and the current
    user does not have this permission.
    """
    implements(IPublishTraverse)

    def publishTraverse(self, request, name):
        try:
            return self[name]
        except KeyError:
            raise NotFound(self, name, request)

    def __getitem__(self, name):
        # Make sure a theme is enabled
        if not isThemeEnabled(self.request):
            raise KeyError(name)

        # Check if there is views/<name>.pt in the theme, if not raise
        currentTheme = getCurrentTheme()
        if currentTheme is None:
            raise KeyError(name)

        themeDirectory = queryResourceDirectory(THEME_RESOURCE_NAME, currentTheme)
        if themeDirectory is None:
            raise KeyError(name)

        templatePath = "%s/%s.pt" % (FRAGMENTS_DIRECTORY, name,)
        if not themeDirectory.isFile(templatePath):
            raise KeyError(name)

        template = themeDirectory.readFile(templatePath)

        # Now disable the theme so we don't double-transform
        self.request.response.setHeader('X-Theme-Disabled', '1')

        return FragmentView(self.context, self.request, name, 'zope.Public', template)