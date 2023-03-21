from plone.app.theming.interfaces import IThemeAppliedEvent
from zope.interface import implementer


@implementer(IThemeAppliedEvent)
class ThemeAppliedEvent:
    def __init__(self, theme):
        self.theme = theme
