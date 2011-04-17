import logging
import zipfile

from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.publisher.browser import BrowserView

from plone.registry.interfaces import IRegistry

from plone.app.theming.interfaces import _
from plone.app.theming.interfaces import IThemeSettings

from plone.app.theming.utils import extractThemeInfo
from plone.app.theming.utils import getZODBThemes
from plone.app.theming.utils import getAvailableThemes
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import getOrCreatePersistentResourceDirectory

from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.decode import processInputs
from Products.statusmessages.interfaces import IStatusMessage

logger = logging.getLogger('plone.app.theming')

class ThemingControlpanel(BrowserView):
    
    def __call__(self):
        if self.update():
            return self.index()
        return ''
    
    def update(self):
        processInputs(self.request)
        
        self.settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        
        self.zodbThemes = getZODBThemes()
        
        self.selectedTheme = None
        self.availableThemes = []
        
        self.errors = {}
        submitted = False
        
        form = self.request.form
        
        if 'form.button.Cancel' in form:
            self.redirect(_(u"Changes canceled."))
            return False
        
        self.availableThemes = getAvailableThemes()
        self.selectedTheme = self.getSelectedTheme(self.availableThemes, self.settings.rules)
        
        if 'form.button.BasicSave' in form:
            self.authorize()
            submitted = True
            
            self.settings.enabled = form.get('enabled', False)
            themeSelection = form.get('selectedTheme', None)
            
            if themeSelection != "_other_":
                themeData = self.getThemeData(self.availableThemes, themeSelection)
                applyTheme(themeData)
            
        if 'form.button.AdvancedSave' in form:
            self.authorize()
            submitted = True
            
            self.settings.readNetwork = form.get('readNetwork', False)
            
            rules = form.get('rules', None)
            prefix = form.get('absolutePrefix', None)
            
            hostnameBlacklist = form.get('hostnameBlacklist', [])
            
            parameterExpressions = {}
            parameterExpressionsList = form.get('parameterExpressions', [])
            
            for line in parameterExpressionsList:
                try:
                    name, expression = line.split('=', 1)
                    parameterExpressions[str(name.strip())] = str(expression.strip())
                except ValueError:
                    self.errors['parameterExpressions'] = _('error_invalid_parameter_expressions', 
                        default=u"Please ensure you enter one expression per line, in the format <name> = <expression>."
                    )
            
            if not self.errors:
                
                self.settings.rules = rules
                self.settings.absolutePrefix = prefix
                self.settings.parameterExpressions = parameterExpressions
                self.settings.hostnameBlacklist = hostnameBlacklist
        
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
                
                try:
                    themeData = extractThemeInfo(themeZip)
                except (ValueError, KeyError,), e:
                    logger.warn(str(e))
                    self.errors['themeArchive'] = _('error_no_rules_file',
                            u"The uploaded file does not contain a valid theme archive."
                        )
                else:
                    
                    themeContainer = getOrCreatePersistentResourceDirectory()
                    themeExists = themeData.__name__ in themeContainer
                    
                    if themeExists:
                        if not replaceExisting:
                            self.errors['themeArchive'] = _('error_already_installed',
                                    u"This theme is already installed. Select 'Replace existing theme' and re-upload to replace it."
                                )
                        else:
                            del themeContainer[themeData.__name__]
                            performImport = True
                    else:
                        performImport = True
                    
            if performImport:
                themeContainer.importZip(themeZip)
                
                if enableNewTheme:
                    applyTheme(themeData)
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
    
    def getSelectedTheme(self, themes, rules):
        for item in themes:
            if item.rules == rules:
                return item.__name__
        return False
    
    def getThemeData(self, themes, themeSelection):
        for item in themes:
            if item.__name__ == themeSelection:
                return item
        return None
    
    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized
    
    def redirect(self, message):
        IStatusMessage(self.request).add(message)
        portalUrl = getToolByName(self.context, 'portal_url')()
        self.request.response.redirect("%s/plone_control_panel" % portalUrl)
