from plone.app.theming.interfaces import IThemeAppliedEvent
from zope.interface import implements


class ThemeAppliedEvent(object):
    implements(IThemeAppliedEvent)

    def __init__(self, theme):
        self.theme = theme