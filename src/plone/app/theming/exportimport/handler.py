from lxml import etree

from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.site.hooks import getSite
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import getAvailableThemes

def importTheme(context):
    """Apply the theme with the id contained in the profile file theme.xml
    and enable the theme.
    """

    data = context.readDataFile('theme.xml')
    if not data:
        return

    logger = context.getLogger('plone.app.theming.exportimport')

    tree = etree.fromstring(data)

    themeName = tree.find("name")
    themeEnabled = tree.find("enabled")

    if themeName is not None:
        themeName = themeName.text.strip()
        themeInfo = None

        allThemes = getAvailableThemes()
        for info in allThemes:
            if info.__name__.lower() == themeName.lower():
                themeInfo = info
                break

        if themeInfo is None:
            raise ValueError("Theme %s is not available" % themeName)

        applyTheme(themeInfo)
        logger.info('Theme %s applied' % themeName)

    toadapt = (getSite(), getRequest())
    settings = getMultiAdapter(toadapt, IThemeSettings)

    if themeEnabled is not None:
        themeEnabled = themeEnabled.text.strip().lower()

        if themeEnabled in ("y", "yes", "true", "t", "1", "on",):
            settings.enabled = True
            logger.info('Theme enabled')
        elif themeEnabled in ("n", "no", "false", "f", "0", "off",):
            settings.enabled = False
            logger.info('Theme disabled')
        else:
            raise ValueError("%s is not a valid value for <enabled />" % themeEnabled)
