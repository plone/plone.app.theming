import logging
import Globals

from urlparse import urlsplit

from lxml import etree
from diazo.compiler import compile_theme
from diazo.utils import quote_param

from repoze.xmliter.utils import getHTMLSerializer

from zope.interface import implements, Interface
from zope.component import adapts
from zope.component import queryUtility
from zope.site.hooks import getSite

from plone.registry.interfaces import IRegistry
from plone.transformchain.interfaces import ITransform

from plone.app.theming.interfaces import IThemeSettings, IThemingLayer
from plone.app.theming.utils import expandAbsolutePrefix

from plone.app.theming.utils import PythonResolver
from plone.app.theming.utils import InternalResolver
from plone.app.theming.utils import NetworkResolver

from plone.app.theming.utils import findContext
from plone.app.theming.utils import compileExpression
from plone.app.theming.utils import createExpressionContext
from plone.app.theming.utils import isThemeEnabled
from plone.app.theming.zmi import patch_zmi

# Disable theming of ZMI
patch_zmi()

LOGGER = logging.getLogger('plone.app.theming')

class _Cache(object):
    """Simple cache for the transform
    """

    def __init__(self):
        self.transform = None
        self.expressions = None

    def updateTransform(self, transform):
        self.transform = transform

    def updateExpressions(self, expressions):
        self.expressions = expressions

def getCache(settings):
    # We need a persistent object to hang a _v_ attribute off for caching.

    registry = settings.__registry__
    caches = getattr(registry, '_v_plone_app_theming_caches', None)
    if caches is None:
        caches = registry._v_plone_app_theming_caches = {}

    key = getSite().absolute_url()

    cache = caches.get(key)
    if cache is None:
        cache = caches[key] = _Cache()
    return cache

def invalidateCache(settings, event):
    """When our settings are changed, invalidate the cache on all zeo clients
    """
    registry = settings.__registry__
    registry._p_changed = True
    if hasattr(registry, '_v_plone_app_theming_caches'):
        del registry._v_plone_app_theming_caches

class ThemeTransform(object):
    """Late stage in the 8000's transform chain. When plone.app.blocks is
    used, we can benefit from lxml parsing having taken place already.
    """

    implements(ITransform)
    adapts(Interface, IThemingLayer)

    order = 8850

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def setupTransform(self):
        request = self.request
        DevelopmentMode = Globals.DevelopmentMode

        # Obtain settings. Do nothing if not found
        settings = self.getSettings()

        if settings is None:
            return None

        if not isThemeEnabled(request, settings):
            return None

        cache = getCache(settings)

        # Apply theme
        transform = None

        if not DevelopmentMode:
            transform = cache.transform

        if transform is None:
            rules = settings.rules
            absolutePrefix = settings.absolutePrefix or None
            readNetwork = settings.readNetwork
            accessControl = etree.XSLTAccessControl(read_file=True, write_file=False, create_dir=False, read_network=readNetwork, write_network=False)

            if absolutePrefix:
                absolutePrefix = expandAbsolutePrefix(absolutePrefix)

            params = set(settings.parameterExpressions.keys() + ['url', 'base', 'path', 'scheme', 'host'])
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

            transform = etree.XSLT(compiledTheme,
                    access_control=accessControl,
                )

            if not DevelopmentMode:
                cache.updateTransform(transform)

        return transform

    def getSettings(self):
        registry = queryUtility(IRegistry)
        if registry is None:
            return None

        try:
            settings = registry.forInterface(IThemeSettings, False)
        except KeyError:
            return None

        return settings

    def parseTree(self, result):
        contentType = self.request.response.getHeader('Content-Type')
        if contentType is None or not contentType.startswith('text/html'):
            return None

        contentEncoding = self.request.response.getHeader('Content-Encoding')
        if contentEncoding and contentEncoding in ('zip', 'deflate', 'compress',):
            return None

        try:
            return getHTMLSerializer(result, pretty_print=False)
        except (TypeError, etree.ParseError):
            return None

    def transformString(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformUnicode(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformIterable(self, result, encoding):
        """Apply the transform if required
        """

        result = self.parseTree(result)
        if result is None:
            return None

        transform = self.setupTransform()
        if transform is None:
            return None

        # Find real or virtual path - PATH_INFO has VHM elements in it
        url = self.request.get('ACTUAL_URL', '')

        # Find the host name
        base = self.request.get('BASE1', '')
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

        settings = self.getSettings()
        if settings.doctype:
            result.doctype = settings.doctype
            if not result.doctype.endswith('\n'):
                result.doctype += '\n'
        parameterExpressions = settings.parameterExpressions or {}
        if parameterExpressions:
            cache = getCache(settings)
            DevelopmentMode = Globals.DevelopmentMode

            # Compile and cache expressions
            expressions = None
            if not DevelopmentMode:
                expressions = cache.expressions

            if expressions is None:
                expressions = {}
                for name, expressionText in parameterExpressions.items():
                    expressions[name] = compileExpression(expressionText)

                if not DevelopmentMode:
                    cache.updateExpressions(expressions)

            # Execute all expressions
            context = findContext(self.request)
            expressionContext = createExpressionContext(context, self.request)
            for name, expression in expressions.items():
                params[name] = quote_param(expression(expressionContext))

        transformed = transform(result.tree, **params)
        if transformed is None:
            return None

        result.tree = transformed

        return result
