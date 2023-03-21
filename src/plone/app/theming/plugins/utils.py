from configparser import ConfigParser
from plone.app.theming.interfaces import IThemePlugin
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.memoize.ram import cache
from plone.resource.manifest import MANIFEST_FILENAME
from zope.component import getUtilitiesFor


def pluginsCacheKey(fun):
    return len(list(getUtilitiesFor(IThemePlugin)))


def pluginSettingsCacheKey(fun, themeDirectory, plugins=None):
    return themeDirectory.__name__, len(plugins)


def sortDependencies(plugins):
    """Topological sort"""
    queue = []
    waiting = {}  # (n,p) -> [remaining deps]

    for n, p in plugins:
        if p.dependencies:
            waiting[(n, p)] = list(p.dependencies)
        else:
            queue.append((n, p))

    while queue:
        n, p = queue.pop()
        yield (n, p)

        for (nw, pw), deps in [x for x in waiting.items()]:
            if n in deps:
                deps.remove(n)

            if not deps:
                queue.append((nw, pw))
                del waiting[(nw, pw)]

    if waiting:
        raise ValueError(f"Could not resolve dependencies for: {waiting:s}")


@cache(pluginsCacheKey)
def getPlugins():
    """Get all registered plugins topologically sorted"""
    plugins = []

    for name, plugin in getUtilitiesFor(IThemePlugin):
        plugins.append(
            (
                name,
                plugin,
            )
        )

    return list(sortDependencies(plugins))


@cache(pluginSettingsCacheKey)
def getPluginSettings(themeDirectory, plugins=None):
    """Given an IResourceDirectory for a theme, return the settings for the
    given list of plugins (or all plugins, if not given) provided as a list
    of (name, plugin) pairs.

    Returns a dict of dicts, with the outer dict having plugin names as keys
    and containing plugins settings (key/value pairs) as values.
    """
    if plugins is None:
        plugins = getPlugins()

    manifestContents = {}

    if themeDirectory.isFile(MANIFEST_FILENAME):
        parser = ConfigParser()
        fp = themeDirectory.openFile(MANIFEST_FILENAME)
        try:
            parser.read_string(fp.read().decode())
            for section in parser.sections():
                manifestContents[section] = {}
                for name, value in parser.items(section):
                    manifestContents[section][name] = value
        finally:
            try:
                fp.close()
            except AttributeError:
                pass

    pluginSettings = {}
    for name, plugin in plugins:
        pluginSettings[name] = manifestContents.get(
            f"{THEME_RESOURCE_NAME:s}:{name:s}", {}
        )
    return pluginSettings
