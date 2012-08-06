import urllib
import urlparse
import os.path

import lxml.etree
import lxml.html
import lxml.html.builder

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

        self.rulesFileName = RULE_FILENAME

        self.jsVariables = "var CURRENT_SELECTION='%s'; var THEME_BASE_URL='%s'; var THEME_BASE_PATH_ENCODED='%s'; var EDITABLE=%s; var RULE_FILENAME='%s';" % (
                self.request.get('file-selector') or '',
                self.themeBaseUrl,
                self.themeBasePathEncoded,
                str(self.editable).lower(),
                self.rulesFileName
            )

    def update(self):
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
                        'path': '/' + path,
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

        Additionally:

        - a query string parameter ``links`` can be set to one of ``disable``
          or ``replace``. The former will disable hyperlinks; the latter will
          replace them with links using the ``@@themeing-controlpanel-getframe``
          view.
        - a query string parameter ``forms`` can be set to one of ``disable``
          or ``replace``. The former will disable forms ; the latter will
          replace them with links using the ``@@themeing-controlpanel-getframe``
          view.
        - a query string parameter ``title`` can be set to give a new page
          title
        """

        processInputs(self.request)

        path = self.request.form.get('path', None)
        theme = self.request.form.get('theme', 'off')
        links = self.request.form.get('links', None)
        forms = self.request.form.get('forms', None)
        title = self.request.form.get('title', None)

        if not path:
            return "<html><head></head><body></body></html>"

        portal = getPortal()
        portal_url = portal.absolute_url()
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
                result = ' '  # Zope does not deal well with empty responses
            return result

        result = result.decode(encoding).encode('ascii', 'xmlcharrefreplace')
        if len(result) == 0:
            result = ' '  # Zope does not deal well with empty responses

        if theme == 'off':
            self.request.response.setHeader('X-Theme-Disabled', '1')
        elif theme == 'apply':
            self.request.response.setHeader('X-Theme-Disabled', '1')
            themeInfo = getThemeFromResourceDirectory(self.context)

            registry = getUtility(IRegistry)
            settings = registry.forInterface(IThemeSettings, False)

            context = self.context
            try:
                context = findContext(portal.restrictedTraverse(path))
            except (KeyError, NotFound,):
                pass

            serializer = getHTMLSerializer([result], pretty_print=False)

            try:
                transform = compileThemeTransform(themeInfo.rules, themeInfo.absolutePrefix, settings.readNetwork, themeInfo.parameterExpressions or {})
            except lxml.etree.XMLSyntaxError, e:
                return self.themeInfo_error_template(error=e.msg)

            params = prepareThemeParameters(context, self.request, themeInfo.parameterExpressions or {})

            # Fix url and path since the request gave us this view
            params['url'] = quote_param("%s%s" % (portal_url, path,))
            params['path'] = quote_param("%s%s" % (portal.absolute_url_path(), path,))

            if themeInfo.doctype:
                serializer.doctype = themeInfo.doctype
                if not serializer.doctype.endswith('\n'):
                    serializer.doctype += '\n'

            serializer.tree = transform(serializer.tree, **params)
            result = ''.join(serializer)

        if title or links or forms:
            tree = lxml.html.fromstring(result)

            def encodeUrl(orig):
                origUrl = urlparse.urlparse(orig)
                newPath = origUrl.path
                newQuery = urlparse.parse_qs(origUrl.query)

                # relative?
                if not origUrl.netloc:
                    newPath = urlparse.urljoin(path.rstrip("/") + "/", newPath.lstrip("/"))
                elif not orig.lower().startswith(portal_url.lower()):
                    # Not an internal URL - ignore
                    return orig

                newQuery['path'] = newPath
                newQuery['theme'] = theme
                if links:
                    newQuery['links'] = links
                if forms:
                    newQuery['forms'] = forms
                if title:
                    newQuery['title'] = title

                return self.request.getURL() + '?' + urllib.urlencode(newQuery)

            if title:
                titleElement = tree.cssselect("html head title")
                if titleElement:
                    titleElement[0].text = title
                else:
                    headElement = tree.cssselect("html head")
                    if headElement:
                        headElement[0].append(lxml.html.builder.TITLE(title))

            if links:
                for n in tree.cssselect("a[href]"):
                    if links == 'disable':
                        n.attrib['href'] = '#'
                    elif links == 'replace':
                        n.attrib['href'] = encodeUrl(n.attrib['href'])

            if forms:
                for n in tree.cssselect("form[action]"):
                    if forms == 'disable':
                        n.attrib['action'] = '#'
                        n.attrib['onsubmit'] = 'javascript:return false;'
                    elif forms == 'replace':
                        n.attrib['action'] = encodeUrl(n.attrib['action'])

            result = lxml.html.tostring(tree)

        return result

    def save(self, value):
        """Save the rules file (AJAX request)
        """
        processInputs(self.request)
        value = value.replace('\r\n', '\n')
        self.context.writeFile(RULE_FILENAME, value.encode('utf-8'))
