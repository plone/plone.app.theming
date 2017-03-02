# -*- coding: utf-8 -*-
from zope.publisher.browser import BrowserView

import docutils.core
import pkg_resources


class Help(BrowserView):

    def __call__(self):
        rstSource = pkg_resources.resource_string(
            'plone.app.theming.browser',
            'resources/userguide.rst'
        )
        parts = docutils.core.publish_parts(
            source=rstSource,
            writer_name='html'
        )
        html = parts['body_pre_docinfo'] + parts['fragment']
        return """<div class="content">{0:s}</div>""".format(html)
