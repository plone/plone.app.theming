import unittest2 as unittest

from plone.app.theming.testing import THEMING_INTEGRATION_TESTING


class TestIntegration(unittest.TestCase):

    layer = THEMING_INTEGRATION_TESTING

    def test_getOrCreatePersistentResourceDirectory_new(self):
        from plone.app.theming.utils import getOrCreatePersistentResourceDirectory

        d = getOrCreatePersistentResourceDirectory()
        self.assertEqual(d.__name__, "theme")

    def test_getOrCreatePersistentResourceDirectory_exists(self):
        from zope.component import getUtility
        from plone.resource.interfaces import IResourceDirectory
        from plone.app.theming.utils import getOrCreatePersistentResourceDirectory

        persistentDirectory = getUtility(IResourceDirectory, name="persistent")
        persistentDirectory.makeDirectory("theme")

        d = getOrCreatePersistentResourceDirectory()
        self.assertEqual(d.__name__, "theme")

    def test_getAvailableThemes(self):
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme

        themes = getAvailableThemes()

        self.assertEqual(len(themes), 3)
        theme = getTheme('plone.app.theming.tests')
        self.assertTrue(theme is not None)
        self.assertEqual(theme.__name__, 'plone.app.theming.tests')
        self.assertEqual(theme.title, 'Test theme')
        self.assertEqual(theme.description, 'A theme for testing')
        self.assertEqual(theme.rules, '/++theme++plone.app.theming.tests/rules.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++plone.app.theming.tests')
        self.assertEqual(theme.parameterExpressions, {'foo': "python:request.get('bar')"})
        self.assertEqual(theme.doctype, "<!DOCTYPE html>")

    def test_getZODBThemes(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import getOrCreatePersistentResourceDirectory
        from plone.app.theming.utils import getZODBThemes

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'default_rules.zip'))

        z = zipfile.ZipFile(f)

        themeContainer = getOrCreatePersistentResourceDirectory()
        themeContainer.importZip(z)

        zodbThemes = getZODBThemes()

        self.assertEqual(len(zodbThemes), 1)

        self.assertEqual(zodbThemes[0].__name__, 'default_rules')
        self.assertEqual(zodbThemes[0].rules, '/++theme++default_rules/rules.xml')
        self.assertEqual(zodbThemes[0].absolutePrefix, '/++theme++default_rules')

        f.close()

    def test_applyTheme(self):
        from zope.component import getUtility

        from plone.registry.interfaces import IRegistry

        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import applyTheme

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)

        theme = None
        for t in getAvailableThemes():
            theme = t
            break

        self.assertEqual(settings.rules, None)
        applyTheme(theme)

        self.assertEqual(settings.rules, theme.rules)
        self.assertEqual(settings.absolutePrefix, theme.absolutePrefix)
        self.assertEqual(settings.parameterExpressions, theme.parameterExpressions)
        self.assertEqual(settings.doctype, theme.doctype)

    def test_applyTheme_None(self):
        from zope.component import getUtility

        from plone.registry.interfaces import IRegistry

        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import applyTheme

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)

        settings.rules = u"/++theme++foo/rules.xml"
        settings.absolutePrefix = u"/++theme++foo"
        settings.parameterExpressions = {}

        applyTheme(None)

        self.assertEqual(settings.rules, None)
        self.assertEqual(settings.absolutePrefix, None)
        self.assertEqual(settings.parameterExpressions, {})


class TestUnit(unittest.TestCase):

    def test_extractThemeInfo_default_rules(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'default_rules.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'default_rules')
        self.assertEqual(theme.rules, u'/++theme++default_rules/rules.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++default_rules')

        f.close()

    def test_extractThemeInfo_manifest_rules(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_rules.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'manifest_rules')
        self.assertEqual(theme.rules, 'other.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++manifest_rules')
        self.assertEqual(theme.title, 'Test theme')

        f.close()

    def test_extractThemeInfo_manifest_prefix(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_prefix.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'manifest_prefix')
        self.assertEqual(theme.rules, u'/++theme++manifest_prefix/rules.xml')
        self.assertEqual(theme.absolutePrefix, '/foo')
        self.assertEqual(theme.title,  'Test theme')

        f.close()

    def test_extractThemeInfo_manifest_default_rules(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_default_rules.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'manifest_default_rules')
        self.assertEqual(theme.rules, u'/++theme++manifest_default_rules/rules.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++manifest_default_rules')
        self.assertEqual(theme.title,  'Test theme')

        f.close()

    def test_extractThemeInfo_manifest_preview(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_preview.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'manifest_preview')
        self.assertEqual(theme.rules, u'/++theme++manifest_preview/rules.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++manifest_preview')
        self.assertEqual(theme.title,  'Test theme')
        self.assertEqual(theme.preview,  'preview.png')

        f.close()

    def test_extractThemeInfo_manifest_default_rules_override(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_default_rules_override.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'manifest_default_rules_override')
        self.assertEqual(theme.rules, 'other.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++manifest_default_rules_override')
        self.assertEqual(theme.title,  'Test theme')

        f.close()

    def test_extractThemeInfo_nodir(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'nodir.zip'))
        z = zipfile.ZipFile(f)

        self.assertRaises(ValueError, extractThemeInfo, z)

        f.close()

    def test_extractThemeInfo_multiple_dir(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'multiple_dir.zip'))
        z = zipfile.ZipFile(f)

        self.assertRaises(ValueError, extractThemeInfo, z)

        f.close()

    def test_extractThemeInfo_ignores_dotfiles_resource_forks(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'ignores_dotfiles_resource_forks.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'default_rules')
        self.assertEqual(theme.rules, u'/++theme++default_rules/rules.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++default_rules')

        f.close()

    def test_extractThemeInfo_with_subdirectories(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo

        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'subdirectories.zip'))
        z = zipfile.ZipFile(f)

        theme = extractThemeInfo(z)

        self.assertEqual(theme.__name__, 'subdirectories')
        self.assertEqual(theme.rules, u'/++theme++subdirectories/rules.xml')
        self.assertEqual(theme.absolutePrefix, '/++theme++subdirectories')

        f.close()
