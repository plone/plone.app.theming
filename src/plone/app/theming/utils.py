import Globals
import pkg_resources

from lxml import etree

from zope.site.hooks import getSite
from zope.component import getUtility
from zope.component import queryUtility
from zope.component import queryMultiAdapter
from zope.globalrequest import getRequest

from plone.subrequest import subrequest

from plone.resource.interfaces import IResourceDirectory
from plone.resource.utils import queryResourceDirectory
from plone.resource.manifest import extractManifestFromZipFile
from plone.resource.manifest import getAllResources
from plone.resource.manifest import getZODBResources
from plone.resource.manifest import MANIFEST_FILENAME

from plone.registry.interfaces import IRegistry

from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import MANIFEST_FORMAT
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import IThemeSettings

from plone.app.theming.theme import Theme
from plone.app.theming.plugins.utils import getPlugins
from plone.app.theming.plugins.utils import getPluginSettings

from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.Expressions import getEngine


class NetworkResolver(etree.Resolver):
    """Resolver for network urls
    """
    def resolve(self, system_url, public_id, context):
        if '://' in system_url and system_url != 'file:///__diazo__':
            return self.resolve_filename(system_url, context)


class PythonResolver(etree.Resolver):
    """Resolver for python:// paths
    """

    def resolve(self, system_url, public_id, context):
        if not system_url.lower().startswith('python://'):
            return None
        filename = resolvePythonURL(system_url)
        return self.resolve_filename(filename, context)


def resolvePythonURL(url):
    """Resolve the python resource url to it's path

    This can resolve python://dotted.package.name/file/path URLs to paths.
    """
    assert url.lower().startswith('python://')
    spec = url[9:]
    package, resource_name = spec.split('/', 1)
    return pkg_resources.resource_filename(package, resource_name)


class InternalResolver(etree.Resolver):
    """Resolver for internal absolute and relative paths (excluding protocol).
    If the path starts with a /, it will be resolved relative to the Plone
    site navigation root.
    """

    def resolve(self, system_url, public_id, context):
        request = getRequest()
        if request is None:
            return None

        # Ignore URLs with a scheme
        if '://' in system_url:
            return None

        # Ignore the special 'diazo:' resolvers
        if system_url.startswith('diazo:'):
            return None

        context = findContext(request)
        portalState = queryMultiAdapter(
            (context, request), name=u"plone_portal_state")

        if portalState is None:
            root = None
        else:
            root = portalState.navigation_root()

        response = subrequest(system_url, root=root)
        if response.status != 200:
            return None
        result = response.getBody()
        content_type = response.headers.get('content-type')
        encoding = None
        if content_type is not None and ';' in content_type:
            content_type, encoding = content_type.split(';', 1)
        if encoding is None:
            encoding = 'utf-8'
        else:
            # e.g. charset=utf-8
            encoding = encoding.split('=', 1)[1].strip()
        result = result.decode(encoding).encode('ascii', 'xmlcharrefreplace')

        if content_type in ('text/javascript', 'application/x-javascript'):
            result = ''.join([
                '<html><body><script type="text/javascript">',
                result,
                '</script></body></html>',
                ])
        elif content_type == 'text/css':
            result = ''.join([
                '<html><body><style type="text/css">',
                result,
                '</style></body></html>',
                ])

        return self.resolve_string(result, context)


def getPortal():
    """Return the portal object
    """
    request = getRequest()
    context = findContext(request)
    portalState = queryMultiAdapter(
        (context, request), name=u"plone_portal_state")
    if portalState is None:
        return None
    return portalState.portal()


def findContext(request):
    """Find the context from the request
    """
    published = request.get('PUBLISHED', None)
    context = getattr(published, '__parent__', None)
    if context is None:
        context = request.PARENTS[0]
    return context


def expandAbsolutePrefix(prefix):
    """Prepend the Plone site URL to the prefix if it starts with /
    """
    if not prefix or not prefix.startswith('/'):
        return prefix
    portal = getPortal()
    if portal is None:
        return ''
    path = portal.absolute_url_path()
    if path and path.endswith('/'):
        path = path[:-1]
    return path + prefix


def getOrCreatePersistentResourceDirectory():
    """Obtain the 'theme' persistent resource directory, creating it if
    necessary.
    """

    persistentDirectory = getUtility(IResourceDirectory, name="persistent")
    if THEME_RESOURCE_NAME not in persistentDirectory:
        persistentDirectory.makeDirectory(THEME_RESOURCE_NAME)

    return persistentDirectory[THEME_RESOURCE_NAME]


def createExpressionContext(context, request):
    """Create an expression context suitable for evaluating parameter
    expressions.
    """

    contextState = queryMultiAdapter(
        (context, request), name=u"plone_context_state")
    portalState = queryMultiAdapter(
        (context, request), name=u"plone_portal_state")

    data = {
        'context': context,
        'request': request,
        'portal': portalState.portal(),
        'context_state': contextState,
        'portal_state': portalState,
        'nothing': None,
    }

    return getEngine().getContext(data)


def compileExpression(text):
    """Compile the given expression. The returned value is suitable for
    caching in a volatile attribute
    """
    return getEngine().compile(text.strip())


def isValidThemeDirectory(directory):
    """Determine if the given plone.resource directory is a valid theme
    directory
    """
    return directory.isFile(MANIFEST_FILENAME) or \
           directory.isFile(RULE_FILENAME)


def extractThemeInfo(zipfile):
    """Return an ITheme based on the information in the given zipfile.

    Will throw a ValueError if the theme directory does not contain a single
    top level directory or the rules file cannot be found.
    """

    resourceName, manifestDict = extractManifestFromZipFile(
        zipfile, MANIFEST_FORMAT)

    rulesFile = None
    absolutePrefix = '/++%s++%s' % (THEME_RESOURCE_NAME, resourceName)
    title = None
    description = None
    parameters = {}
    doctype = ""

    if manifestDict is not None:
        rulesFile = manifestDict.get('rules', rulesFile)
        absolutePrefix = manifestDict['prefix'] or absolutePrefix
        title = manifestDict.get('title', None)
        description = manifestDict.get('title', None)
        parameters = manifestDict.get('parameters', {})
        doctype = manifestDict.get('doctype', "")

    if not rulesFile:
        try:
            zipfile.getinfo("%s/%s" % (resourceName, RULE_FILENAME,))
        except KeyError:
            raise ValueError("Could not find theme name and rules file")
        rulesFile = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, resourceName,
                                       RULE_FILENAME,)

    return Theme(resourceName, rulesFile,
            title=title,
            description=description,
            absolutePrefix=absolutePrefix,
            parameterExpressions=parameters,
            doctype=doctype,
        )


def getAvailableThemes():
    """Get a list of all ITheme's available in resource directories.
    """

    resources = getAllResources(MANIFEST_FORMAT, filter=isValidThemeDirectory)
    themes = []
    for name, manifest in resources.items():
        title = name.capitalize().replace('-', ' ').replace('.', ' ')
        description = None
        rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, name, RULE_FILENAME,)
        prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME, name,)
        params = {}
        doctype = ""

        if manifest is not None:
            title = manifest['title'] or title
            description = manifest['description'] or description
            rules = manifest['rules'] or rules
            prefix = manifest['prefix'] or prefix
            params = manifest['parameters'] or params
            doctype = manifest['doctype'] or doctype

        if isinstance(rules, str):
            rules = rules.decode('utf-8')
        if isinstance(prefix, str):
            prefix = prefix.decode('utf-8')

        themes.append(Theme(name, rules,
                    title=title,
                    description=description,
                    absolutePrefix=prefix,
                    parameterExpressions=params,
                    doctype=doctype,
                )
            )

    themes.sort(key=lambda x: x.title)
    return themes


def getZODBThemes():
    """Get a list of ITheme's stored in the ZODB.
    """

    resources = getZODBResources(MANIFEST_FORMAT, filter=isValidThemeDirectory)
    themes = []
    for name, manifest in resources.items():
        title = name.capitalize().replace('-', ' ').replace('.', ' ')
        description = None
        rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, name, RULE_FILENAME,)
        prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME, name,)
        params = {}
        doctype = ""

        if manifest is not None:
            title = manifest['title'] or title
            description = manifest['description'] or description
            rules = manifest['rules'] or rules
            prefix = manifest['prefix'] or prefix
            params = manifest['parameters'] or params
            doctype = manifest['doctype'] or doctype

        themes.append(Theme(name, rules,
                            title=title,
                            description=description,
                            absolutePrefix=prefix,
                            parameterExpressions=params,
                            doctype=doctype,
                            )
            )

    themes.sort(key=lambda x: x.title)
    return themes


def getCurrentTheme():
    """Get the name of the currently enabled theme
    """
    settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
    if not settings.rules:
        return None

    if settings.currentTheme:
        return settings.currentTheme

    # BBB: If currentTheme isn't set, look for a theme with a rules file
    # matching that of the current theme
    for theme in getAvailableThemes():
        if theme.rules == settings.rules:
            return theme.__name__

    return None


def isThemeEnabled(request, settings=None):
    """Determine if a theme is enabled for the given request
    """

    # Resolve DevelopmentMode late (i.e. not on import time) since it may
    # be set during import or test setup time
    DevelopmentMode = Globals.DevelopmentMode

    # Disable theming if the response sets a header
    if request.response.getHeader('X-Theme-Disabled'):
        return False

    # Check for diazo.off request parameter
    if (DevelopmentMode and
        request.get('diazo.off', '').lower() in ('1', 'y', 'yes', 't', 'true')
    ):
        return False

    if settings is None:
        registry = queryUtility(IRegistry)
        if registry is None:
            return False

        settings = registry.forInterface(IThemeSettings, False)

    if not settings.enabled or not settings.rules:
        return False

    base1 = request.get('BASE1')
    _, base1 = base1.split('://', 1)
    host = base1.lower()
    serverPort = request.get('SERVER_PORT')

    for hostname in settings.hostnameBlacklist or ():
        if host == hostname or host == "%s:%s" % (hostname, serverPort):
            return False

    return True


def applyTheme(theme):
    """Apply an ITheme
    """

    settings = getUtility(IRegistry).forInterface(IThemeSettings, False)

    plugins = None
    themeDirectory = None
    pluginSettings = None
    currentTheme = getCurrentTheme()

    if currentTheme is not None:
        themeDirectory = queryResourceDirectory(
            THEME_RESOURCE_NAME, currentTheme)
        if themeDirectory is not None:
            plugins = getPlugins()
            pluginSettings = getPluginSettings(themeDirectory, plugins)

    if theme is None:

        settings.currentTheme = None
        settings.rules = None
        settings.absolutePrefix = None
        settings.parameterExpressions = {}
        settings.doctype = ""

        if pluginSettings is not None:
            for name, plugin in plugins:
                plugin.onDisabled(currentTheme, pluginSettings[name],
                                  pluginSettings)

    else:

        if isinstance(theme.rules, str):
            theme.rules = theme.rules.decode('utf-8')

        if isinstance(theme.absolutePrefix, str):
            theme.absolutePrefix = theme.absolutePrefix.decode('utf-8')

        if isinstance(theme.__name__, str):
            theme.__name__ = theme.__name__.decode('utf-8')

        settings.currentTheme = theme.__name__
        settings.rules = theme.rules
        settings.absolutePrefix = theme.absolutePrefix
        settings.parameterExpressions = theme.parameterExpressions
        settings.doctype = theme.doctype

        if pluginSettings is not None:
            for name, plugin in plugins:
                plugin.onDisabled(currentTheme, pluginSettings[name],
                                  pluginSettings)
                plugin.onEnabled(theme, pluginSettings[name], pluginSettings)
