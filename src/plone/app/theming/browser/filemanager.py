from zope.site.hooks import getSite
from zope.publisher.browser import BrowserView

from plone.app.theming.utils import getThemeFromResourceDirectory

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
        self.theme = getThemeFromResourceDirectory(self.context)
        self.title = self.theme.title

        self.portalUrl = getToolByName(self.context, 'portal_url')()

        return True