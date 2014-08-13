from zope.interface import implements
from plone.app.theming.interfaces import ITheme


class Theme(object):
    """A theme, loaded from a resource directory
    """

    implements(ITheme)

    def __init__(self, name, rules,
            title=None,
            description=None,
            absolutePrefix=None,
            parameterExpressions=None,
            doctype=None,
            preview=None,
            enabled_bundles=[],
            disabled_bundles=[]
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

    def __repr__(self):
        return '<Theme "%s">' % self.__name__
