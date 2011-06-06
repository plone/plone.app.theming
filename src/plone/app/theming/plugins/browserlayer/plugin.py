import logging

from zope.interface import implements
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.interface.interface import InterfaceClass

from zope.dottedname.resolve import resolve

from plone.app.theming.interfaces import IThemePlugin

from plone.app.theming.plugins.browserlayer import schemata

logger = logging.getLogger(__name__)

class BrowserLayerPlugin(object):
    """This plugin dynamically creates a browser layer marker interface for
    this theme and applies it to the request when the theme is enabled.

    Name: ``plone.app.theming.plugins.browserlayer.schemata.<theme>``.

    Additional layers to apply may be listed in the manifest::

        [theme:browserlayer]
        layer1 = my.package.interfaces.ISomeLayer
        layer2 = my.package.interfaces.ISomeOtherLayer

    The left hand side (layer1, layer2 above) must be unique, but otherwise
    doesn't matter.
    """

    implements(IThemePlugin)

    dependencies = ()

    def onDiscovery(self, theme, settings, dependenciesSettings):
        layer = InterfaceClass(theme, (Interface,), __module__=schemata.__name__)
        setattr(schemata, theme, layer)

    def onCreated(self, theme, settings, dependenciesSettings):
        pass

    def onEnabled(self, theme, settings, dependenciesSettings):
        pass

    def onDisabled(self, theme, settings, dependenciesSettings):
        pass

    def onRequest(self, request, theme, settings, dependenciesSettings):

        # Apply the dynamic schema

        layer = getattr(schemata, theme, None)
        if layer is None:
            return

        alsoProvides(request, layer)

        # Apply other schemata listed in settings
        for name in settings.values():
            try:
                layer = resolve(name)
                alsoProvides(request, layer)
            except (ImportError, AttributeError,):
                logger.warn("Could not import %s" % name)
