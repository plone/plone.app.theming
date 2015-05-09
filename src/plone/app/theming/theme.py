# -*- coding: utf-8 -*-
from plone.app.theming.interfaces import ITheme
from zope.interface import implementer


@implementer(ITheme)
class Theme(object):
    """A theme, loaded from a resource directory
    """

    def __init__(
        self,
        name,
        rules,
        title=None,
        description=None,
        absolutePrefix=None,
        parameterExpressions=None,
        doctype=None,
        preview=None,
        enabled_bundles=[],
        disabled_bundles=[],
        development_css='',
        development_js='',
        production_css='',
        production_js='',
        tinymce_content_css='',
        tinymce_styles_css=''
    ):

        self.__name__ = name
        self.rules = rules
        self.title = title
        self.description = description
        self.absolutePrefix = absolutePrefix
        self.parameterExpressions = parameterExpressions
        self.doctype = doctype
        self.preview = preview
        self.enabled_bundles = [b for b in enabled_bundles if b]
        self.disabled_bundles = [b for b in disabled_bundles if b]
        self.tinymce_content_css = tinymce_content_css
        self.production_js = production_js
        self.production_css = production_css
        self.development_js = development_js
        self.development_css = development_css
        self.tinymce_styles_css = tinymce_styles_css

    def __repr__(self):
        return '<Theme "{0:s}">'.format(self.__name__)
