from plone.resource.utils import queryResourceDirectory
from plone.resource.utils import iterDirectoriesOfType

from plone.app.theming.interfaces import THEME_RESOURCE_NAME

from plone.app.theming.utils import getCurrentTheme
from plone.app.theming.utils import isThemeEnabled

from plone.app.theming.plugins.utils import getPlugins
from plone.app.theming.plugins.utils import getPluginSettings

def onStartup(event):
    """Call onDiscovery() on each plugin for each theme on startup
    """

    plugins = getPlugins()

    for themeDirectory in iterDirectoriesOfType(THEME_RESOURCE_NAME):
        pluginSettings = getPluginSettings(themeDirectory, plugins)

        for name, plugin in plugins:
            plugin.onDiscovery(themeDirectory.__name__, pluginSettings[name], pluginSettings)

def onRequest(object, event):
    """Call onRequest() on each plugin for the eanbled theme on each request
    """

    request = event.request

    if not isThemeEnabled(request):
        return

    theme = getCurrentTheme()
    if theme is None:
        return

    themeDirectory = queryResourceDirectory(THEME_RESOURCE_NAME, theme)
    if themeDirectory is None:
        return

    plugins = getPlugins()
    pluginSettings = getPluginSettings(themeDirectory, plugins)

    for name, plugin in plugins:
        plugin.onRequest(request, theme, pluginSettings[name], pluginSettings)
