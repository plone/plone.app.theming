# -*- coding: utf-8 -*-
from plone.app.theming.testing import THEMING_INTEGRATION_TESTING
from plone.app.theming.utils import extractThemeInfo

import os.path
import unittest
import zipfile


class TestIntegration(unittest.TestCase):

    layer = THEMING_INTEGRATION_TESTING

    def test_getOrCreatePersistentResourceDirectory_new(self):
        from plone.app.theming.utils import getOrCreatePersistentResourceDirectory  # noqa

        d = getOrCreatePersistentResourceDirectory()
        self.assertEqual(d.__name__, "theme")

    def test_getOrCreatePersistentResourceDirectory_exists(self):
        from zope.component import getUtility
        from plone.resource.interfaces import IResourceDirectory
        from plone.app.theming.utils import getOrCreatePersistentResourceDirectory  # noqa

        persistentDirectory = getUtility(IResourceDirectory, name="persistent")
        persistentDirectory.makeDirectory("theme")

        d = getOrCreatePersistentResourceDirectory()
        self.assertEqual(d.__name__, "theme")

    def test_getAvailableThemes(self):
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme

        themes = getAvailableThemes()

        self.assertTrue(len(themes) >= 3)
        theme = getTheme('plone.app.theming.tests')
        self.assertTrue(theme is not None)
        self.assertEqual(theme.__name__, 'plone.app.theming.tests')
        self.assertEqual(theme.title, 'Test theme')
        self.assertEqual(theme.description, 'A theme for testing')
        self.assertEqual(
            theme.rules,
            '/++theme++plone.app.theming.tests/rules.xml'
        )
        self.assertEqual(
            theme.absolutePrefix,
            '/++theme++plone.app.theming.tests'
        )
        self.assertEqual(
            theme.parameterExpressions,
            {'foo': "python:request.get('bar')"}
        )
        self.assertEqual(theme.doctype, "<!DOCTYPE html>")

    def test_getZODBThemes(self):
        import zipfile
        import os.path
        from plone.app.theming.utils import getOrCreatePersistentResourceDirectory  # noqa
        from plone.app.theming.utils import getZODBThemes
        path = os.path.join(
            os.path.dirname(__file__), 'zipfiles', 'default_rules.zip')
        with open(path, 'rb') as fp:
            zf = zipfile.ZipFile(fp)

            themeContainer = getOrCreatePersistentResourceDirectory()
            themeContainer.importZip(zf)

            zodbThemes = getZODBThemes()

            self.assertEqual(len(zodbThemes), 1)

            self.assertEqual(zodbThemes[0].__name__, 'default_rules')
            self.assertEqual(
                zodbThemes[0].rules,
                '/++theme++default_rules/rules.xml'
            )
            self.assertEqual(
                zodbThemes[0].absolutePrefix,
                '/++theme++default_rules'
            )

    def test_applyTheme(self):
        from zope.component import getUtility

        from plone.registry.interfaces import IRegistry

        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import applyTheme

        theme = None
        for t in getAvailableThemes():
            theme = t
            break

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        settings.rules = None

        applyTheme(theme)

        self.assertEqual(settings.rules, theme.rules)
        self.assertEqual(settings.absolutePrefix, theme.absolutePrefix)
        self.assertEqual(
            settings.parameterExpressions,
            theme.parameterExpressions
        )
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

    def test_isThemeEnabled(self):
        from zope.component import getUtility

        from plone.registry.interfaces import IRegistry

        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import isThemeEnabled

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        settings.enabled = True
        settings.rules = u"/++theme++foo/rules.xml"

        request = self.layer['request']

        self.assertTrue(isThemeEnabled(request, settings))

    def test_isThemeEnabled_blacklist(self):
        from zope.component import getUtility

        from plone.registry.interfaces import IRegistry

        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import isThemeEnabled

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        settings.enabled = True
        settings.rules = u"/++theme++foo/rules.xml"

        request = self.layer['request']
        request.set('BASE1', 'http://nohost/path/to/site')

        self.assertTrue(isThemeEnabled(request, settings))
        self.assertEqual(request.get('SERVER_URL'), 'http://nohost')

        # Should pay no attention to BASE1 and only use SERVER_URL
        settings.hostnameBlacklist.append('nohost')
        self.assertFalse(isThemeEnabled(request, settings))

    def test_createThemeFromTemplate(self):
        from plone.app.theming.utils import createThemeFromTemplate
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme
        from plone.app.theming.interfaces import THEME_RESOURCE_NAME
        from plone.app.theming.interfaces import RULE_FILENAME
        title = "copy of test theme"
        description = "test theme creation"
        themeName = createThemeFromTemplate(title, description,
                                            baseOn="plone.app.theming.tests")
        titles = [theme.title for theme in getAvailableThemes()]
        self.assertTrue(title in titles)

        theme = getTheme(themeName)
        expected_prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME,
                                          title.replace(" ", "-"))
        self.assertEqual(theme.absolutePrefix, expected_prefix)

        expected_rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME,
                                            title.replace(" ", "-"),
                                            RULE_FILENAME)
        self.assertEqual(theme.rules, expected_rules)

    def test_createThemeFromTemplate_custom_prefix(self):
        from plone.app.theming.utils import createThemeFromTemplate
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme
        from plone.app.theming.interfaces import THEME_RESOURCE_NAME
        from plone.app.theming.interfaces import RULE_FILENAME
        title = "copy of test theme with custom prefix"
        description = "test theme creation"
        themeName = createThemeFromTemplate(title, description,
                                            baseOn="secondary-theme")
        titles = [theme.title for theme in getAvailableThemes()]
        self.assertTrue(title in titles)

        theme = getTheme(themeName)
        expected_prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME,
                                          title.replace(" ", "-"))
        self.assertEqual(theme.absolutePrefix, expected_prefix)

        expected_rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME,
                                            title.replace(" ", "-"),
                                            RULE_FILENAME)
        self.assertEqual(theme.rules, expected_rules)

        self.assertEqual(theme.enabled_bundles, ['plone'])
        self.assertEqual(theme.disabled_bundles, ['foobar'])

        expected_dev_css = u"/++%s++%s/less/barceloneta.plone.less" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        expected_prod_css = u"/++%s++%s/less/barceloneta-compiled.css" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        expected_tinymce = u"/++%s++%s/less/barceloneta-compiled.css" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        self.assertEqual(theme.development_css, expected_dev_css)
        self.assertEqual(theme.production_css, expected_prod_css)
        self.assertEqual(theme.tinymce_content_css, expected_tinymce)

        expected_dev_js = u"/++%s++%s/script.js" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        expected_prod_js = u"/++%s++%s/script.min.js" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        self.assertEqual(theme.development_js, expected_dev_js)
        self.assertEqual(theme.production_js, expected_prod_js)

    def test_createThemeFromTemplate_rel_path(self):
        from plone.app.theming.utils import createThemeFromTemplate
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme
        from plone.app.theming.interfaces import THEME_RESOURCE_NAME
        from plone.app.theming.interfaces import RULE_FILENAME
        title = "copy of test theme with custom prefix"
        description = "test theme creation"
        themeName = createThemeFromTemplate(title, description,
                                            baseOn="another-theme")
        titles = [theme.title for theme in getAvailableThemes()]
        self.assertTrue(title in titles)

        theme = getTheme(themeName)
        expected_prefix = u"/++%s++%s" % (THEME_RESOURCE_NAME,
                                          title.replace(" ", "-"))
        self.assertEqual(theme.absolutePrefix, expected_prefix)

        expected_rules = u"/++%s++%s/%s" % (THEME_RESOURCE_NAME,
                                           title.replace(" ", "-"),
                                           RULE_FILENAME)
        self.assertEqual(theme.rules, expected_rules)

        self.assertEqual(theme.enabled_bundles, ['plone'])
        self.assertEqual(theme.disabled_bundles, ['foobar'])

        expected_dev_css = u"++%s++%s/less/barceloneta.plone.less" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        expected_prod_css = u"++%s++%s/less/barceloneta-compiled.css" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        expected_tinymce = u"++%s++%s/less/barceloneta-compiled.css" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        self.assertEqual(theme.development_css, expected_dev_css)
        self.assertEqual(theme.production_css, expected_prod_css)
        self.assertEqual(theme.tinymce_content_css, expected_tinymce)

        expected_dev_js = u"++%s++%s/script.js" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        expected_prod_js = u"++%s++%s/script.min.js" % (
            THEME_RESOURCE_NAME, title.replace(" ", "-"))
        self.assertEqual(theme.development_js, expected_dev_js)
        self.assertEqual(theme.production_js, expected_prod_js)

    def test_createThemeFromTemplate_ja_str_title(self):
        from plone.app.theming.utils import createThemeFromTemplate
        title = "copy of test theme by 日本語"
        description = "test theme by 日本語"
        try:
            createThemeFromTemplate(title, description,
                                            baseOn="another-theme")
        except UnicodeEncodeError:
            self.fail(msg=u"Unicode Encode Error")

    def test_createThemeFromTemplate_ja_unicode_title(self):
        from plone.app.theming.utils import createThemeFromTemplate
        title = u"copy of test theme by 日本語"
        description = u"test theme by 日本語"
        try:
            createThemeFromTemplate(title, description,
                                            baseOn="another-theme")
        except UnicodeEncodeError:
            self.fail(msg=u"Unicode Encode Error")


class TestUnit(unittest.TestCase):

    def _open_zipfile(self, filename):
        ''' Helper that opens a zip file in our test directory
        '''
        path = os.path.join(os.path.dirname(__file__), 'zipfiles', filename)
        return open(path, 'rb')

    def test_extractThemeInfo_default_rules(self):
        with self._open_zipfile('default_rules.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'default_rules')
            self.assertEqual(theme.rules, u'/++theme++default_rules/rules.xml')
            self.assertEqual(theme.absolutePrefix, '/++theme++default_rules')

    def test_extractThemeInfo_manifest_rules(self):
        with self._open_zipfile('manifest_rules.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'manifest_rules')
            self.assertEqual(theme.rules, 'other.xml')
            self.assertEqual(theme.absolutePrefix, '/++theme++manifest_rules')
            self.assertEqual(theme.title, 'Test theme')

    def test_extractThemeInfo_manifest_prefix(self):
        with self._open_zipfile('manifest_prefix.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'manifest_prefix')
            self.assertEqual(
                theme.rules,
                u'/++theme++manifest_prefix/rules.xml'
            )
            self.assertEqual(theme.absolutePrefix, '/foo')
            self.assertEqual(theme.title,  'Test theme')

    def test_extractThemeInfo_manifest_default_rules(self):
        with self._open_zipfile('manifest_default_rules.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'manifest_default_rules')
            self.assertEqual(
                theme.rules,
                u'/++theme++manifest_default_rules/rules.xml'
            )
            self.assertEqual(
                theme.absolutePrefix,
                '/++theme++manifest_default_rules'
            )
            self.assertEqual(theme.title,  'Test theme')

    def test_extractThemeInfo_manifest_preview(self):
        with self._open_zipfile('manifest_preview.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'manifest_preview')
            self.assertEqual(
                theme.rules,
                u'/++theme++manifest_preview/rules.xml'
            )
            self.assertEqual(
                theme.absolutePrefix,
                '/++theme++manifest_preview'
            )
            self.assertEqual(theme.title,  'Test theme')
            self.assertEqual(theme.preview,  'preview.png')

    def test_extractThemeInfo_manifest_default_rules_override(self):
        with self._open_zipfile('manifest_default_rules_override.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'manifest_default_rules_override')
            self.assertEqual(theme.rules, 'other.xml')
            self.assertEqual(
                theme.absolutePrefix,
                '/++theme++manifest_default_rules_override'
            )
            self.assertEqual(theme.title,  'Test theme')

    def test_extractThemeInfo_nodir(self):
        with self._open_zipfile('nodir.zip') as fp:
            zf = zipfile.ZipFile(fp)
            self.assertRaises(ValueError, extractThemeInfo, zf)

    def test_extractThemeInfo_multiple_dir(self):
        with self._open_zipfile('multiple_dir.zip') as fp:
            zf = zipfile.ZipFile(fp)
            self.assertRaises(ValueError, extractThemeInfo, zf)

    def test_extractThemeInfo_ignores_dotfiles_resource_forks(self):
        with self._open_zipfile('ignores_dotfiles_resource_forks.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'default_rules')
            self.assertEqual(theme.rules, u'/++theme++default_rules/rules.xml')
            self.assertEqual(theme.absolutePrefix, '/++theme++default_rules')

    def test_extractThemeInfo_with_subdirectories(self):
        with self._open_zipfile('subdirectories.zip') as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, 'subdirectories')
            self.assertEqual(
                theme.rules,
                u'/++theme++subdirectories/rules.xml'
            )
            self.assertEqual(theme.absolutePrefix, '/++theme++subdirectories')
