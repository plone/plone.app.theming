from zope.interface import Interface
from zope import schema
from zope.i18nmessageid import MessageFactory

from plone.resource.manifest import ManifestFormat

_ = MessageFactory(u"plone")

THEME_RESOURCE_NAME = 'theme'
RULE_FILENAME = 'rules.xml'

MANIFEST_FORMAT = ManifestFormat(THEME_RESOURCE_NAME,
        keys=['title', 'description', 'rules', 'prefix'],
        parameterSections=['parameters'],
    )

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

class IThemingLayer(Interface):
    """Browser layer used to indicate that plone.app.theming is installed
    """
