from plone.app.theming.testing import THEMING_INTEGRATION_TESTING

import unittest


class TestExportImport(unittest.TestCase):
    layer = THEMING_INTEGRATION_TESTING

    def test_import_filesystem(self):
        from plone.app.theming.exportimport.handler import importTheme
        from plone.app.theming.interfaces import IThemeSettings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        class FauxContext:
            def getLogger(self, name):
                import logging

                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == "theme.xml"
                return "<theme><name>plone.app.theming.tests</name></theme>"

        importTheme(FauxContext())

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)

        self.assertEqual(settings.rules, "/++theme++plone.app.theming.tests/rules.xml")
        self.assertEqual(settings.absolutePrefix, "/++theme++plone.app.theming.tests")
        self.assertEqual(
            settings.parameterExpressions, {"foo": "python:request.get('bar')"}
        )

    def test_import_no_file(self):
        from plone.app.theming.exportimport.handler import importTheme
        from plone.app.theming.interfaces import IThemeSettings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        class FauxContext:
            def getLogger(self, name):
                import logging

                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == "theme.xml"
                return None

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        rules = settings.rules
        absolutePrefix = settings.absolutePrefix
        parameterExpressions = settings.parameterExpressions

        importTheme(FauxContext())

        # should be unchanged
        self.assertEqual(settings.rules, rules)
        self.assertEqual(settings.absolutePrefix, absolutePrefix)
        self.assertEqual(settings.parameterExpressions, parameterExpressions)

    def test_import_not_found(self):
        from plone.app.theming.exportimport.handler import importTheme

        class FauxContext:
            def getLogger(self, name):
                import logging

                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == "theme.xml"
                return "<theme><name>invalid-theme-name</name></theme>"

        self.assertRaises(ValueError, importTheme, FauxContext())

    def test_import_enable(self):
        from plone.app.theming.exportimport.handler import importTheme
        from plone.app.theming.interfaces import IThemeSettings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        class FauxContext:
            def getLogger(self, name):
                import logging

                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == "theme.xml"
                return "<theme><enabled>true</enabled></theme>"

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        settings.enabled = False

        importTheme(FauxContext())

        self.assertEqual(settings.enabled, True)

    def test_import_disable(self):
        from plone.app.theming.exportimport.handler import importTheme
        from plone.app.theming.interfaces import IThemeSettings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        class FauxContext:
            def getLogger(self, name):
                import logging

                return logging.getLogger(name)

            def readDataFile(self, name):
                assert name == "theme.xml"
                return "<theme><enabled>false</enabled></theme>"

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)

        settings.enabled = True

        importTheme(FauxContext())

        self.assertEqual(settings.enabled, False)
