# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.decode import processInputs
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFPlone.interfaces import ILinkSchema
from plone.app.theming.interfaces import DEFAULT_THEME_FILENAME
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import TEMPLATE_THEME
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import _
from plone.app.theming.plugins.utils import getPluginSettings
from plone.app.theming.plugins.utils import getPlugins
from plone.app.theming.utils import theming_policy
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import createThemeFromTemplate
from plone.app.theming.utils import extractThemeInfo
from plone.app.theming.utils import getAvailableThemes
from plone.app.theming.utils import getOrCreatePersistentResourceDirectory
from plone.app.theming.utils import getZODBThemes
from plone.memoize.instance import memoize
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.publisher.browser import BrowserView
from zope.schema.interfaces import IVocabularyFactory
import logging
import zipfile

logger = logging.getLogger('plone.app.theming')


def authorize(context, request):
    authenticator = getMultiAdapter((context, request), name=u"authenticator")
    if not authenticator.verify():
        raise Unauthorized


class ThemingControlpanel(BrowserView):

    def __call__(self):
        self.pskin = getToolByName(self.context, 'portal_skins')

        if self.update():
            return self.index()
        return ''

    def _setup(self):
        registry = getUtility(IRegistry)
        self.theme_settings = registry.forInterface(IThemeSettings, False)
        self.link_settings = registry.forInterface(ILinkSchema,
                                                   prefix="plone",
                                                   check=False)
        self.zodbThemes = getZODBThemes()
        self.availableThemes = getAvailableThemes()
        self.selectedTheme = self.getSelectedTheme(
            self.availableThemes,
            self.theme_settings.rules
        )
        self.overlay = ''

        self.skinsVocabulary = getUtility(
            IVocabularyFactory,
            name='plone.app.vocabularies.Skins'
        )(
            self.context
        )

        # Set response header to make sure control panel is never themed
        self.request.response.setHeader('X-Theme-Disabled', '1')

    def redirect(self, url):
        self.request.response.redirect(url)

    def get_mark_special_links(self):
        return self.link_settings.mark_special_links

    def set_mark_special_links(self, value):
        self.link_settings.mark_special_links = value

    mark_special_links = property(get_mark_special_links,
                                  set_mark_special_links)

    def get_ext_links_open_new_window(self):
        return self.link_settings.external_links_open_new_window

    def set_ext_links_open_new_window(self, value):
        self.link_settings.external_links_open_new_window = value

    ext_links_open_new_window = property(get_ext_links_open_new_window,
                                         set_ext_links_open_new_window)

    def update(self):
        # XXX: complexity too high: refactoring needed
        processInputs(self.request)
        self._setup()
        self.errors = {}
        form = self.request.form

        if 'form.button.Cancel' in form:
            IStatusMessage(self.request).add(_(u"Changes cancelled"))

            portalUrl = getToolByName(self.context, 'portal_url')()
            self.redirect("{0:s}/plone_control_panel".format(portalUrl))

            return False

        if 'form.button.Enable' in form:
            self.authorize()

            themeSelection = form.get('themeName', None)

            if themeSelection:
                themeData = self.getThemeData(
                    self.availableThemes,
                    themeSelection
                )
                applyTheme(themeData)
                self.theme_settings.enabled = True

            IStatusMessage(
                self.request
            ).add(
                _(
                    u"Theme enabled. Note that this control panel page is "
                    u"never themed."
                )
            )
            self._setup()
            return True

        if 'form.button.InvalidateCache' in form:
            self.authorize()
            policy = theming_policy()
            policy.invalidateCache()
            return True

        if 'form.button.Disable' in form:
            self.authorize()

            applyTheme(None)
            self.theme_settings.enabled = False

            IStatusMessage(self.request).add(_(u"Theme disabled."))
            self._setup()
            return True

        if 'form.button.AdvancedSave' in form:
            self.authorize()

            self.theme_settings.readNetwork = form.get('readNetwork', False)

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
                    name = str(name.strip())
                    expression = str(expression.strip())
                    parameterExpressions[name] = expression
                except ValueError:
                    message = _(
                        'error_invalid_parameter_expressions',
                        default=u"Please ensure you enter one expression per "
                                u"line, in the format <name> = <expression>."
                        )
                    self.errors['parameterExpressions'] = message

            themeBase = form.get('themeBase', None)
            markSpecialLinks = form.get('markSpecialLinks', None)
            extLinksOpenInNewWindow = form.get('extLinksOpenInNewWindow', None)

            if not self.errors:
                # Trigger onDisabled() on plugins if theme was active
                # previously and rules were changed
                if self.theme_settings.rules != rules:
                    applyTheme(None)

                self.theme_settings.enabled = themeEnabled
                self.theme_settings.rules = rules
                self.theme_settings.absolutePrefix = prefix
                self.theme_settings.parameterExpressions = parameterExpressions
                self.theme_settings.hostnameBlacklist = hostnameBlacklist
                self.theme_settings.doctype = doctype

                # Theme base settings
                if themeBase is not None:
                    self.pskin.default_skin = themeBase.encode('utf-8')
                if markSpecialLinks is not None:
                    self.mark_special_links = markSpecialLinks
                if extLinksOpenInNewWindow is not None:
                    self.ext_links_open_new_window = extLinksOpenInNewWindow

                IStatusMessage(self.request).add(_(u"Changes saved"))
                self._setup()
                return True
            else:
                IStatusMessage(self.request).add(
                    _(u"There were errors"), 'error'
                )
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
                self.errors['themeArchive'] = _(
                    'error_invalid_zip',
                    default=u"The uploaded file is not a valid Zip archive"
                )

            if themeZip:

                try:
                    themeData = extractThemeInfo(themeZip, checkRules=False)
                except (ValueError, KeyError,), e:
                    logger.warn(str(e))
                    self.errors['themeArchive'] = _(
                        'error_no_rules_file',
                        u"The uploaded file does not contain a valid theme "
                        u"archive."
                    )
                else:

                    themeContainer = getOrCreatePersistentResourceDirectory()
                    themeExists = themeData.__name__ in themeContainer

                    if themeExists:
                        if not replaceExisting:
                            self.errors['themeArchive'] = _(
                                'error_already_installed',
                                u"This theme is already installed. Select "
                                u"'Replace existing theme' and re-upload to "
                                u"replace it."
                            )
                        else:
                            del themeContainer[themeData.__name__]
                            performImport = True
                    else:
                        performImport = True

            if performImport:
                themeContainer.importZip(themeZip)

                themeDirectory = queryResourceDirectory(
                    THEME_RESOURCE_NAME,
                    themeData.__name__
                )
                if themeDirectory is not None:
                    # If we don't have a rules file, use the template
                    if themeData.rules == u"/++{0:s}++{1:s}/{2:s}".format(
                        THEME_RESOURCE_NAME,
                        themeData.__name__,
                        RULE_FILENAME,
                    ) and not themeDirectory.isFile(RULE_FILENAME):
                        templateThemeDirectory = queryResourceDirectory(
                            THEME_RESOURCE_NAME,
                            TEMPLATE_THEME
                        )
                        themeDirectory.writeFile(
                            RULE_FILENAME,
                            templateThemeDirectory.readFile(RULE_FILENAME)
                        )

                        if not themeDirectory.isFile(DEFAULT_THEME_FILENAME):
                            IStatusMessage(self.request).add(
                                _(
                                    u"A boilerplate rules.xml was added to "
                                    u"your theme, but no index.html file "
                                    u"found. Update rules.xml to reference "
                                    u"the current theme file."
                                ),
                                'warning',
                            )

                    plugins = getPlugins()
                    pluginSettings = getPluginSettings(themeDirectory, plugins)
                    if pluginSettings is not None:
                        for name, plugin in plugins:
                            plugin.onCreated(
                                themeData.__name__,
                                pluginSettings[name],
                                pluginSettings
                            )

                if enableNewTheme:
                    applyTheme(themeData)
                    self.theme_settings.enabled = True

            if not self.errors:
                portalUrl = getToolByName(self.context, 'portal_url')()
                self.redirect(
                    "{0}/++theme++{1}/@@theming-controlpanel-mapper".format(
                        portalUrl,
                        themeData.__name__
                    )
                )
                return False
            else:
                IStatusMessage(self.request).add(
                    _(u"There were errors"),
                    "error"
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

                IStatusMessage(self.request).add(
                    _(u"There were errors"),
                    'error'
                )

                self.renderOverlay('new-theme')
                return True

            else:

                if any(x.__name__ == title for x in getZODBThemes()):
                    self.errors['title'] = _(u"Duplicate title")

                    IStatusMessage(self.request).add(
                        _(u"This title is already in use"),
                        'error'
                    )

                    return True

                name = createThemeFromTemplate(title, description, baseOn)
                self._setup()

                if enableImmediately:
                    themeData = self.getThemeData(self.availableThemes, name)
                    applyTheme(themeData)
                    self.theme_settings.enabled = True

                portalUrl = getToolByName(self.context, 'portal_url')()
                self.redirect(
                    "{0}/++theme++{1}/@@theming-controlpanel-mapper".format(
                        portalUrl,
                        name
                    )
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

        complete = [];
        active_theme = None

        for theme in self.availableThemes:
            if theme.__name__ == TEMPLATE_THEME:
                continue

            #We've overwritten this theme, skip it
            if complete.__contains__(theme.__name__):
                continue

            override = False

            #Is there more than one theme with the same name?
            if len( filter(lambda x: x.__name__ == theme.__name__, self.availableThemes) ) > 1:
                #Then we make sure we're using the TTW version, not the filesystem version.
                theme = filter(lambda x: x.__name__ == theme.__name__, self.zodbThemes)[0]
                override = True

            previewUrl = "++resource++plone.app.theming/defaultPreview.png"
            if theme.preview:
                previewUrl = "++theme++{0:s}/{1:s}".format(
                    theme.__name__,
                    theme.preview,
                )

            theme_data = {
                'name': theme.__name__,
                'title': theme.title,
                'description': theme.description,
                'override': override,
                'editable': theme.__name__ in zodbNames,
                'preview': "{0}/{1}".format(portalUrl, previewUrl),
                'selected': theme.__name__ == self.selectedTheme,
            }
            if theme.__name__ == self.selectedTheme:
                active_theme = theme_data
            else:
                themes.append(theme_data)

            complete.append(theme.__name__)

        themes.sort(key=lambda x: x['title'])
        if active_theme:
            themes.insert(0, active_theme)

        return themes

    def redirectToFieldset(self, fieldset):
        portalUrl = getToolByName(self.context, 'portal_url')()
        self.redirect(
            "{0}/{1}#fieldsetlegend-{2}".format(
                portalUrl,
                self.__name__,
                fieldset
            )
        )

    def renderOverlay(self, overlay):
        self.overlay = overlay

    def authorize(self):
        return authorize(self.context, self.request)
