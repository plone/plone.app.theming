import unittest2 as unittest

from plone.app.theming.testing import THEMING_INTEGRATION_TESTING

class TestIntegraiton(unittest.TestCase):
    
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

class TestUnit(unittest.TestCase):

    def test_extractThemeInfo_default_rules(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo
        
        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'default_rules.zip'))
        z = zipfile.ZipFile(f)
        
        theme, rules, prefix = extractThemeInfo(z)
        
        self.assertEqual(theme, 'default_rules')
        self.assertEqual(rules, 'rules.xml')
        self.assertEqual(prefix, '/++theme++default_rules')
        
        f.close()
    
    def test_extractThemeInfo_manifest_rules(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo
        
        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_rules.zip'))
        z = zipfile.ZipFile(f)
        
        theme, rules, prefix = extractThemeInfo(z)
        
        self.assertEqual(theme, 'manifest_rules')
        self.assertEqual(rules, 'other.xml')
        self.assertEqual(prefix, '/++theme++manifest_rules')
        
        f.close()
    
    def test_extractThemeInfo_manifest_prefix(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo
        
        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_prefix.zip'))
        z = zipfile.ZipFile(f)
        
        theme, rules, prefix = extractThemeInfo(z)
        
        self.assertEqual(theme, 'manifest_prefix')
        self.assertEqual(rules, 'rules.xml')
        self.assertEqual(prefix, '/foo')
        
        f.close()
    
    def test_extractThemeInfo_manifest_default_rules(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo
        
        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_default_rules.zip'))
        z = zipfile.ZipFile(f)
        
        theme, rules, prefix = extractThemeInfo(z)
        
        self.assertEqual(theme, 'manifest_default_rules')
        self.assertEqual(rules, 'rules.xml')
        self.assertEqual(prefix, '/++theme++manifest_default_rules')
        
        f.close()
    
    def test_extractThemeInfo_manifest_default_rules_override(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo
        
        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'manifest_default_rules_override.zip'))
        z = zipfile.ZipFile(f)
        
        theme, rules, prefix = extractThemeInfo(z)
        
        self.assertEqual(theme, 'manifest_default_rules_override')
        self.assertEqual(rules, 'other.xml')
        self.assertEqual(prefix, '/++theme++manifest_default_rules_override')
        
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
        
        theme, rules, prefix = extractThemeInfo(z)
        
        self.assertEqual(theme, 'default_rules')
        self.assertEqual(rules, 'rules.xml')
        self.assertEqual(prefix, '/++theme++default_rules')
        
        f.close()
    
    def test_extractThemeInfo_with_subdirectories(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import extractThemeInfo
        
        f = open(os.path.join(os.path.dirname(__file__), 'zipfiles', 'subdirectories.zip'))
        z = zipfile.ZipFile(f)
        
        theme, rules, prefix = extractThemeInfo(z)
        
        self.assertEqual(theme, 'subdirectories')
        self.assertEqual(rules, 'rules.xml')
        self.assertEqual(prefix, '/++theme++subdirectories')
        
        f.close()
    
