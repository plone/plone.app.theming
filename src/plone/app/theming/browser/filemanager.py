from zope.site.hooks import getSite
from zope.publisher.browser import BrowserView

from plone.resource.manifest import MANIFEST_FILENAME
from plone.resource.manifest import getManifest

from plone.app.theming.interfaces import MANIFEST_FORMAT

from Products.CMFCore.utils import getToolByName

class FileManager(BrowserView):
    
    def __call__(self):
        if self.update():
            # Evil hack to deal with the lack of implicit acquisition from
            # resource directories
            self.context = getSite()
            return self.index()
        return ''

    def update(self):
        self.request.response.setHeader('X-Theme-Disabled', '1')
        
        self.resourceDirectory = self.context
        self.name = self.resourceDirectory.__name__

        self.portalUrl = getToolByName(self.context, 'portal_url')()

        return True

    def title(self):
        if MANIFEST_FILENAME in self.resourceDirectory:
            fi = self.resourceDirectory.openFile(MANIFEST_FILENAME)
            self.manifest = getManifest(fi, MANIFEST_FORMAT)
            self.title = self.manifest.get('title') or self.title
