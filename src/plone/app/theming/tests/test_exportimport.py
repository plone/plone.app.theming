import unittest2 as unittest

from plone.app.theming.testing import THEMING_INTEGRATION_TESTING

class TestExportImport(unittest.TestCase):

    layer = THEMING_INTEGRATION_TESTING

    def test_import_filesystem(self):
        from plone.app.theming.interfaces import IThemeSettingsLookup
        from plone.app.theming.exportimport.handler import importTheme

        class FauxContext(object):

            def getLogger(self, name):
                import logging
                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == 'theme.xml'
                return "<theme><name>plone.app.theming.tests</name></theme>"

        importTheme(FauxContext())

        settings = IThemeSettingsLookup(self.layer['portal'])

        self.assertEqual(settings.rules, '/++theme++plone.app.theming.tests/rules.xml')
        self.assertEqual(settings.absolutePrefix, '/++theme++plone.app.theming.tests')
        self.assertEqual(settings.parameterExpressions, {'foo': "python:request.get('bar')"})

    def test_import_no_file(self):
        from plone.app.theming.interfaces import IThemeSettingsLookup
        from plone.app.theming.exportimport.handler import importTheme

        class FauxContext(object):

            def getLogger(self, name):
                import logging
                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == 'theme.xml'
                return None

        importTheme(FauxContext())

        settings = IThemeSettingsLookup(self.layer['portal'])

        self.assertEqual(settings.rules, None)
        self.assertEqual(settings.absolutePrefix, None)
        self.assertEqual(settings.parameterExpressions, {})

    def test_import_not_found(self):
        from plone.app.theming.exportimport.handler import importTheme

        class FauxContext(object):

            def getLogger(self, name):
                import logging
                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == 'theme.xml'
                return "<theme><name>invalid-theme-name</name></theme>"

        self.assertRaises(ValueError, importTheme, FauxContext())

    def test_import_enable(self):
        from plone.app.theming.interfaces import IThemeSettingsLookup
        from plone.app.theming.exportimport.handler import importTheme

        class FauxContext(object):

            def getLogger(self, name):
                import logging
                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == 'theme.xml'
                return "<theme><enabled>true</enabled></theme>"

        settings = IThemeSettingsLookup(self.layer['portal'])

        self.assertEqual(settings.enabled, False)

        importTheme(FauxContext())

        self.assertEqual(settings.enabled, True)

    def test_import_disable(self):
        from plone.app.theming.interfaces import IThemeSettingsLookup
        from plone.app.theming.exportimport.handler import importTheme

        class FauxContext(object):

            def getLogger(self, name):
                import logging
                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == 'theme.xml'
                return "<theme><enabled>false</enabled></theme>"

        settings = IThemeSettingsLookup(self.layer['portal'])

        settings.enabled = True

        importTheme(FauxContext())

        self.assertEqual(settings.enabled, False)
