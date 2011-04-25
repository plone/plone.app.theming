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

class JbotPlugin(object):
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
            layerName = "%s.%s" % (schemata.__name__, theme,)
            if 'layer' in settings:
                layerName = settings['layer']
            
            try:
                layer = resolve(layerName)
            except (ImportError, AttributeError,):
                logger.warn("Could not import %s" % layer)
            else:
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
