import logging
import os.path
import z3c.jbot.metaconfigure

from zope.interface import implements
from zope.dottedname.resolve import resolve

from plone.resource.utils import queryResourceDirectory

from plone.app.theming.interfaces import IThemePlugin
from plone.app.theming.interfaces import THEME_RESOURCE_NAME

from plone.app.theming.plugins.browserlayer import schemata

logger = logging.getLogger(__name__)

class OverridesPlugin(object):
    """This plugin automatically registers a ``z3c.jbot`` style template
    overrides directory for the theme.
    
    By default, it looks for a directory ``overrides`` in the theme directory,
    and registers that with ``z3c.jbot`` using the default browser layer
    created by the ``browserlayer`` plugin.
    
    This directory can then contain template overrides using ``z3c.jbot``
    naming conventions, e.g. ``my.package.browser.some_template.pt`` will
    override the file ``some_template.pt`` in ``my.package.browser`` when
    the theme is in effect.
    
    The directory and layer can be overriden in the manifest if required::
        
        [theme:overrides]
        directory = template-overrides
        layer = my.package.interfaces.ISomeLayer
    
    The directory name is relative to the theme directory. The layer interface
    must already exist.
    """
    
    implements(IThemePlugin)
    
    dependencies = ('browserlayer',)
    
    registered = {}
    
    def onDiscovery(self, theme, settings, dependenciesSettings):
        res = queryResourceDirectory(THEME_RESOURCE_NAME, theme)
        if res is None:
            return
        
        directoryName = 'overrides'
        if 'directory' in settings:
            directoryName = settings['directory']
        
        if res.isDirectory(directoryName):
            
            layer = getattr(schemata, theme, None)
            
            if 'layer' in settings:
                layerName = settings['layer']
            
                try:
                    layer = resolve(layerName)
                except (ImportError, AttributeError,):
                    logger.warn("Could not import %s" % layerName)
                    return
            
            path = os.path.join(res.directory, directoryName)
            
            manager = z3c.jbot.metaconfigure.handler(path, layer)
            self.registered[theme] = manager
    
    def onCreated(self, theme, settings, dependenciesSettings):
        pass
    
    def onEnabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onDisabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onRequest(self, request, theme, settings, dependenciesSettings):
        pass
