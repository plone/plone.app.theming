from zope.interface import implements
from plone.app.theming.interfaces import IThemePlugin

class CSSPlugin(object):
    implements(IThemePlugin)
    
    dependencies = ()
    
    def onDiscovery(self, theme, settings, dependenciesSettings):
        pass
    
    def onCreated(self, theme, settings, dependenciesSettings):
        pass
    
    def onEnabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onDisabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onRequest(self, request, theme, settings, dependenciesSettings):
        pass
