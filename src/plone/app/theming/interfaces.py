from datetime import datetime
from plone.resource.manifest import ManifestFormat
from zope import schema
from zope.i18nmessageid import MessageFactory
from zope.interface import Attribute
from zope.interface import Interface


_ = MessageFactory("plone")

THEME_RESOURCE_NAME = "theme"
RULE_FILENAME = "rules.xml"
DEFAULT_THEME_FILENAME = "index.html"
TEMPLATE_THEME = "template"

MANIFEST_FORMAT = ManifestFormat(
    THEME_RESOURCE_NAME,
    keys=[
        "title",
        "description",
        "rules",
        "prefix",
        "doctype",
        "preview",
        "enabled-bundles",
        "disabled-bundles",
        "development-css",
        "production-css",
        "tinymce-content-css",
        "tinymce-styles-css",
        "development-js",
        "production-js",
    ],
    parameterSections=["parameters"],
)

THEME_EXTENSIONS = frozenset(["html", "htm"])


def get_default_custom_css_timestamp():
    return datetime.now()


class ITheme(Interface):
    """A theme, loaded from a resource directory"""

    __name__ = schema.TextLine(
        title=_("Name"),
    )

    rules = schema.TextLine(
        title=_("Path to rules"),
    )

    title = schema.TextLine(
        title=_("Title"),
        required=False,
    )

    description = schema.TextLine(
        title=_("Description"),
        required=False,
    )

    absolutePrefix = schema.TextLine(
        title=_("Absolute prefix"),
        required=False,
    )

    parameterExpressions = schema.Dict(
        title=_("Parameter expressions"),
        key_type=schema.TextLine(),
        value_type=schema.TextLine(),
        required=False,
    )

    doctype = schema.ASCIILine(
        title=_("Doctype"),
        required=False,
        default="",
    )

    preview = schema.ASCIILine(
        title=_("Preview image"),
        required=False,
    )


class IThemeSettings(Interface):
    """Transformation settings"""

    enabled = schema.Bool(
        title=_("enabled", "Enabled"),
        description=_(
            "enable_theme_globally",
            "Use this option to enable or disable the theme globally. "
            "Note that the options will also affect whether the theme "
            "is used when this option is enabled.",
        ),
        required=True,
        default=False,
    )

    currentTheme = schema.TextLine(
        title=_("current_theme", "Current theme"),
        description=_(
            "current_theme_description",
            "The name of the current theme, i.e. the one applied most " "recently.",
        ),
        required=True,
    )

    rules = schema.TextLine(
        title=_("rules_file", "Rules file"),
        description=_("rules_file_path", "File path to the rules file"),
        required=False,
    )

    absolutePrefix = schema.TextLine(
        title=_("absolute_url_prefix", "Absolute URL prefix"),
        description=_(
            "convert_relative_url",
            "Convert relative URLs in the theme file to absolute paths "
            "using this prefix.",
        ),
        required=False,
    )

    readNetwork = schema.Bool(
        title=_("readNetwork", "Read network"),
        description=_(
            "network_urls_allowed",
            "If enabled, network (http, https) urls are allowed in "
            "the rules file and this config.",
        ),
        required=True,
        default=False,
    )

    hostnameBlacklist = schema.List(
        title=_("hostname_blacklist", "Unthemed host names"),
        description=_(
            "hostname_blacklist_description",
            "If there are hostnames that you do not want to be themed, you "
            "can list them here. This is useful during theme development, "
            "so that you can compare the themed and unthemed sites. In some "
            "cases, you may also want to provided an unthemed host alias for "
            "content administrators to be able to use 'plain' Plone.",
        ),
        value_type=schema.TextLine(),
        required=False,
        default=["127.0.0.1"],
    )

    parameterExpressions = schema.Dict(
        title=_("parameter_expressions", "Parameter expressions"),
        description=_(
            "parameter_expressions_description",
            "You can define parameters here, which will be passed to the "
            "compiled theme. In your rules file, you can refer to a "
            "parameter by $name. Parameters are defined using TALES "
            "expressions, which should evaluate to a string, a number, a "
            "boolean or None. Available variables are `context`, `request`, "
            "`portal`, `portal_state`,  and `context_state`.",
        ),
        key_type=schema.ASCIILine(),
        value_type=schema.ASCIILine(),
        required=False,
        default={},
    )

    doctype = schema.ASCIILine(
        title=_("doctype", "Doctype"),
        description=_(
            "doctype_description",
            "You can specify a Doctype string which will be set on the "
            'for example "<!DOCTYPE html>". If left blank the default XHTML '
            "1.0 transitional Doctype or that set in the Diazo theme is used.",
        ),
        required=False,
        default="",
    )

    custom_css = schema.SourceText(
        title=_(
            "label_custom_css",
            "Custom CSS",
        ),
        description=_(
            "help_custom_css",
            "Define your own custom CSS in the field below. This is a good "
            "place for quick customizations of things like colors and the "
            "toolbar. Definitions here will override previously defined CSS "
            "of Plone. Please use this only for small customizations, as it "
            "is hard to keep track of changes here. For bigger changes you most "
            "likely want to customize a full theme and make your changes "
            "there.",
        ),
        default="",
        required=False,
    )

    custom_css_timestamp = schema.Datetime(
        title=_(
            "Custom CSS Timestamp",
        ),
        description=_(
            "Time stamp when the custom CSS was changed. "
            "Used to generate custom.css with timestamp in URL.",
        ),
        defaultFactory=get_default_custom_css_timestamp,
        required=False,
    )


class IThemingLayer(Interface):
    """Browser layer used to indicate that plone.app.theming is installed"""


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
        title=_("Dependencies"),
        description=_("Plugins on which this plugin depends"),
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
        """Called upon traversal into the site when a theme is enabled"""


class IThemeAppliedEvent(Interface):
    theme = Attribute("theme that is getting applied")


class INoRequest(Interface):
    """Fallback to enable querying for the policy adapter
    even in the absence of a proper IRequest."""


class IThemingPolicy(Interface):
    """An adapter on request that provides access to the current
    theme and theme settings.
    """

    def getSettings():
        """Settings for current theme."""

    def getCurrentTheme():
        """The name of the current theme."""

    def isThemeEnabled():
        """Whether theming is enabled."""

    def getCache(theme=None):
        """Managing the cache is a policy decision."""

    def getCacheKey(theme=None):
        """Managing the cache is a policy decision."""

    def invalidateCache():
        """When our settings are changed, invalidate the cache on all zeo clients."""

    def get_theme():
        """Returns the current theme object, cached."""

    def set_theme(themeName, themeObj):
        """Update the theme cache."""
