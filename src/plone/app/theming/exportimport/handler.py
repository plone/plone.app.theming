# -*- coding: utf-8 -*-
from lxml import etree
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import getAvailableThemes
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def importTheme(context):
    """Apply the theme with the id contained in the profile file theme.xml
    and enable the theme.
    """

    data = context.readDataFile('theme.xml')
    if not data:
        return

    logger = context.getLogger('plone.app.theming.exportimport')

    tree = etree.fromstring(data)

    # apply theme if given and valid
    themeName = tree.find("name")
    if themeName is not None:
        themeName = themeName.text.strip()
        themeInfo = None

        allThemes = getAvailableThemes()
        for info in allThemes:
            if info.__name__.lower() == themeName.lower():
                themeInfo = info
                break

        if themeInfo is None:
            raise ValueError("Theme {0:s} is not available".format(themeName))

        applyTheme(themeInfo)
        logger.info('Theme {0:s} applied'.format(themeName))

    # enable/disable theme
    themeEnabled = tree.find("enabled")
    if themeEnabled is None:
        return

    settings = getUtility(IRegistry).forInterface(IThemeSettings, False)

    themeEnabled = themeEnabled.text.strip().lower()
    if themeEnabled in ("y", "yes", "true", "t", "1", "on",):
        settings.enabled = True
        logger.info('Theme enabled')
    elif themeEnabled in ("n", "no", "false", "f", "0", "off",):
        settings.enabled = False
        logger.info('Theme disabled')
    else:
        raise ValueError(
            "{0:s} is not a valid value for <enabled />".format(themeEnabled)
        )
