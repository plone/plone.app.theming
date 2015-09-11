# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.utils import safe_unicode
from Products.PageTemplates.Expressions import getEngine
from StringIO import StringIO
from diazo.compiler import compile_theme
from diazo.compiler import quote_param
from lxml import etree
from plone.app.theming.interfaces import IThemingPolicy
from plone.app.theming.interfaces import INoRequest
from plone.app.theming.interfaces import MANIFEST_FORMAT
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.plugins.utils import getPluginSettings
from plone.app.theming.plugins.utils import getPlugins
from plone.app.theming.theme import Theme
from plone.i18n.normalizer.interfaces import IURLNormalizer
from plone.resource.interfaces import IResourceDirectory
from plone.resource.manifest import MANIFEST_FILENAME
from plone.resource.manifest import extractManifestFromZipFile
from plone.resource.manifest import getManifest
from plone.resource.manifest import getZODBResources
from plone.resource.manifest import getAllResources
from plone.resource.utils import cloneResourceDirectory
from plone.resource.utils import iterDirectoriesOfType
from plone.resource.utils import queryResourceDirectory
from plone.subrequest import subrequest
from urlparse import urlsplit
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implementer
import logging
import pkg_resources

LOGGER = logging.getLogger('plone.app.theming')


@implementer(INoRequest)
class NoRequest(object):
    """Fallback to enable querying for the policy adapter
    even in the absence of a proper IRequest."""


def theming_policy(request=None):
    """Primary policy accessor, uses pluggable ZCA lookup.
    Resolves into a IThemingPolicy adapter."""
    if not request:
        request = getRequest()
    if not request:
        request = NoRequest()  # the adapter knows how to handle this
    return IThemingPolicy(request)


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
                system_url = '/{0:s}/{1:s}'.format(
                    '/'.join(context_path),
                    system_url
                )

        response = subrequest(system_url, root=root)
        if response.status != 200:
            LOGGER.error("Couldn't resolve {0:s}".format(system_url))
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
        (context, request),
        name=u"plone_portal_state"
    )
    if portalState is None:
        return None
    return portalState.portal()


def findContext(request):
    """Find the context from the request
    """
    published = request.get('PUBLISHED', None)
    context = getattr(published, '__parent__', None)
    if context is not None:
        return context

    for parent in request.PARENTS:
        if IContentish.providedBy(parent) or ISiteRoot.providedBy(parent):
            return parent

    return request.PARENTS[0]


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
    return directory.isFile(MANIFEST_FILENAME) \
        or directory.isFile(RULE_FILENAME)


def extractThemeInfo(zipfile, checkRules=True):
    """Return an ITheme based on the information in the given zipfile.
    Will throw a ValueError if the theme directory does not contain a single
    top level directory or the rules file cannot be found.
    Set checkRules=False to disable the rules check.
    """

    name, manifest = extractManifestFromZipFile(
        zipfile,
        MANIFEST_FORMAT
    )
    if not manifest:
        manifest = {}
    rules = manifest.get('rules', None)
    if rules is None:
        if checkRules:
            try:
                zipfile.getinfo(
                    "{0:s}/{1:s}".format(name, RULE_FILENAME)
                )
            except KeyError:
                raise ValueError("Could not find theme name and rules file")
        rules = u"/++{0:s}++{1:s}/{0:s}".format(
            THEME_RESOURCE_NAME,
            name,
            RULE_FILENAME
        )
    return getTheme(name, manifest)


def getTheme(name, manifest=None, resources=None):
    if manifest is None:
        if resources is None:
            resources = getAllResources(
                MANIFEST_FORMAT,
                filter=isValidThemeDirectory
            )
        if name not in resources:
            return None
        manifest = resources[name] or {}

    title = manifest.get('title', None)
    if title is None:
        title = name.capitalize().replace('-', ' ').replace('.', ' ')
    description = manifest.get('description', None)
    rules = manifest.get('rules', None)
    if rules is None:
        rules = u"/++{0:s}++{1:s}/{2:s}".format(
            THEME_RESOURCE_NAME,
            name,
            RULE_FILENAME,
        )
    prefix = manifest.get('prefix', None)
    if prefix is None:
        prefix = u"/++{0:s}++{1:s}".format(THEME_RESOURCE_NAME, name)
    params = manifest.get('parameters', None) or {}
    doctype = manifest.get('doctype', None) or ""
    preview = manifest.get('preview', None)
    enabled_bundles = manifest.get('enabled-bundles', None) or ''
    enabled_bundles = enabled_bundles.split(',') if enabled_bundles else []
    disabled_bundles = manifest.get('disabled-bundles', None) or ''
    disabled_bundles = disabled_bundles.split(',') if disabled_bundles else []
    development_css = manifest.get('development-css', None) or ''
    development_js = manifest.get('development-js', None) or ''
    production_css = manifest.get('production-css', None) or ''
    production_js = manifest.get('production-js', None) or ''
    tinymce_content_css = manifest.get('tinymce-content-css', None) or ''
    tinymce_styles_css = manifest.get('tinymce-styles-css', None) or ''
    if isinstance(rules, str):
        rules = rules.decode('utf-8')
    if isinstance(prefix, str):
        prefix = prefix.decode('utf-8')
    return Theme(
        name,
        rules,
        title=title,
        description=description,
        absolutePrefix=prefix,
        parameterExpressions=params,
        doctype=doctype,
        preview=preview,
        enabled_bundles=enabled_bundles,
        disabled_bundles=disabled_bundles,
        development_css=development_css,
        development_js=development_js,
        production_css=production_css,
        production_js=production_js,
        tinymce_content_css=tinymce_content_css,
        tinymce_styles_css=tinymce_styles_css
    )


def getAvailableThemes():
    """Get a list of all ITheme's available in resource directories.
    """
    resources = getThemeResources(MANIFEST_FORMAT, filter=isValidThemeDirectory)
    themes = []
    for theme in resources:
        themes.append(getTheme(theme['name'], theme))

    themes.sort(key=lambda x: safe_unicode(x.title))
    return themes

def getThemeResources(format, defaults=None, filter=None, manifestFilename=MANIFEST_FILENAME):

    resources = []

    for directory in iterDirectoriesOfType(format.resourceType, filter_duplicates=False):

        if filter is not None and not filter(directory):
            continue

        name = directory.__name__

        if directory.isFile(manifestFilename):

            manifest = directory.openFile(manifestFilename)
            try:
                theme = getManifest(manifest, format, defaults)
                theme['name'] = name
                resources.append(theme)
            except:
                LOGGER.exception("Unable to read manifest for theme directory %s", name)
            finally:
                manifest.close()

    return resources


def getThemeFromResourceDirectory(resourceDirectory):
    """Return a Theme object from a resource directory
    """
    name = resourceDirectory.__name__
    if resourceDirectory.isFile(MANIFEST_FILENAME):
        manifest = getManifest(
            resourceDirectory.openFile(MANIFEST_FILENAME), MANIFEST_FORMAT
        )
    else:
        manifest = {}

    return getTheme(name, manifest)


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
    return theming_policy().getCurrentTheme()


def isThemeEnabled(request, settings=None):
    """Determine if a theme is enabled for the given request
    """
    return theming_policy(request).isThemeEnabled(settings)


def applyTheme(theme):
    """Apply an ITheme
    """
    # on write, force using default policy
    policy = IThemingPolicy(NoRequest())
    settings = policy.getSettings()

    plugins = None
    themeDirectory = None
    pluginSettings = None
    currentTheme = policy.getCurrentTheme()

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

        currentTheme = settings.currentTheme
        themeDirectory = queryResourceDirectory(
            THEME_RESOURCE_NAME, currentTheme)
        if themeDirectory is not None:
            plugins = getPlugins()
            pluginSettings = getPluginSettings(themeDirectory, plugins)

        if pluginSettings is not None:
            for name, plugin in plugins:
                plugin.onEnabled(currentTheme, pluginSettings[name],
                                 pluginSettings)
        policy.set_theme(currentTheme, theme)


def createThemeFromTemplate(title, description, baseOn='template'):
    """Create a new theme from the given title and description based on
    another theme resource directory
    """

    source = queryResourceDirectory(THEME_RESOURCE_NAME, baseOn)
    if source is None:
        raise KeyError("Theme {0:s} not found".format(baseOn))

    themeName = getUtility(IURLNormalizer).normalize(title)
    if isinstance(themeName, unicode):
        themeName = themeName.encode('utf-8')

    resources = getOrCreatePersistentResourceDirectory()

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

    if manifest.has_option('theme', 'prefix'):
        prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME, themeName)
        manifest.set('theme', 'prefix', prefix)

    if manifest.has_option('theme', 'rules'):
        rule = manifest.get('theme', 'rules')
        rule_file_name = rule.split('/')[-1]  # extract real rules file name
        rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, themeName,
                                   rule_file_name)
        manifest.set('theme', 'rules', rules)

    paths_to_fix = ['development-css', 'production-css', 'tinymce-content-css',
                    'development-js', 'production-js']
    for var_path in paths_to_fix:
        if not manifest.has_option('theme', var_path):
            continue
        val = manifest.get('theme', var_path)
        if not val:
            continue
        template_prefix = '++%s++%s/' % (THEME_RESOURCE_NAME, baseOn)
        if template_prefix in val:
            # okay, fix
            val = val.replace(template_prefix, '++%s++%s/' % (THEME_RESOURCE_NAME, themeName))
            manifest.set('theme', var_path, val)

    manifestContents = StringIO()
    manifest.write(manifestContents)
    target.writeFile(MANIFEST_FILENAME, manifestContents)

    return themeName


def getParser(type, readNetwork):
    """Set up a parser for either rules, theme or compiler
    """

    if type == 'rules':
        parser = etree.XMLParser(recover=False)
    elif type == 'theme':
        parser = etree.HTMLParser()
    elif type == 'compiler':
        parser = etree.XMLParser()
    parser.resolvers.add(InternalResolver())
    parser.resolvers.add(PythonResolver())
    if readNetwork:
        parser.resolvers.add(NetworkResolver())
    return parser


def compileThemeTransform(
    rules,
    absolutePrefix=None,
    readNetwork=False,
    parameterExpressions=None,
    runtrace=False
):
    """Prepare the theme transform by compiling the rules with the given options
    """

    if parameterExpressions is None:
        parameterExpressions = {}

    accessControl = etree.XSLTAccessControl(
        read_file=True,
        write_file=False,
        create_dir=False,
        read_network=readNetwork,
        write_network=False
    )

    if absolutePrefix:
        absolutePrefix = expandAbsolutePrefix(absolutePrefix)
    params = set(['url', 'base', 'path', 'scheme', 'host'])
    params.update(parameterExpressions.keys())
    xslParams = {k: '' for k in params}

    compiledTheme = compile_theme(
        rules,
        absolute_prefix=absolutePrefix,
        parser=getParser('theme', readNetwork),
        rules_parser=getParser('rules', readNetwork),
        compiler_parser=getParser('compiler', readNetwork),
        read_network=readNetwork,
        access_control=accessControl,
        update=True,
        xsl_params=xslParams,
        runtrace=runtrace,
    )

    if not compiledTheme:
        return None

    return etree.XSLT(
        compiledTheme,
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
    if not parameterExpressions:
        return params

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
