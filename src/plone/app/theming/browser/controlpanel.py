# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from datetime import datetime
from plone.app.theming.interfaces import _
from plone.app.theming.interfaces import DEFAULT_THEME_FILENAME
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import TEMPLATE_THEME
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.plugins.utils import getPlugins
from plone.app.theming.plugins.utils import getPluginSettings
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import createThemeFromTemplate
from plone.app.theming.utils import extractThemeInfo
from plone.app.theming.utils import getAvailableThemes
from plone.app.theming.utils import getOrCreatePersistentResourceDirectory
from plone.app.theming.utils import getZODBThemes
from plone.app.theming.utils import theming_policy
from plone.memoize.instance import memoize
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.utils import safe_nativestring
from Products.CMFPlone.interfaces import ILinkSchema
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.publisher.browser import BrowserView
from zope.schema.interfaces import IVocabularyFactory

import logging
import six
import zipfile


try:
    # Zope 4
    from Products.Five.browser.decode import processInputs
except ImportError:
    # Zope 5
    processInputs = None


logger = logging.getLogger('plone.app.theming')


def authorize(context, request):
    authenticator = getMultiAdapter((context, request), name=u"authenticator")
    if not authenticator.verify():
        raise Unauthorized


class ThemingControlpanel(BrowserView):

    @property
    def site_url(self):
        """Return the absolute URL to the current site, which is likely not
        necessarily the portal root.
        """
        return getSite().absolute_url()

    @property
    def hostname_blacklist(self):
        hostname_blacklist = self.request.get('hostnameBlacklist', [])
        if six.PY2:
            return hostname_blacklist
        return [safe_nativestring(host) for host in hostname_blacklist]

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
            self.theme_settings.currentTheme,
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
        if processInputs is not None:
            processInputs(self.request)
        self._setup()
        self.errors = {}
        form = self.request.form

        if 'form.button.Cancel' in form:
            IStatusMessage(self.request).add(_(u"Changes cancelled"))
            self.redirect("{0}/@@overview-controlpanel".format(self.site_url))
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

            custom_css = form.get('custom_css', b'')

            if not self.errors:
                # Trigger onDisabled() on plugins if theme was active
                # previously and rules were changed
                if self.theme_settings.rules != rules:
                    applyTheme(None)

                self.theme_settings.enabled = themeEnabled
                self.theme_settings.rules = rules
                self.theme_settings.absolutePrefix = prefix
                self.theme_settings.parameterExpressions = parameterExpressions
                self.theme_settings.hostnameBlacklist = self.hostname_blacklist
                if custom_css != self.theme_settings.custom_css:
                    self.theme_settings.custom_css_timestamp = datetime.now()
                self.theme_settings.custom_css = custom_css
                self.theme_settings.doctype = doctype

                # Theme base settings
                if themeBase is not None:
                    if six.PY2:
                        themeBase = themeBase.encode('utf-8')
                    self.pskin.default_skin = themeBase
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
            except (zipfile.BadZipfile, zipfile.LargeZipFile):
                logger.exception("Could not read zip file")
                self.errors['themeArchive'] = _(
                    'error_invalid_zip',
                    default=u"The uploaded file is not a valid Zip archive"
                )

            if themeZip:

                try:
                    themeData = extractThemeInfo(themeZip, checkRules=False)
                except (ValueError, KeyError) as e:
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
                self.redirect(
                    "{0}/++theme++{1}/@@theming-controlpanel-mapper".format(
                        self.site_url,
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

                self.redirect(
                    "{0}/++theme++{1}/@@theming-controlpanel-mapper".format(
                        self.site_url,
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

    def getSelectedTheme(self, themes, themeName, rules):
        for item in themes:
            if item.__name__ == themeName:
                return item.__name__

        # BBB: If currentTheme isn't set, look for a theme with a rules file
        # matching that of the current theme. Same as what policy does
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

        complete = []
        active_theme = None

        for theme in self.availableThemes:
            if theme.__name__ == TEMPLATE_THEME:
                continue

            # We've overwritten this theme, skip it
            if complete.__contains__(theme.__name__):
                continue

            override = False

            # Is there more than one theme with the same name?
            if len([x for x in self.availableThemes if x.__name__ == theme.__name__]) > 1:
                # Then we make sure we're using the TTW version, not the filesystem version.
                try:
                    theme = list(filter(lambda x: x.__name__ == theme.__name__, self.zodbThemes))[0]
                    override = True
                # Or when TTW is not available, the first available filesystem version.
                except IndexError:
                    theme = list(filter(lambda x: x.__name__ == theme.__name__, self.availableThemes))[0]

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
                'preview': "{0}/{1}".format(self.site_url, previewUrl),
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
        self.redirect(
            "{0}/{1}#fieldsetlegend-{2}".format(
                self.site_url,
                self.__name__,
                fieldset
            )
        )

    def renderOverlay(self, overlay):
        self.overlay = overlay

    def authorize(self):
        return authorize(self.context, self.request)
