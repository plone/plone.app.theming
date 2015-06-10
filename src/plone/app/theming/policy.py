# -*- coding: utf-8 -*-
import Globals

from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.publisher.interfaces import IRequest

from plone.app.theming.interfaces import IThemingPolicy
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming import utils


def invalidateCache(settings, event):
    """Event handler for registry change"""
    utils.theming_policy().invalidateCache()


@implementer(IThemingPolicy)
class ThemingPolicy(object):

    # use static class attribute instead of _v_volatiles
    CACHE_STORAGE = {}

    def __init__(self, request):
        """Adapt IRequest.
        Do not call this class directly, always use a
        utils.theming_policy(request) adapter lookup.

        This enables overriding of the IThemingPolicy adapter
        via ZCML by integrators.

        When used as INoRequest adapter, returns the default policy.
        """
        if IRequest.providedBy(request):
            self.request = request
        else:
            self.request = None

    def getSettings(self):
        """Settings for current theme."""
        registry = queryUtility(IRegistry)
        if registry is None:
            return None
        try:
            settings = registry.forInterface(IThemeSettings, False)
        except KeyError:
            return None
        return settings

    def getCurrentTheme(self):
        """The name of the current theme."""
        settings = self.getSettings()
        if not settings.rules:
            return None
        if settings.currentTheme:
            return settings.currentTheme

        # BBB: If currentTheme isn't set, look for a theme with a rules file
        # matching that of the current theme
        for theme in utils.getAvailableThemes():
            if theme.rules == settings.rules:
                return theme.__name__

        return None

    def isThemeEnabled(self, settings=None):
        """Whether theming is enabled."""

        # Resolve DevelopmentMode late (i.e. not on import time) since it may
        # be set during import or test setup time
        DevelopmentMode = Globals.DevelopmentMode

        # Disable theming if the response sets a header
        if self.request.response.getHeader('X-Theme-Disabled'):
            return False

        # Check for diazo.off request parameter
        true_vals = ('1', 'y', 'yes', 't', 'true')
        if (DevelopmentMode and self.request.get(
                'diazo.off', '').lower() in true_vals):
            return False

        if not settings:
            settings = self.getSettings()
        if not settings.enabled or not settings.rules:
            return False

        server_url = self.request.get('SERVER_URL')
        proto, host = server_url.split('://', 1)
        host = host.lower()
        serverPort = self.request.get('SERVER_PORT')

        for hostname in settings.hostnameBlacklist or ():
            if host == hostname or host == ':'.join((hostname, serverPort)):
                return False

        return True

    def getCache(self, theme=None):
        """Managing the cache is a policy decision."""
        caches = self.getCacheStorage()
        key = self.getCacheKey(theme)
        cache = caches.get(key)
        if cache is None:
            cache = caches[key] = ThemeCache()
        return cache

    def getCacheKey(self, theme=None):
        if not theme:
            theme = self.getCurrentTheme()
        key = "%s::%s" % (getSite().absolute_url(), theme)
        return key

    def getCacheStorage(self):
        return self.__class__.CACHE_STORAGE

    def invalidateCache(self):
        """When our settings are changed, invalidate the cache on all zeo clients
        """
        self.__class__.CACHE_STORAGE = {}

    def get_theme(self):
        """Managing the theme cache is a plone.app.theming policy
        decision. Moved out out Products.CMFPlone."""
        cache = self.getCache()
        themeObj = cache.themeObj
        if not themeObj:
            theme = self.getCurrentTheme()
            themeObj = utils.getTheme(theme)
            self.set_theme(theme, themeObj)
        return themeObj

    def set_theme(self, themeName, themeObj):
        """Update the theme cache"""
        cache = self.getCache(themeName)
        cache.updateTheme(themeObj)


class ThemeCache(object):
    """Simple cache for the transform and theme
    """

    def __init__(self):
        self.transform = None
        self.expressions = None
        self.themeObj = None

    def updateTransform(self, transform):
        self.transform = transform

    def updateExpressions(self, expressions):
        self.expressions = expressions

    def updateTheme(self, themeObj):
        self.themeObj = themeObj
