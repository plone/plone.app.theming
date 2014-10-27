# -*- coding: utf-8 -*-
from lxml import etree
from plone.app.theming.interfaces import IThemingLayer
from plone.app.theming.utils import compileThemeTransform
from plone.app.theming.utils import findContext
from plone.app.theming.utils import getParser
from plone.app.theming.utils import prepareThemeParameters
from plone.app.theming.utils import theming_policy
from plone.app.theming.zmi import patch_zmi
from plone.transformchain.interfaces import ITransform
from repoze.xmliter.utils import getHTMLSerializer
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
import Globals
import logging

# Disable theming of ZMI
patch_zmi()

LOGGER = logging.getLogger('plone.app.theming')


@implementer(ITransform)
@adapter(Interface, IThemingLayer)
class ThemeTransform(object):
    """Late stage in the 8000's transform chain. When plone.app.blocks is
    used, we can benefit from lxml parsing having taken place already.
    """

    order = 8850

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def setupTransform(self, runtrace=False):
        DevelopmentMode = Globals.DevelopmentMode
        policy = theming_policy(self.request)

        # Obtain settings. Do nothing if not found
        settings = policy.getSettings()

        if settings is None:
            return None

        if not policy.isThemeEnabled():
            return None

        cache = policy.getCache()

        # Apply theme
        transform = None

        if not DevelopmentMode:
            transform = cache.transform

        if transform is None:
            rules = settings.rules
            absolutePrefix = settings.absolutePrefix or None
            readNetwork = settings.readNetwork
            parameterExpressions = settings.parameterExpressions

            transform = compileThemeTransform(
                rules,
                absolutePrefix,
                readNetwork,
                parameterExpressions,
                runtrace=runtrace
            )
            if transform is None:
                return None

            if not DevelopmentMode:
                cache.updateTransform(transform)

        return transform

    def getSettings(self):
        return theming_policy(self.request).getSettings()

    def parseTree(self, result):
        contentType = self.request.response.getHeader('Content-Type')
        if contentType is None or not contentType.startswith('text/html'):
            return None

        contentEncoding = self.request.response.getHeader('Content-Encoding')
        if contentEncoding \
           and contentEncoding in ('zip', 'deflate', 'compress',):
            return None

        try:
            return getHTMLSerializer(result, pretty_print=False)
        except (AttributeError, TypeError, etree.ParseError):
            return None

    def transformString(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformUnicode(self, result, encoding):
        return self.transformIterable([result], encoding)

    def transformIterable(self, result, encoding):
        """Apply the transform if required
        """
        # Obtain settings. Do nothing if not found
        policy = theming_policy(self.request)
        settings = policy.getSettings()
        if settings is None:
            return None
        if not policy.isThemeEnabled():
            return None
        result = self.parseTree(result)
        if result is None:
            return None

        DevelopmentMode = Globals.DevelopmentMode
        diazo_debug = self.request.get('diazo.debug', '').lower()
        runtrace = (
            DevelopmentMode
            and diazo_debug in ('1', 'y', 'yes', 't', 'true')
        )

        try:
            etree.clear_error_log()

            if settings.doctype:
                result.doctype = settings.doctype
                if not result.doctype.endswith('\n'):
                    result.doctype += '\n'

            transform = self.setupTransform(runtrace=runtrace)
            if transform is None:
                return None

            cache = None
            if not DevelopmentMode:
                cache = policy.getCache()

            parameterExpressions = settings.parameterExpressions or {}
            params = prepareThemeParameters(
                findContext(self.request),
                self.request,
                parameterExpressions,
                cache
            )

            transformed = transform(result.tree, **params)
            error_log = transform.error_log
            if transformed is not None:
                # Transformed worked, swap content with result
                result.tree = transformed
        except etree.LxmlError as e:
            if not(DevelopmentMode):
                raise
            error_log = e.error_log
            runtrace = True

        if runtrace:
            from diazo.runtrace import generate_debug_html
            # Add debug information to end of body
            body = result.tree.xpath('/html/body')[0]
            debug_url = findContext(
                self.request
            ).portal_url() + '/++resource++diazo-debug'
            body.insert(
                -1,
                generate_debug_html(
                    debug_url,
                    rules=settings.rules,
                    rules_parser=getParser('rules', settings.readNetwork),
                    error_log=error_log,
                )
            )
        return result
