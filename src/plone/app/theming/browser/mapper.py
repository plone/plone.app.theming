# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from diazo.utils import quote_param
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import THEME_EXTENSIONS
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import compileThemeTransform
from plone.app.theming.utils import findPathContext
from plone.app.theming.utils import getPortal
from plone.app.theming.utils import getThemeFromResourceDirectory
from plone.app.theming.utils import prepareThemeParameters
from plone.app.theming.utils import theming_policy
from plone.memoize import view
from plone.registry.interfaces import IRegistry
from plone.resource.interfaces import IWritableResourceDirectory
from plone.subrequest import subrequest
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources import add_bundle_on_request
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from repoze.xmliter.utils import getHTMLSerializer
from six.moves import urllib
from zExceptions import NotFound
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.publisher.browser import BrowserView

import json
import lxml.etree
import lxml.html
import lxml.html.builder
import os.path
import six


try:
    # Zope 4
    from Products.Five.browser.decode import processInputs
except ImportError:
    # Zope 5
    processInputs = None


class ThemeMapper(BrowserView):

    theme_error_template = ViewPageTemplateFile("theme-error.pt")

    def __call__(self):
        add_bundle_on_request(self.request, 'thememapper')
        self.setup()

        if self.update():
            # Evil hack to deal with the lack of implicit acquisition from
            # resource directories
            self.context = getSite()
            return self.index()
        return ''

    @view.memoize
    def development(self):
        registry = getUtility(IRegistry)
        current_username = _getAuthenticatedUser(self.context).getUserName()
        if current_username == 'Anonymous User':
            return False
        return registry.records['plone.resources.development'].value

    def setup(self):
        self.request.response.setHeader('X-Theme-Disabled', '1')
        if processInputs is not None:
            processInputs(self.request)

        self.resourceDirectory = self.context
        self.theme = getThemeFromResourceDirectory(self.context)
        self.name = self.resourceDirectory.__name__
        self.title = self.theme.title

        self.portalUrl = getToolByName(self.context, 'portal_url')()
        self.themeBasePath = "++{0:s}++{1:s}".format(
            THEME_RESOURCE_NAME,
            self.name
        )
        self.themeBasePathEncoded = urllib.parse.quote_plus(self.themeBasePath)
        self.themeBaseUrl = '/'.join([self.portalUrl, self.themeBasePath])

        try:
            registry = getUtility(IRegistry)
            self.lessUrl = registry['plone.resources.lessc']
            self.lessVariables = self.portalUrl + '/' + registry['plone.resources.less-variables']
        except:
            self.lessUrl = None
            self.lessVariables = None

        self.editable = IWritableResourceDirectory.providedBy(
            self.resourceDirectory
        )

        if self.editable:
            self.resourceUrl = self.resourceDirectory.context.absolute_url()
        else:
            self.resourceUrl = None

        policy = theming_policy(self.request)
        settings = policy.getSettings()
        self.active = (settings.enabled
                       and self.name == policy.getCurrentTheme())

        self.rulesFileName = RULE_FILENAME

    def update(self):
        self.themeFiles = self.findThemeFiles(self.resourceDirectory)

        self.defaultThemeFile = None
        for t in self.themeFiles:

            # Select the first .html theme file
            if self.defaultThemeFile is None:
                self.defaultThemeFile = t['path']

            # Prefer the first index.html or theme.html
            if t['filename'].lower() in ('index.html', 'index.htm',
                                         'theme.html', 'theme.htm',):
                self.defaultThemeFile = t['path']
                break

        return True

    def get_thememapper_config(self):
        config = {
            'themeUrl': self.resourceUrl,
            'editable': self.editable,
            'lessUrl': self.lessUrl,
            'lessVariables': self.lessVariables,
            'filemanagerConfig': {
                'actionUrl': '{0}/@@plone.resourceeditor.filemanager-actions'.format(  # noqa
                    self.themeBaseUrl
                ),
            },
            'mockupUrl': '{0}/@@theming-controlpanel-mapper-getframe?path=/{1}/{2}&theme=off'.format(  # noqa
                self.themeBaseUrl,
                self.themeBasePathEncoded,
                self.defaultThemeFile
            ),
            'unthemedUrl': '{0}/@@theming-controlpanel-mapper-getframe?path=/&diazo.off=1'.format(  # noqa
                self.themeBaseUrl
            ),
            'previewUrl': '{0}/++theme++{1}/@@theming-controlpanel-mapper-getframe?path=/&theme=apply&forms=disable&links=replace&title=Preview:+{2}'.format(  # noqa
                self.portalUrl,
                self.name,
                self.title
            ),
            'helpUrl': 'http://docs.diazo.org/en/latest'
        }
        return json.dumps(config)

    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request),
                                        name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized

    def redirect(self, message):
        IStatusMessage(self.request).add(message)
        self.request.response.redirect(
            "{0:s}/@@theming-controlpanel".format(self.portalUrl)
        )

    def findThemeFiles(self, directory, files=None, prefix=''):
        """Depth-first search of files with known extensions.
        Returns a list of dicts with keys path, filename and extension.
        """

        if files is None:
            files = []

        dirs = []

        for filename in directory.listDirectory():
            if not filename or filename == RULE_FILENAME:
                continue

            if directory.isDirectory(filename):
                dirs.append(filename)
            else:

                path = filename
                if prefix:
                    path = prefix + '/' + filename

                basename, ext = os.path.splitext(filename)
                ext = ext[1:].lower()
                if ext in THEME_EXTENSIONS:
                    files.append({
                        'path': '/' + path,
                        'filename': filename,
                        'extension': ext,
                    })

        # Do directories last
        for filename in dirs:
            path = filename
            if prefix:
                path = prefix + '/' + filename
            self.findThemeFiles(directory[filename], files=files, prefix=path)

        return files

    def getFrame(self):
        """AJAX method to load a frame's contents

        Expects two query string parameters: ``path`` - the path to fetch - and
        ``theme``, which can be 'off', to disable the theme and 'apply' to
        apply the current theme to the response.

        Additionally:

        - a query string parameter ``links`` can be set to one of ``disable``
          or ``replace``. The former will disable hyperlinks; the latter will
          replace them with links using the
          ``@@themeing-controlpanel-getframe`` view.
        - a query string parameter ``forms`` can be set to one of ``disable``
          or ``replace``. The former will disable forms ; the latter will
          replace them with links using the
          ``@@themeing-controlpanel-getframe`` view.
        - a query string parameter ``title`` can be set to give a new page
          title
        """
        if processInputs is not None:
            processInputs(self.request)

        path = self.request.form.get('path', '/')
        theme = self.request.form.get('theme', 'off')
        links = self.request.form.get('links', None)
        forms = self.request.form.get('forms', None)
        title = self.request.form.get('title', None)

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

            policy = theming_policy(self.request)
            settings = policy.getSettings()

            context = findPathContext(path) or portal

            serializer = getHTMLSerializer([result], pretty_print=False)

            try:
                transform = compileThemeTransform(
                    themeInfo.rules, themeInfo.absolutePrefix,
                    settings.readNetwork, themeInfo.parameterExpressions or {})
            except lxml.etree.XMLSyntaxError as e:
                return self.theme_error_template(error=e.msg)

            params = prepareThemeParameters(
                context, self.request, themeInfo.parameterExpressions or {})

            # Fix url and path since the request gave us this view
            params['url'] = quote_param(''.join((portal_url, path,)))
            params['path'] = quote_param(
                ''.join((portal.absolute_url_path(), path,))
            )

            if themeInfo.doctype:
                serializer.doctype = themeInfo.doctype
                if not serializer.doctype.endswith('\n'):
                    serializer.doctype += '\n'

            serializer.tree = transform(serializer.tree, **params)
            result = b''.join(serializer)

        if title or links or forms:
            tree = lxml.html.fromstring(result)

            def encodeUrl(orig):
                origUrl = urllib.parse.urlparse(orig)
                newPath = origUrl.path
                newQuery = urllib.parse.parse_qs(origUrl.query)

                # relative?
                if not origUrl.netloc:
                    newPath = urllib.parse.urljoin(
                        path.rstrip("/") + "/", newPath.lstrip("/"))
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
                    if isinstance(title, six.text_type):
                        newQuery['title'] = title.encode('utf-8', 'replace')
                    else:
                        newQuery['title'] = title

                return self.request.getURL() + '?' + urllib.parse.urlencode(newQuery)

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
