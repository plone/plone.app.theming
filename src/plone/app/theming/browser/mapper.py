import urllib
import os.path

import lxml.etree

from diazo.utils import quote_param

from zope.component import getMultiAdapter
from zope.component import getUtility

from zope.site.hooks import getSite
from zope.publisher.browser import BrowserView

from repoze.xmliter.utils import getHTMLSerializer
from plone.app.theming.utils import compileThemeTransform
from plone.app.theming.utils import prepareThemeParameters
from plone.app.theming.utils import getCurrentTheme

from plone.registry.interfaces import IRegistry

from plone.subrequest import subrequest

from plone.resource.interfaces import IWritableResourceDirectory

from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import THEME_EXTENSIONS

from plone.app.theming.utils import getPortal
from plone.app.theming.utils import findContext
from plone.app.theming.utils import getThemeFromResourceDirectory

from AccessControl import Unauthorized
from zExceptions import NotFound

from Products.Five.browser.decode import processInputs
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.utils import getToolByName

class ThemeMapper(BrowserView):

    theme_error_template = ViewPageTemplateFile("theme-error.pt")

    def __call__(self):
        self.setup()

        if self.update():
            # Evil hack to deal with the lack of implicit acquisition from
            # resource directories
            self.context = getSite()
            return self.index()
        return ''

    def setup(self):
        self.request.response.setHeader('X-Theme-Disabled', '1')
        processInputs(self.request)

        self.resourceDirectory = self.context
        self.theme = getThemeFromResourceDirectory(self.context)
        self.name = self.resourceDirectory.__name__
        self.title = self.theme.title

        self.portalUrl = getToolByName(self.context, 'portal_url')()
        self.themeBasePath = "++%s++%s" % (THEME_RESOURCE_NAME, self.name,)
        self.themeBasePathEncoded = urllib.quote_plus(self.themeBasePath)
        self.themeBaseUrl = "%s/%s" % (self.portalUrl, self.themeBasePath,)

        self.editable = IWritableResourceDirectory.providedBy(self.resourceDirectory)

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        self.active = (settings.enabled and self.name == getCurrentTheme())

        self.jsVariables="var BASE_URL='%s'; var CURRENT_SELECTION='%s'; var THEME_BASE_URL='%s'; var EDITABLE=%s" % (
                self.request['URL'],
                self.request.get('file-selector') or '',
                self.themeBaseUrl,
                str(self.editable).lower(),
            );

    def update(self):
        rulesFile = RULE_FILENAME

        if not self.resourceDirectory.isFile(rulesFile):
            self.rules = "(%s not found)" % rulesFile
        else:
            self.rules = self.resourceDirectory.readFile(rulesFile)

        self.themeFiles = self.findThemeFiles(self.resourceDirectory)

        self.defaultThemeFile = None
        for t in self.themeFiles:

            # Select the first .html theme file
            if self.defaultThemeFile is None:
                self.defaultThemeFile = t['path']

            # Prefer the first index.html or theme.html
            if t['filename'].lower() in ('index.html', 'index.htm', 'theme.html', 'theme.htm',):
                self.defaultThemeFile = t['path']
                break

        return True

    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized

    def redirect(self, message):
        IStatusMessage(self.request).add(message)
        self.request.response.redirect("%s/@@theming-controlpanel" % self.portalUrl)

    def findThemeFiles(self, directory, files=None, prefix=''):
        """Depth-first search of files with known extensions.
        Returns a list of dicts with keys path, filename and extension.
        """

        if files is None:
            files = []

        dirs = []

        for f in directory.listDirectory():
            if not f or f == RULE_FILENAME:
                continue

            if directory.isDirectory(f):
                dirs.append(f)
            else:

                path = f
                if prefix:
                    path = prefix + '/' + f

                basename, ext = os.path.splitext(f)
                ext = ext[1:].lower()
                if ext in THEME_EXTENSIONS:
                    files.append({
                        'path': path,
                        'filename': f,
                        'extension': ext,
                    })

        # Do directories last
        for f in dirs:
            path = f
            if prefix:
                path = prefix + '/' + f
            self.findThemeFiles(directory[f], files=files, prefix=path)

        return files

    def getFrame(self):
        """AJAX method to load a frame's contents

        Expects two query string parameters: ``path`` - the path to fetch - and
        ``theme``, which can be 'off', to disable the theme and 'apply' to
        apply the current theme to the response.
        """

        processInputs(self.request)

        path = self.request.form.get('path', None)
        theme = self.request.form.get('theme', 'off')

        if not path:
            return "<html><head></head><body></body></html>"

        portal = getPortal()
        response = subrequest(path, root=portal)

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

        # Not HTML? Return as-is
        if content_type is None or not content_type.startswith('text/html'):
            if len(result) == 0:
                result = ' ' # Zope does not deal well with empty responses
            return result

        result = result.decode(encoding).encode('ascii', 'xmlcharrefreplace')
        if len(result) == 0:
            result = ' ' # Zope does not deal well with empty responses

        if theme == 'off':
            self.request.response.setHeader('X-Theme-Disabled', '1')
        elif theme == 'apply':
            self.request.response.setHeader('X-Theme-Disabled', '1')
            theme = getThemeFromResourceDirectory(self.context)

            registry = getUtility(IRegistry)
            settings = registry.forInterface(IThemeSettings, False)

            context = self.context
            try:
                context = findContext(portal.restrictedTraverse(path))
            except (KeyError, NotFound,):
                pass

            serializer = getHTMLSerializer([result], pretty_print=False)

            try:
                transform = compileThemeTransform(theme.rules, theme.absolutePrefix, settings.readNetwork, theme.parameterExpressions or {})
            except lxml.etree.XMLSyntaxError, e:
                return self.theme_error_template(error=e.msg)

            params = prepareThemeParameters(context, self.request, theme.parameterExpressions or {})

            # Fix url and path since the request gave us this view
            params['url'] = quote_param("%s%s" % (portal.absolute_url(), path,))
            params['path'] = quote_param("%s%s" % (portal.absolute_url_path(), path,))

            if theme.doctype:
                serializer.doctype = theme.doctype
                if not serializer.doctype.endswith('\n'):
                    serializer.doctype += '\n'

            serializer.tree = transform(serializer.tree, **params)
            result = ''.join(serializer)

        return result

    def save(self, value):
        """Save the rules file (AJAX request)
        """
        processInputs(self.request)
        value = value.replace('\r\n', '\n');
        self.context.writeFile(RULE_FILENAME, value.encode('utf-8'))