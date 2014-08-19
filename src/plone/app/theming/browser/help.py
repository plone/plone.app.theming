import pkg_resources
from zope.publisher.browser import BrowserView
import docutils.core


class Help(BrowserView):

    def __call__(self):
        rstSource = pkg_resources.resource_string('plone.app.theming.browser', 'resources/userguide.rst')
        parts = docutils.core.publish_parts(source=rstSource, writer_name='html')
        return parts['body_pre_docinfo'] + parts['fragment']
