from plone.app.registry.browser import controlpanel
from plone.app.theming.interfaces import IThemeSettings, _

class ThemeSettingsEditForm(controlpanel.RegistryEditForm):
    
    schema = IThemeSettings
    label = _('theme_settings', u"Theme settings") 
    description = _('use_settings_below',
                    u"Use the settings below to configure a theme for this site")
    
    def updateWidgets(self):
        super(ThemeSettingsEditForm, self).updateWidgets()
        self.widgets['rules'].size = 60
        self.widgets['absolutePrefix'].size = 60
    
class ThemeSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = ThemeSettingsEditForm
