from zope.interface import Interface
from zope import schema
from zope.i18nmessageid import MessageFactory

from plone.resource.manifest import ManifestFormat

_ = MessageFactory(u"plone")

THEME_RESOURCE_NAME = 'theme'
RULE_FILENAME = 'rules.xml'
DEFAULT_THEME_FILENAME = 'index.html'
TEMPLATE_THEME = 'template'

MANIFEST_FORMAT = ManifestFormat(THEME_RESOURCE_NAME,
        keys=['title', 'description', 'rules', 'prefix', 'doctype', 'preview'],
        parameterSections=['parameters'],
    )

THEME_EXTENSIONS = frozenset(['html', 'htm'])


class ITheme(Interface):
    """A theme, loaded from a resource directory
    """

    __name__ = schema.TextLine(
            title=_(u"Name"),
        )

    rules = schema.TextLine(
            title=_(u"Path to rules"),
        )

    title = schema.TextLine(
            title=_(u"Title"),
            required=False,
        )

    description = schema.TextLine(
            title=_(u"Description"),
            required=False,
        )

    absolutePrefix = schema.TextLine(
            title=_(u"Absolute prefix"),
            required=False,
        )

    parameterExpressions = schema.Dict(
            title=_(u"Parameter expressions"),
            key_type=schema.TextLine(),
            value_type=schema.TextLine(),
            required=False,
        )

    doctype = schema.ASCIILine(
            title=_(u"Doctype"),
            required=False,
            default="",
        )

    preview = schema.ASCIILine(
            title=_(u"Preview image"),
            required=False,
        )


class IThemeSettings(Interface):
    """Transformation settings
    """

    enabled = schema.Bool(
            title=_('enabled', u"Enabled"),
            description=_('enable_theme_globally',
                          u"Use this option to enable or disable the theme "
                          u"globally. Note that the options will also affect "
                          u"whether the theme is used when this option is "
                          u'enabled.'),
            required=True,
            default=False,
        )

    currentTheme = schema.TextLine(
            title=_('current_theme', u"Current theme"),
            description=_('current_theme_description',
                          u"The name of the current theme, i.e. the one "
                          u"applied most recently."),
            required=True,
        )

    rules = schema.TextLine(
            title=_('rules_file', u"Rules file"),
            description=_('rules_file_path',
                          u"File path to the rules file"),
            required=False,
        )

    absolutePrefix = schema.TextLine(
            title=_('absolute_url_prefix', u"Absolute URL prefix"),
            description=_('convert_relative_url',
                 u"Convert relative URLs in the theme file to absolute paths "
                 u"using this prefix."),
            required=False,
        )

    readNetwork = schema.Bool(
            title=_('readNetwork', u"Read network"),
            description=_('network_urls_allowed',
                          u"If enabled, network (http, https) urls are "
                          u"allowed in the rules file and this config."),
            required=True,
            default=False,
        )

    hostnameBlacklist = schema.List(
            title=_('hostname_blacklist', u"Unthemed host names"),
            description=_('hostname_blacklist_description',
                u"If there are hostnames that you do not want to be themed, "
                u"you can list them here. This is useful during theme "
                u"development, so that you can compare the themed and unthemed "
                u"sites. In some cases, you may also want to provided an "
                u"unthemed host alias for content administrators to be able "
                u"to use 'plain' Plone."),
            value_type=schema.TextLine(),
            required=False,
            default=[u"127.0.0.1"],
        )

    parameterExpressions = schema.Dict(
            title=_('parameter_expressions', u"Parameter expressions"),
            description=_('parameter_expressions_description',
                u"You can define parameters here, which will be passed to "
                u"the compiled theme. In your rules file, you can refer "
                u"to a parameter by $name. Parameters are defined using "
                u"TALES expressions, which should evaluate to a string, "
                u"a number, a boolean or None. Available variables are "
                u"`context`, `request`, `portal`, `portal_state`,  and "
                u"`context_state`."),
            key_type=schema.ASCIILine(),
            value_type=schema.ASCIILine(),
            required=False,
            default={},
        )

    doctype = schema.ASCIILine(
            title=_('doctype', u"Doctype"),
            description=_('doctype_description',
                u'You can specify a Doctype string which will be set on the '
                u'output, for example "<!DOCTYPE html>". '
                u'If left blank the default XHTML 1.0 transitional Doctype '
                u'or that set in the Diazo theme is used.'),
            required=False,
            default="",
        )


class IThemingLayer(Interface):
    """Browser layer used to indicate that plone.app.theming is installed
    """


class IThemePlugin(Interface):
    """Register a named utility providing this interface to create a theme
    plugin.

    The various lifecycle methods will be called with the relevant theme
    name and a dictionary called ``settings`` which reflects any settings for
    this plugin stored in the theme's manifest.

    Plugin settings are found in a section called ``[theme:pluginname]``.

    Plugins may have dependencies. Dependent plugins are invoked after their
    dependencies. The settings of dependencies are passed to lifecycle methods
    in the variable ``dependencySetings``, which is a dictionary of
    dictionaries. The keys are plugin names, and the values equivalent to
    the ``settings`` variable for the corresponding plugin.

    If a given plugin can't be the found, an exception will be thrown during
    activation.
    """

    dependencies = schema.Tuple(
            title=_(u"Dependencies"),
            description=_(u"Plugins on which this plugin depends"),
            value_type=schema.ASCIILine(),
        )

    def onDiscovery(theme, settings, dependenciesSettings):
        """Called when the theme is discovered at startup time. This is
        not applicable for through-the-web/zip-file imported themes!
        """

    def onCreated(theme, settings, dependenciesSettings):
        """Called when the theme is created through the web (or imported
        from a zip file)
        """

    def onEnabled(theme, settings, dependenciesSettings):
        """Called when the theme is enabled through the control panel, either
        because the global "enabled" flag was switched, or because the theme
        was changed.
        """

    def onDisabled(theme, settings, dependenciesSettings):
        """Called when the given theme is disabled through the control panel,
        either because the global "enabled" flag was switched, or because the
        theme was changed.
        """

    def onRequest(request, theme, settings, dependenciesSettings):
        """Called upon traversal into the site when a theme is enabled
        """
