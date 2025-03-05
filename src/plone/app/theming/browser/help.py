from importlib import resources
from zope.publisher.browser import BrowserView

import docutils.core


class Help(BrowserView):
    def __call__(self):
        ref = resources.files("plone.app.theming").joinpath(
            "browser/resources/userguide.rst"
        )
        rstSource = str(ref.read_bytes())

        parts = docutils.core.publish_parts(source=rstSource, writer_name="html")
        html = parts["body_pre_docinfo"] + parts["fragment"]
        return f"""<div class="content">{html:s}</div>"""
