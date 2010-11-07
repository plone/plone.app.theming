from zope.component import queryUtility
from plone.registry.interfaces import IRegistry

from plone.app.theming.interfaces import IThemeSettings

def setHeader(object, event):
    """Set a header X-Theme-Enabled in the request if theming is enabled.

    This is useful for checking in things like the portal_css/portal_javascripts
    registries.
    """
    
    request = event.request
    
    registry = queryUtility(IRegistry)
    if registry is None:
        return
    
    settings = None
    try:
        settings = registry.forInterface(IThemeSettings)
    except KeyError:
        return
    
    if not settings.enabled:
        return
    
    request.environ['HTTP_X_THEME_ENABLED'] = True
