import logging
import zipfile

from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.publisher.browser import BrowserView

from plone.registry.interfaces import IRegistry

from plone.resource.manifest import MANIFEST_FILENAME
from plone.resource.manifest import getZODBResources
from plone.resource.manifest import getAllResources

from plone.app.theming.interfaces import _
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.interfaces import RULE_FILENAME
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import MANIFEST_FORMAT

from plone.app.theming.utils import getOrCreatePersistentResourceDirectory
from plone.app.theming.utils import extractThemeInfo

from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.decode import processInputs
from Products.statusmessages.interfaces import IStatusMessage

logger = logging.getLogger('plone.app.theming')

def isValidThemeDirectory(directory):
    return directory.isFile(MANIFEST_FILENAME) or directory.isFile(RULE_FILENAME)

class ThemingControlpanel(BrowserView):
    
    def __call__(self):
        if self.update():
            return self.index()
        return ''
    
    def update(self):
        processInputs(self.request)
        
        self.settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        
        self.zodbThemes = self.getZODBThemes()
        
        self.selectedTheme = None
        self.availableThemes = []
        self.selectedTheme = None
        
        self.errors = {}
        submitted = False
        
        form = self.request.form
        
        if 'form.button.Cancel' in form:
            self.redirect(_(u"Changes canceled."))
            return False
        
        self.availableThemes = self.getAvailableThemes()
        self.selectedTheme = self.getSelectedTheme(self.availableThemes, self.settings.rules)
        
        if 'form.button.BasicSave' in form:
            self.authorize()
            submitted = True
            
            self.settings.enabled = form.get('enabled', False)
            themeSelection = form.get('selectedTheme', None)
            
            if themeSelection != "_other_":
                rules, prefix = self.getRulesAndPrefix(self.availableThemes, themeSelection)
                
                self.settings.rules = rules
                self.settings.absolutePrefix = prefix
            
        if 'form.button.AdvancedSave' in form:
            self.authorize()
            submitted = True
            
            self.settings.readNetwork = form.get('readNetwork', False)
            
            rules = form.get('rules', None)
            prefix = form.get('absolutePrefix', None)
            
            self.settings.rules = rules
            self.settings.absolutePrefix = prefix
        
        if 'form.button.Import' in form:
            self.authorize()
            submitted = True
            
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
                
                themeName, rulesFile, absolutePrefix = None, None, None
                
                try:
                    themeName, rulesFile, absolutePrefix = extractThemeInfo(themeZip)
                except (ValueError, KeyError,), e:
                    logger.warn(str(e))
                    self.errors['themeArchive'] = _('error_no_rules_file',
                            u"The uploaded file does not contain a valid theme archive."
                        )
                else:
                    
                    themeContainer = getOrCreatePersistentResourceDirectory()
                    themeExists = themeName in themeContainer
                    
                    if themeExists:
                        if not replaceExisting:
                            self.errors['themeArchive'] = _('error_already_installed',
                                    u"This theme is already installed. Select 'Replace existing theme' and re-upload to replace it."
                                )
                        else:
                            del themeContainer[themeName]
                            performImport = True
                    else:
                        performImport = True
                    
            if performImport:
                themeContainer.importZip(themeZip)
        
                if enableNewTheme:
                    self.settings.rules = u"/++theme++%s/%s" % (themeName, rulesFile,)
        
                    if isinstance(absolutePrefix, str):
                        absolutePrefix = absolutePrefix.decode('utf-8')
        
                    self.settings.absolutePrefix = absolutePrefix
                    self.settings.enabled = True
        
        if 'form.button.DeleteSelected' in form:
            self.authorize()
            submitted = True
            
            toDelete = form.get('themes', [])
            themeDirectory = getOrCreatePersistentResourceDirectory()
            
            for theme in toDelete:
                del themeDirectory[theme]
        
        if submitted and not self.errors:
            IStatusMessage(self.request).add(_(u"Changes saved"))
        elif submitted:
            IStatusMessage(self.request).add(_(u"There were errors"), 'error')
        
        return True
    
    def getAvailableThemes(self):
        
        resources = getAllResources(MANIFEST_FORMAT, filter=isValidThemeDirectory)
        themes = []
        for name, manifest in resources.items():
            title = name.capitalize().replace('-', ' ').replace('.', ' ')
            description = None
            rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME, name, RULE_FILENAME,)
            prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME, name,)
            
            if manifest is not None:
                title       = manifest['title'] or title
                description = manifest['description'] or description
                rules       = manifest['rules'] or rules
                prefix      = manifest['prefix'] or prefix
            
            if isinstance(rules, str):
                rules = rules.decode('utf-8')
            if isinstance(prefix, str):
                prefix = prefix.decode('utf-8')
            
            themes.append({
                    'id': name,
                    'title': title,
                    'description': description,
                    'rules': rules,
                    'absolutePrefix': prefix,
                })
        
        themes.sort(key=lambda x: x['title'])
        return themes

    
    def getSelectedTheme(self, themes, rules):
        for item in themes:
            if item['rules'] == rules:
                return item['id']
        return False
    
    def getRulesAndPrefix(self, themes, themeSelection):
        for item in themes:
            if item['id'] == themeSelection:
                return (item['rules'], item['absolutePrefix'],)
        return None, None
    
    def getZODBThemes(self):
        
        resources = getZODBResources(MANIFEST_FORMAT, filter=isValidThemeDirectory)
        themes = []
        for name, manifest in resources.items():
            title = name.capitalize().replace('-', ' ').replace('.', ' ')
            description = None
            
            if manifest is not None:
                title       = manifest['title'] or title
                description = manifest['description'] or description
            
            themes.append({
                    'id': name,
                    'title': title,
                    'description': description,
                })
        
        themes.sort(key=lambda x: x['title'])
        return themes
    
    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized
    
    def redirect(self, message):
        IStatusMessage(self.request).add(message)
        portalUrl = getToolByName(self.context, 'portal_url')()
        self.request.response.redirect("%s/plone_control_panel" % portalUrl)
