from zope.interface import implements
from plone.app.theming.interfaces import IThemePlugin

class JavascriptPlugin(object):
    implements(IThemePlugin)
    
    dependencies = ()
    
    def onDiscovery(self, theme, settings, dependenciesSettings):
        pass
    
    def onCreation(self, theme, settings, dependenciesSettings):
        pass
    
    def onEnabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onDisabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onRequest(self, request, theme, settings, dependenciesSettings):
        pass
