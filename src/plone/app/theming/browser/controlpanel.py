import logging
from ConfigParser import SafeConfigParser

from zope.component import getUtility
from zope.publisher.browser import BrowserView

from plone.registry.interfaces import IRegistry

from plone.resource.utils import iterDirectoriesOfType

from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.interfaces import RULE_FILENAME, MANIFEST_FILENAME
from plone.app.theming.interfaces import _

from Products.statusmessages.interfaces import IStatusMessage
from Products.Five.browser.decode import processInputs
from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('plone.app.theming')

class ThemingControlpanel(BrowserView):
    
    def __call__(self):
        if self.update():
            return self.index()
        return ''
    
    def update(self):
        processInputs(self.request)
        
        self.settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        
        self.selectedTheme = None
        self.availableThemes = []
        self.selectedTheme = None
        
        self.errors = {}
        
        form = self.request.form
        
        if 'form.button.Cancel' in form:
            self.redirect(_(u"Changes canceled."))
            return False
        
        self.availableThemes = self.getAvailableThemes()
        self.selectedTheme = self.getSelectedTheme(self.availableThemes, self.settings.rules)
        
        if 'form.button.Save' in form:
            
            self.settings.enabled = form.get('enabled', False)
            self.settings.readNetwork = form.get('readNetwork', False)
            
            rules = form.get('rules', None)
            prefix = form.get('absolutePrefix', None)
            
            # If a theme was selected and it's not the one that was previously
            # selected, let this override the advanced settings
            themeSelection = form.get('selectedTheme', None)
            if themeSelection:
                if self.selectionChanged(self.availableThemes, themeSelection, self.settings.rules):
                    rules, prefix = self.getRulesAndPrefix(self.availableThemes, themeSelection)
            
            self.settings.rules = rules
            self.settings.absolutePrefix = prefix
            
            if not self.errors:
                self.redirect(_(u"Changes saved."))
                return False
        
        return True
    
    def getAvailableThemes(self):
        themes = []
        for directory in iterDirectoriesOfType('theme'):
            if directory.isFile(RULE_FILENAME):
                name = directory.__name__
                title = name.capitalize().replace('-', ' ').replace('.', ' ')
                description = None
                rules = u"/++theme++%s/%s" % (name, RULE_FILENAME,)
                absolutePrefix = u"/++theme++%s" % name
                
                if directory.isFile(MANIFEST_FILENAME):
                    manifest = directory.openFile(MANIFEST_FILENAME)
                    try:
                        parser = SafeConfigParser({
                                'title': title,
                                'description': description,
                                'rules': None,
                                'prefix': absolutePrefix,
                            })
                        parser.readfp(manifest)
                        
                        title = parser.get('theme', 'title')
                        description = parser.get('theme', 'description')
                        manifestRules = parser.get('theme', 'rules')
                        if manifestRules is not None:
                            rules = '/++theme++%s/%s' % (name, manifestRules,)
                        
                        absolutePrefix = parser.get('theme', 'prefix')
                    except:
                        logger.exception("Unable to read manifest for theme directory %s", name)
                    finally:
                        manifest.close()
                
                if isinstance(rules, str):
                    rules = rules.decode('utf-8')
                if isinstance(absolutePrefix, str):
                    absolutePrefix = absolutePrefix.decode('utf-8')
                
                themes.append({
                    'id': name,
                    'title': title,
                    'description': description,
                    'rules': rules,
                    'absolutePrefix': absolutePrefix,
                })
                
        return themes
    
    def getSelectedTheme(self, themes, rules):
        for item in themes:
            if item['rules'] == rules:
                return item['id']
        return False
    
    def selectionChanged(self, themes, themeSelection, rules):
        for item in themes:
            if item['id'] == themeSelection:
                return item['rules'] != rules
        return False
    
    def getRulesAndPrefix(self, themes, themeSelection):
        for item in themes:
            if item['id'] == themeSelection:
                return (item['rules'], item['absolutePrefix'],)
        return None, None
    
    def redirect(self, message):
        IStatusMessage(self.request).add(message)
        portalUrl = getToolByName(self.context, 'portal_url')()
        self.request.response.redirect("%s/plone_control_panel" % portalUrl)
