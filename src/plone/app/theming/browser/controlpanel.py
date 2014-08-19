import logging
import zipfile

from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.schema.interfaces import IVocabularyFactory
from zope.publisher.browser import BrowserView

from plone.resource.utils import queryResourceDirectory
from plone.registry.interfaces import IRegistry

from plone.memoize.instance import memoize

from plone.app.theming.interfaces import _
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import DEFAULT_THEME_FILENAME
from plone.app.theming.interfaces import TEMPLATE_THEME

from plone.app.theming.utils import extractThemeInfo
from plone.app.theming.utils import getZODBThemes
from plone.app.theming.utils import getAvailableThemes
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import getOrCreatePersistentResourceDirectory
from plone.app.theming.utils import createThemeFromTemplate

from plone.app.theming.plugins.utils import getPluginSettings
from plone.app.theming.plugins.utils import getPlugins

from plone.app.controlpanel.skins import ISkinsSchema

from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.decode import processInputs
from Products.statusmessages.interfaces import IStatusMessage

logger = logging.getLogger('plone.app.theming')


def authorize(context, request):
    authenticator = getMultiAdapter((context, request), name=u"authenticator")
    if not authenticator.verify():
        raise Unauthorized


class ThemingControlpanel(BrowserView):

    def __call__(self):
        if self.update():
            return self.index()
        return ''

    def _setup(self):
        self.settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        self.zodbThemes = getZODBThemes()
        self.availableThemes = getAvailableThemes()
        self.selectedTheme = self.getSelectedTheme(self.availableThemes, self.settings.rules)
        self.overlay = ''

        self.skinsSettings = ISkinsSchema(self.context)
        self.skinsVocabulary = getUtility(IVocabularyFactory, name='plone.app.vocabularies.Skins')(self.context)

        # Set response header to make sure control panel is never themed
        self.request.response.setHeader('X-Theme-Disabled', '1')

    def redirect(self, url):
        self.request.response.redirect(url)

    def update(self):
        processInputs(self.request)
        self._setup()
        self.errors = {}
        form = self.request.form

        if 'form.button.Cancel' in form:
            IStatusMessage(self.request).add(_(u"Changes cancelled"))

            portalUrl = getToolByName(self.context, 'portal_url')()
            self.redirect("%s/plone_control_panel" % portalUrl)

            return False

        if 'form.button.Enable' in form:
            self.authorize()

            themeSelection = form.get('themeName', None)

            if themeSelection:
                themeData = self.getThemeData(self.availableThemes, themeSelection)
                applyTheme(themeData)
                self.settings.enabled = True

            IStatusMessage(self.request).add(_(u"Theme enabled. Note that this control panel page is never themed."))
            self._setup()
            return True

        if 'form.button.Disable' in form:
            self.authorize()

            applyTheme(None)
            self.settings.enabled = False

            IStatusMessage(self.request).add(_(u"Theme disabled."))
            self._setup()
            return True

        if 'form.button.AdvancedSave' in form:
            self.authorize()

            self.settings.readNetwork = form.get('readNetwork', False)

            themeEnabled = form.get('themeEnabled', False)
            rules = form.get('rules', None)
            prefix = form.get('absolutePrefix', None)
            doctype = str(form.get('doctype', ""))

            hostnameBlacklist = form.get('hostnameBlacklist', [])

            parameterExpressions = {}
            parameterExpressionsList = form.get('parameterExpressions', [])

            for line in parameterExpressionsList:
                try:
                    name, expression = line.split('=', 1)
                    parameterExpressions[str(name.strip())] = \
                                                    str(expression.strip())
                except ValueError:
                    self.errors['parameterExpressions'] = \
                                    _('error_invalid_parameter_expressions',
                        default=u"Please ensure you enter one "
                                u"expression per line, in the "
                                u"format <name> = <expression>."
                    )

            themeBase = form.get('themeBase', None)
            markSpecialLinks = form.get('markSpecialLinks', None)
            extLinksOpenInNewWindow = form.get('extLinksOpenInNewWindow', None)
            usePopups = form.get('usePopups', None)
            iconVisibility = form.get('iconVisibility', None)

            if not self.errors:

                # Trigger onDisabled() on plugins if theme was active
                # previously and rules were changed

                if self.settings.rules != rules:
                    applyTheme(None)

                self.settings.enabled = themeEnabled
                self.settings.rules = rules
                self.settings.absolutePrefix = prefix
                self.settings.parameterExpressions = parameterExpressions
                self.settings.hostnameBlacklist = hostnameBlacklist
                self.settings.doctype = doctype

                # Theme base settings

                if themeBase is not None:
                    self.skinsSettings.theme = themeBase.encode('utf-8')
                if markSpecialLinks is not None:
                    self.skinsSettings.mark_special_links = markSpecialLinks
                if extLinksOpenInNewWindow is not None:
                    self.skinsSettings.ext_links_open_new_window = extLinksOpenInNewWindow
                if usePopups is not None:
                    self.skinsSettings.use_popups = usePopups
                if iconVisibility is not None:
                    self.skinsSettings.icon_visibility = iconVisibility.encode('utf-8')

                IStatusMessage(self.request).add(_(u"Changes saved"))
                self._setup()
                return True
            else:
                IStatusMessage(self.request).add(_(u"There were errors"), 'error')
                self.redirectToFieldset('advanced')
                return False

        if 'form.button.Import' in form:
            self.authorize()

            enableNewTheme = form.get('enableNewTheme', False)
            replaceExisting = form.get('replaceExisting', False)
            themeArchive = form.get('themeArchive', None)

            themeZip = None
            performImport = False

            try:
                themeZip = zipfile.ZipFile(themeArchive)
            except (zipfile.BadZipfile, zipfile.LargeZipFile,):
                logger.exception("Could not read zip file")
                self.errors['themeArchive'] = _('error_invalid_zip',
                        default=u"The uploaded file is not a valid Zip archive"
                    )

            if themeZip:

                try:
                    themeData = extractThemeInfo(themeZip, checkRules=False)
                except (ValueError, KeyError,), e:
                    logger.warn(str(e))
                    self.errors['themeArchive'] = _('error_no_rules_file',
                            u"The uploaded file does not contain "
                            u"a valid theme archive."
                        )
                else:

                    themeContainer = getOrCreatePersistentResourceDirectory()
                    themeExists = themeData.__name__ in themeContainer

                    if themeExists:
                        if not replaceExisting:
                            self.errors['themeArchive'] = \
                                _('error_already_installed',
                                    u"This theme is already installed. "
                                    u"Select 'Replace existing theme' "
                                    u"and re-upload to replace it."
                                )
                        else:
                            del themeContainer[themeData.__name__]
                            performImport = True
                    else:
                        performImport = True

            if performImport:
                themeContainer.importZip(themeZip)

                themeDirectory = queryResourceDirectory(THEME_RESOURCE_NAME, themeData.__name__)
                if themeDirectory is not None:

                    # If we don't have a rules file, use the template
                    if themeData.rules == u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, themeData.__name__, RULE_FILENAME,):
                        if not themeDirectory.isFile(RULE_FILENAME):
                            templateThemeDirectory = queryResourceDirectory(THEME_RESOURCE_NAME, TEMPLATE_THEME)
                            themeDirectory.writeFile(RULE_FILENAME, templateThemeDirectory.readFile(RULE_FILENAME))

                            if not themeDirectory.isFile(DEFAULT_THEME_FILENAME):
                                IStatusMessage(self.request).add(
                                        _(u"A boilerplate rules.xml was added to your theme, but no index.html file found. Update rules.xml to reference the current theme file."),
                                        'warning',
                                    )

                    plugins = getPlugins()
                    pluginSettings = getPluginSettings(themeDirectory, plugins)
                    if pluginSettings is not None:
                        for name, plugin in plugins:
                            plugin.onCreated(themeData.__name__,
                                             pluginSettings[name],
                                             pluginSettings)

                if enableNewTheme:
                    applyTheme(themeData)
                    self.settings.enabled = True

            if not self.errors:
                portalUrl = getToolByName(self.context, 'portal_url')()
                self.redirect(
                    "%s/++theme++%s/@@theming-controlpanel-mapper" % (
                        portalUrl, themeData.__name__,)
                    )
                return False
            else:
                IStatusMessage(self.request).add(
                        _(u"There were errors"), "error"
                    )

                self.renderOverlay('upload')
                return True

        if 'form.button.CreateTheme' in form:
            self.authorize()

            title = form.get('title')
            description = form.get('description') or ''
            baseOn = form.get('baseOn', TEMPLATE_THEME)
            enableImmediately = form.get('enableImmediately', True)

            if not title:
                self.errors['title'] = _(u"Title is required")

                IStatusMessage(self.request).add(_(u"There were errors"), 'error')

                self.renderOverlay('new-theme')
                return True

            else:
                name = createThemeFromTemplate(title, description, baseOn)
                self._setup()

                if enableImmediately:
                    themeData = self.getThemeData(self.availableThemes, name)
                    applyTheme(themeData)
                    self.settings.enabled = True

                portalUrl = getToolByName(self.context, 'portal_url')()
                self.redirect(
                    "%s/++theme++%s/@@theming-controlpanel-mapper" % (
                        portalUrl, name,)
                    )
                return False

        if 'form.button.DeleteSelected' in form:
            self.authorize()

            toDelete = form.get('themes', [])
            themeDirectory = getOrCreatePersistentResourceDirectory()

            for theme in toDelete:
                del themeDirectory[theme]

            IStatusMessage(self.request).add(_(u"Theme deleted"), 'info')

            self._setup()
            return True

        return True

    def getSelectedTheme(self, themes, rules):
        for item in themes:
            if item.rules == rules:
                return item.__name__
        return None

    def getThemeData(self, themes, themeSelection):
        for item in themes:
            if item.__name__ == themeSelection:
                return item
        return None

    @memoize
    def themeList(self):
        themes = []
        zodbNames = [t.__name__ for t in self.zodbThemes]

        portalUrl = getToolByName(self.context, 'portal_url')()

        for theme in self.availableThemes:
            if theme.__name__ == TEMPLATE_THEME:
                continue

            previewUrl = "++resource++plone.app.theming/defaultPreview.png"
            if theme.preview:
                previewUrl = "++theme++%s/%s" % (theme.__name__, theme.preview,)

            themes.append({
                'name': theme.__name__,
                'title': theme.title,
                'description': theme.description,
                'editable': theme.__name__ in zodbNames,
                'preview': "%s/%s" % (portalUrl, previewUrl,),
                'selected': theme.__name__ == self.selectedTheme,
            })

        themes.sort(key=lambda x: x['title'])

        return themes

    def redirectToFieldset(self, fieldset):
        portalUrl = getToolByName(self.context, 'portal_url')()
        self.redirect("%s/%s#fieldsetlegend-%s" % (
            portalUrl, self.__name__, fieldset,))

    def renderOverlay(self, overlay):
        self.overlay = overlay

    def authorize(self):
        return authorize(self.context, self.request)