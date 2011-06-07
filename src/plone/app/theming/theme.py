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
    ):

        self.__name__ = name
        self.rules = rules
        self.title = title
        self.description = description
        self.absolutePrefix = absolutePrefix
        self.parameterExpressions = parameterExpressions
        self.doctype = doctype
