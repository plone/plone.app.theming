import Globals

import pkg_resources

from StringIO import StringIO
from ConfigParser import SafeConfigParser

from urlparse import urlsplit

from lxml import etree

from diazo.compiler import compile_theme
from diazo.compiler import quote_param

from zope.component import getUtility
from zope.component import queryUtility
from zope.component import queryMultiAdapter
from zope.globalrequest import getRequest

from plone.subrequest import subrequest

from plone.resource.interfaces import IResourceDirectory
from plone.resource.utils import queryResourceDirectory
from plone.resource.utils import cloneResourceDirectory
from plone.resource.manifest import getManifest
from plone.resource.manifest import extractManifestFromZipFile
from plone.resource.manifest import getAllResources
from plone.resource.manifest import getZODBResources
from plone.resource.manifest import MANIFEST_FILENAME

from plone.registry.interfaces import IRegistry

from plone.i18n.normalizer.interfaces import IURLNormalizer

from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import MANIFEST_FORMAT
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import IThemeSettings

from plone.app.theming.theme import Theme
from plone.app.theming.plugins.utils import getPlugins
from plone.app.theming.plugins.utils import getPluginSettings

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

        if not system_url.startswith('/'):  # only for relative urls
            root_path = root.getPhysicalPath()
            context_path = context.getPhysicalPath()[len(root_path):]
            if len(context_path) == 0:
                system_url = '/' + system_url
            else:
                system_url = '/%s/%s' % ('/'.join(context_path), system_url)

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


def extractThemeInfo(zipfile, checkRules=True):
    """Return an ITheme based on the information in the given zipfile.

    Will throw a ValueError if the theme directory does not contain a single
    top level directory or the rules file cannot be found.

    Set checkRules=False to disable the rules check.
    """

    resourceName, manifestDict = extractManifestFromZipFile(zipfile, MANIFEST_FORMAT)

    rulesFile = None
    absolutePrefix = '/++%s++%s' % (THEME_RESOURCE_NAME, resourceName)
    title = None
    description = None
    parameters = {}
    doctype = ""
    preview = None

    if manifestDict is not None:
        rulesFile = manifestDict.get('rules', rulesFile)
        absolutePrefix = manifestDict['prefix'] or absolutePrefix
        title = manifestDict.get('title', None)
        description = manifestDict.get('title', None)
        parameters = manifestDict.get('parameters', {})
        doctype = manifestDict.get('doctype', "")
        preview = manifestDict.get('preview', None)

    if not rulesFile:
        if checkRules:
            try:
                zipfile.getinfo("%s/%s" % (resourceName, RULE_FILENAME,))
            except KeyError:
                raise ValueError("Could not find theme name and rules file")
        rulesFile = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, resourceName, RULE_FILENAME,)

    return Theme(resourceName, rulesFile,
            title=title,
            description=description,
            absolutePrefix=absolutePrefix,
            parameterExpressions=parameters,
            doctype=doctype,
            preview=preview,
        )


def getTheme(name, manifest=None, resources=None):
    if manifest is None:
        if resources is None:
            resources = getAllResources(
                MANIFEST_FORMAT, filter=isValidThemeDirectory)
        if name not in resources:
            return None
        manifest = resources[name]
    title = name.capitalize().replace('-', ' ').replace('.', ' ')
    description = None
    rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, name, RULE_FILENAME,)
    prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME, name,)
    params = {}
    doctype = ""
    preview = None

    if manifest is not None:
        title = manifest['title'] or title
        description = manifest['description'] or description
        rules = manifest['rules'] or rules
        prefix = manifest['prefix'] or prefix
        params = manifest['parameters'] or params
        doctype = manifest['doctype'] or doctype
        preview = manifest['preview'] or preview

    if isinstance(rules, str):
        rules = rules.decode('utf-8')
    if isinstance(prefix, str):
        prefix = prefix.decode('utf-8')

    return Theme(name, rules,
            title=title,
            description=description,
            absolutePrefix=prefix,
            parameterExpressions=params,
            doctype=doctype,
            preview=preview,
        )


def getAvailableThemes():
    """Get a list of all ITheme's available in resource directories.
    """

    resources = getAllResources(MANIFEST_FORMAT, filter=isValidThemeDirectory)
    themes = []
    for name, manifest in resources.items():
        themes.append(getTheme(name, manifest))

    themes.sort(key=lambda x: x.title)
    return themes


def getThemeFromResourceDirectory(resourceDirectory):
    """Return a Theme object from a resource directory
    """

    name = resourceDirectory.__name__

    title = name.capitalize().replace('-', ' ').replace('.', ' ')
    description = None
    rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, name, RULE_FILENAME,)
    prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME, name,)
    params = {}
    doctype = ""

    if resourceDirectory.isFile(MANIFEST_FILENAME):
        manifest = getManifest(
            resourceDirectory.openFile(MANIFEST_FILENAME), MANIFEST_FORMAT)

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

    return Theme(name, rules,
                title=title,
                description=description,
                absolutePrefix=prefix,
                parameterExpressions=params,
                doctype=doctype,
            )


def getZODBThemes():
    """Get a list of ITheme's stored in the ZODB.
    """

    resources = getZODBResources(MANIFEST_FORMAT, filter=isValidThemeDirectory)
    themes = []
    for name, manifest in resources.items():
        themes.append(getTheme(name, manifest))

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


def createThemeFromTemplate(title, description, baseOn='template'):
    """Create a new theme from the given title and description based on
    another theme resource directory
    """

    source = queryResourceDirectory(THEME_RESOURCE_NAME, baseOn)
    if source is None:
        raise KeyError("Theme %s not found" % baseOn)

    themeName = getUtility(IURLNormalizer).normalize(title)
    if isinstance(themeName, unicode):
        themeName = themeName.encode('utf-8')

    resources = getOrCreatePersistentResourceDirectory()
    if themeName in resources:
        idx = 1
        while "%s-%d" % (themeName, idx,) in resources:
            idx += 1
        themeName = "%s-%d" % (themeName, idx,)

    resources.makeDirectory(themeName)
    target = resources[themeName]

    cloneResourceDirectory(source, target)

    manifest = SafeConfigParser()

    if MANIFEST_FILENAME in target:
        fp = target.openFile(MANIFEST_FILENAME)
        try:
            manifest.readfp(fp)
        finally:
            fp.close()

    if not manifest.has_section('theme'):
        manifest.add_section('theme')

    manifest.set('theme', 'title', title)
    manifest.set('theme', 'description', description)

    manifestContents = StringIO()
    manifest.write(manifestContents)
    target.writeFile(MANIFEST_FILENAME, manifestContents)

    return themeName


def compileThemeTransform(rules, absolutePrefix=None, readNetwork=False, parameterExpressions=None):
    """Prepare the theme transform by compiling the rules with the given options
    """

    if parameterExpressions is None:
        parameterExpressions = {}

    accessControl = etree.XSLTAccessControl(read_file=True, write_file=False, create_dir=False, read_network=readNetwork, write_network=False)

    if absolutePrefix:
        absolutePrefix = expandAbsolutePrefix(absolutePrefix)

    params = set(parameterExpressions.keys() + ['url', 'base', 'path', 'scheme', 'host'])
    xslParams = dict((k, '') for k in params)

    internalResolver = InternalResolver()
    pythonResolver = PythonResolver()
    if readNetwork:
        networkResolver = NetworkResolver()

    rulesParser = etree.XMLParser(recover=False)
    rulesParser.resolvers.add(internalResolver)
    rulesParser.resolvers.add(pythonResolver)
    if readNetwork:
        rulesParser.resolvers.add(networkResolver)

    themeParser = etree.HTMLParser()
    themeParser.resolvers.add(internalResolver)
    themeParser.resolvers.add(pythonResolver)
    if readNetwork:
        themeParser.resolvers.add(networkResolver)

    compilerParser = etree.XMLParser()
    compilerParser.resolvers.add(internalResolver)
    compilerParser.resolvers.add(pythonResolver)
    if readNetwork:
        compilerParser.resolvers.add(networkResolver)

    compiledTheme = compile_theme(rules,
            absolute_prefix=absolutePrefix,
            parser=themeParser,
            rules_parser=rulesParser,
            compiler_parser=compilerParser,
            read_network=readNetwork,
            access_control=accessControl,
            update=True,
            xsl_params=xslParams,
        )

    if not compiledTheme:
        return None

    return etree.XSLT(compiledTheme,
            access_control=accessControl,
        )


def prepareThemeParameters(context, request, parameterExpressions, cache=None):
    """Prepare and return a dict of parameter expression values.
    """

    # Find real or virtual path - PATH_INFO has VHM elements in it
    url = request.get('ACTUAL_URL', '')

    # Find the host name
    base = request.get('BASE1', '')
    path = url[len(base):]
    parts = urlsplit(base.lower())

    params = dict(
            url=quote_param(url),
            base=quote_param(base),
            path=quote_param(path),
            scheme=quote_param(parts.scheme),
            host=quote_param(parts.netloc),
        )

    # Add expression-based parameters
    if parameterExpressions:

        # Compile and cache expressions
        expressions = None
        if cache is not None:
            expressions = cache.expressions

        if expressions is None:
            expressions = {}
            for name, expressionText in parameterExpressions.items():
                expressions[name] = compileExpression(expressionText)

            if cache is not None:
                cache.updateExpressions(expressions)

        # Execute all expressions
        expressionContext = createExpressionContext(context, request)
        for name, expression in expressions.items():
            params[name] = quote_param(expression(expressionContext))

    return params
