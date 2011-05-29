import logging
import os.path
import Products.Five.browser.metaconfigure

from ConfigParser import SafeConfigParser

from zope.interface import implements
from zope.interface import Interface

from zope.configuration.config import ConfigurationMachine

from zope.dottedname.resolve import resolve

from plone.resource.utils import queryResourceDirectory

from plone.app.theming.interfaces import IThemePlugin
from plone.app.theming.interfaces import THEME_RESOURCE_NAME

from plone.app.theming.plugins.browserlayer import schemata

EXTENSION = ".pt"
VIEW_CONFIG_FILENAME = "views.cfg"

logger = logging.getLogger(__name__)

class ViewsPlugin(object):
    """This plugin can be used to register any number of browser views from
    a directory containing page templates.
    
    If a directory ``views`` is found inside the theme directory and this
    contains one or more ``.pt`` files, these will be registered as browser
    views for a theme-specific layer. By default, this layer is the dynamic
    one created by the ``browserlayer`` plugin.
    
    Both the (relative) directory name and the layer (dotted) name can be
    override in the manifest if required::
    
        [theme:views]
        directory = view-templates
        layer = my.package.interfaces.ISomeLayer
    
    Each template is registered as a view using the following configuration
    by default::
    
    * The view name is the name of the page template, minus the ``.pt``
      extension.
    * The view is registered for all contexts (``for="*"``)
    * The view requires the permission ``zope2.View``
    
    These defaults can be overridden by placing a file ``views.cfg`` in the
    ``views`` directory. This should contain one section per template, where
    the section name is the template name minus the ``.pt`` extension. The
    valid options in each section are:
    
    * ``name``, to change the view name
    * ``permission``, to give a different permission name
    * ``for``, to change the view's context
    * ``class``, to let the view re-use an existing class
    
    For example::
    
        # for my-view.pt:
        [my-view]
        name = my-view-at-root
        for = Products.CMFCore.interfaces.ISiteRoot
        permission = cmf.ManagePortal
        class = some.package.browser.MyView
    
    All options are optional, as is the ``views.cfg`` file itself.
    """
    
    implements(IThemePlugin)
    
    dependencies = ('browserlayer',)
    
    registered = {}
    
    def onDiscovery(self, theme, settings, dependenciesSettings):
        res = queryResourceDirectory(THEME_RESOURCE_NAME, theme)
        if res is None:
            return
        
        directoryName = 'views'
        if 'directory' in settings:
            directoryName = settings['views']
        
        if res.isDirectory(directoryName):
            viewsDir = res[directoryName]
            
            layer = getattr(schemata, theme, None)
            
            if 'layer' in settings:
                layerName = settings['layer']
            
                try:
                    layer = resolve(layerName)
                except (ImportError, AttributeError,):
                    logger.warn("Could not import %s" % layerName)
                    return
            
            viewConfig = SafeConfigParser()
            
            if viewsDir.isFile(VIEW_CONFIG_FILENAME):
                fp = viewsDir.openFile(VIEW_CONFIG_FILENAME)
                try:
                    viewConfig.readfp(fp)
                finally:
                    try:
                        fp.close()
                    except AttributeError:
                        pass
            
            views = []
            configurationMachine = ConfigurationMachine()
            path = viewsDir.directory
            
            for filename in os.listdir(path):
                if not filename.lower().endswith(EXTENSION):
                    continue
                
                name = viewName = filename[:-3]
                permission = 'zope2.View'
                for_ = Interface
                class_ = None
                template = os.path.join(path, filename)
                
                # Read override options from views.cfg if applicable
                if viewConfig.has_section(name):
                    
                    if viewConfig.has_option(name, 'name'):
                        viewName = viewConfig.get(name, 'name')
                    
                    if viewConfig.has_option(name, 'permission'):
                        permission = viewConfig.get(name, 'permission')
                    
                    if viewConfig.has_option(name, 'for'):
                        forStr = viewConfig.get(name, 'for')
                        if forStr != "*":
                            for_ = resolve(forStr)
                    
                    if viewConfig.has_option(name, 'class'):
                        class_ = resolve(viewConfig.get(name, 'class'))
                
                Products.Five.browser.metaconfigure.page(
                        configurationMachine,
                        name=viewName,
                        permission=permission,
                        for_=for_,
                        layer=layer,
                        template=template,
                        class_=class_,
                    )
                
                views.append(name)
            
            if len(views) > 0:
                configurationMachine.execute_actions()
            
            self.registered[theme] = views

    def onCreated(self, theme, settings, dependenciesSettings):
        pass
    
    def onEnabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onDisabled(self, theme, settings, dependenciesSettings):
        pass
    
    def onRequest(self, request, theme, settings, dependenciesSettings):
        pass
