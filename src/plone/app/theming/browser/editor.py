import os.path

from zope.component import getMultiAdapter
from zope.site.hooks import getSite
from zope.publisher.browser import BrowserView

from plone.resource.manifest import MANIFEST_FILENAME
from plone.resource.manifest import getManifest

from plone.app.theming.interfaces import _
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import MANIFEST_FORMAT

from AccessControl import Unauthorized
from Products.Five.browser.decode import processInputs
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.utils import getToolByName

KNOWN_EXTENSIONS = frozenset(['css', 'html', 'htm', 'txt', 'xml', 'js', 'cfg'])

class ThemeEditor(BrowserView):

    def __call__(self):
        self.setup()

        # AJAX methods
        if 'ajax_load' in self.request.form:
            if 'fetch' in self.request.form:
                return self.fetch(self.request.form['fetch'])
        
        # Standard rendering
        else:
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
        self.name = self.resourceDirectory.__name__
        self.title = self.name.capitalize().replace('-', ' ').replace('.', ' ')
        self.manifest = None
        self.editableFiles = []

        self.jsVariables="var BASE_URL='%s'; var CURRENT_SELECTION='%s';" % (
                self.request['URL'],
                self.request.get('file-selector') or '',
            );
    
    def update(self):
        form = self.request.form

        if 'form.button.Save' in form:
            self.authorize()
            
            edited = {}
            for key in form.keys():
                if key.startswith('edited-file-'):
                    edited[key[12:]] = form[key]
            self.saveFiles(edited)

            IStatusMessage(self.request).add(_(u"Changes saved"))
        
        elif 'form.button.Cancel' in form:
            self.redirect(_(u"Edit cancelled"))
            return False
        
        # We're not processing the form - do the more expensive setup

        if MANIFEST_FILENAME in self.resourceDirectory:
            self.manifest = getManifest(self.resourceDirectory.openFile(MANIFEST_FILENAME), MANIFEST_FORMAT)
            self.title = self.manifest.get('title') or self.title
        
        self.editableFiles = self.findEditableFiles(self.resourceDirectory)

        return True
    
    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized
    
    def redirect(self, message):
        IStatusMessage(self.request).add(message)
        portalUrl = getToolByName(self.context, 'portal_url')()
        self.request.response.redirect("%s/@@theming-controlpanel" % portalUrl)
    
    def findEditableFiles(self, directory, files=None, prefix=''):
        """Depth-first search of files with known extensions.
        Returns a list of dicts with keys path, filename and extension.
        """

        if files is None:
            files = []
        
        for f in directory.listDirectory():
            if not f:
                continue
            
            path = f
            if prefix:
                path = prefix + '/' + f
            if directory.isDirectory(f):
                self.findEditableFiles(directory[f], files=files, prefix=path)
            else:
                basename, ext = os.path.splitext(f)
                ext = ext[1:].lower()
                if ext in KNOWN_EXTENSIONS:
                    files.append({
                        'path': path,
                        'filename': f,
                        'extension': ext,
                    })
        return files
    
    def fetch(self, path):
        """Fetch the contents of a file
        """

        self.request.response.setHeader('Content-Type', 'text/plain')
        return self.resourceDirectory.readFile(path.encode('utf-8'))
    
    def saveFiles(self, files):
        """Save files given as a dict of path -> contents (unicode string)
        """
        for path, contents in files.iteritems():
            self.resourceDirectory.writeFile(path, contents.encode('utf-8'))
    