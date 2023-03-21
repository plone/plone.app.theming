from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.theming.testing import THEMING_FUNCTIONAL_TESTING
from plone.app.theming.testing import THEMING_INTEGRATION_TESTING
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import extractThemeInfo
from plone.app.theming.utils import getTheme
from plone.testing.zope import Browser

import os.path
import tempfile
import transaction
import unittest
import zipfile


# We will try to let the rules file point to a theme on the file system.
# For security reasons, this should not work.
# This is one of the fixes from PloneHotFix20210518.
RULES = """<?xml version="1.0" encoding="UTF-8"?>
<rules
    xmlns="http://namespaces.plone.org/diazo"
    xmlns:css="http://namespaces.plone.org/diazo/css"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
        <theme href="{0}" />
</rules>
"""
# The theme will contain a message:
MESSAGE = "Hello from a temporary directory."
# We have a sample theme file here:
HERE = os.path.dirname(__file__)
PACKAGE_THEME_FILENAME = "package_theme.txt"
PACKAGE_THEME = os.path.join(HERE, PACKAGE_THEME_FILENAME)


class TestIntegration(unittest.TestCase):
    layer = THEMING_INTEGRATION_TESTING

    def test_getOrCreatePersistentResourceDirectory_new(self):
        from plone.app.theming.utils import (  # noqa
            getOrCreatePersistentResourceDirectory,
        )

        d = getOrCreatePersistentResourceDirectory()
        self.assertEqual(d.__name__, "theme")

    def test_getOrCreatePersistentResourceDirectory_exists(self):
        from plone.app.theming.utils import (  # noqa
            getOrCreatePersistentResourceDirectory,
        )
        from plone.resource.interfaces import IResourceDirectory
        from zope.component import getUtility

        persistentDirectory = getUtility(IResourceDirectory, name="persistent")
        persistentDirectory.makeDirectory("theme")

        d = getOrCreatePersistentResourceDirectory()
        self.assertEqual(d.__name__, "theme")

    def test_getAvailableThemes(self):
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme

        themes = getAvailableThemes()

        self.assertTrue(len(themes) >= 3)
        theme = getTheme("plone.app.theming.tests")
        self.assertTrue(theme is not None)
        self.assertEqual(theme.__name__, "plone.app.theming.tests")
        self.assertEqual(theme.title, "Test theme")
        self.assertEqual(theme.description, "A theme for testing")
        self.assertEqual(theme.rules, "/++theme++plone.app.theming.tests/rules.xml")
        self.assertEqual(theme.absolutePrefix, "/++theme++plone.app.theming.tests")
        self.assertEqual(
            theme.parameterExpressions, {"foo": "python:request.get('bar')"}
        )
        self.assertEqual(theme.doctype, "<!DOCTYPE html>")

    def test_getZODBThemes(self):
        from plone.app.theming.utils import (  # noqa
            getOrCreatePersistentResourceDirectory,
        )
        from plone.app.theming.utils import getZODBThemes

        import os.path
        import zipfile

        path = os.path.join(os.path.dirname(__file__), "zipfiles", "default_rules.zip")
        with open(path, "rb") as fp:
            zf = zipfile.ZipFile(fp)

            themeContainer = getOrCreatePersistentResourceDirectory()
            themeContainer.importZip(zf)

            zodbThemes = getZODBThemes()

            self.assertEqual(len(zodbThemes), 1)

            self.assertEqual(zodbThemes[0].__name__, "default_rules")
            self.assertEqual(zodbThemes[0].rules, "/++theme++default_rules/rules.xml")
            self.assertEqual(zodbThemes[0].absolutePrefix, "/++theme++default_rules")

    def test_applyTheme(self):
        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import applyTheme
        from plone.app.theming.utils import getAvailableThemes
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        theme = None
        for t in getAvailableThemes():
            theme = t
            break

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        settings.rules = None

        applyTheme(theme)

        self.assertEqual(settings.rules, theme.rules)
        self.assertEqual(settings.absolutePrefix, theme.absolutePrefix)
        self.assertEqual(settings.parameterExpressions, theme.parameterExpressions)
        self.assertEqual(settings.doctype, theme.doctype)

    def test_applyTheme_None(self):
        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import applyTheme
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)

        settings.rules = "/++theme++foo/rules.xml"
        settings.absolutePrefix = "/++theme++foo"
        settings.parameterExpressions = {}

        applyTheme(None)

        self.assertEqual(settings.rules, None)
        self.assertEqual(settings.absolutePrefix, None)
        self.assertEqual(settings.parameterExpressions, {})

    def test_isThemeEnabled(self):
        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import isThemeEnabled
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        settings.enabled = True
        settings.rules = "/++theme++foo/rules.xml"

        request = self.layer["request"]

        self.assertTrue(isThemeEnabled(request, settings))

    def test_isThemeEnabled_blacklist(self):
        from plone.app.theming.interfaces import IThemeSettings
        from plone.app.theming.utils import isThemeEnabled
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        settings.enabled = True
        settings.rules = "/++theme++foo/rules.xml"

        request = self.layer["request"]
        request.set("BASE1", "http://nohost/path/to/site")

        self.assertTrue(isThemeEnabled(request, settings))
        self.assertEqual(request.get("SERVER_URL"), "http://nohost")

        # Should pay no attention to BASE1 and only use SERVER_URL
        settings.hostnameBlacklist.append("nohost")
        self.assertFalse(isThemeEnabled(request, settings))

    def test_createThemeFromTemplate(self):
        from plone.app.theming.interfaces import RULE_FILENAME
        from plone.app.theming.interfaces import THEME_RESOURCE_NAME
        from plone.app.theming.utils import createThemeFromTemplate
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme

        title = "copy of test theme"
        description = "test theme creation"
        themeName = createThemeFromTemplate(
            title, description, baseOn="plone.app.theming.tests"
        )
        titles = [theme.title for theme in getAvailableThemes()]
        self.assertTrue(title in titles)

        theme = getTheme(themeName)
        expected_prefix = "/++{}++{}".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        self.assertEqual(theme.absolutePrefix, expected_prefix)

        expected_rules = "/++{}++{}/{}".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-"), RULE_FILENAME
        )
        self.assertEqual(theme.rules, expected_rules)

    def test_createThemeFromTemplate_custom_prefix(self):
        from plone.app.theming.interfaces import RULE_FILENAME
        from plone.app.theming.interfaces import THEME_RESOURCE_NAME
        from plone.app.theming.utils import createThemeFromTemplate
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme

        title = "copy of test theme with custom prefix"
        description = "test theme creation"
        themeName = createThemeFromTemplate(
            title, description, baseOn="secondary-theme"
        )
        titles = [theme.title for theme in getAvailableThemes()]
        self.assertTrue(title in titles)

        theme = getTheme(themeName)
        expected_prefix = "/++{}++{}".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        self.assertEqual(theme.absolutePrefix, expected_prefix)

        expected_rules = "/++{}++{}/{}".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-"), RULE_FILENAME
        )
        self.assertEqual(theme.rules, expected_rules)

        self.assertEqual(theme.enabled_bundles, ["plone"])
        self.assertEqual(theme.disabled_bundles, ["foobar"])

        expected_dev_css = "/++{}++{}/css/barceloneta.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_prod_css = "/++{}++{}/css/barceloneta.min.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_tinymce_content_css = "/++{}++{}/css/barceloneta.min.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_tinymce_styles_css = "/++{}++{}/css/custom-format-styles.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        self.assertEqual(theme.development_css, expected_dev_css)
        self.assertEqual(theme.production_css, expected_prod_css)
        self.assertEqual(theme.tinymce_content_css, expected_tinymce_content_css)
        self.assertEqual(theme.tinymce_styles_css, expected_tinymce_styles_css)

        expected_dev_js = "/++{}++{}/script.js".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_prod_js = "/++{}++{}/script.min.js".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        self.assertEqual(theme.development_js, expected_dev_js)
        self.assertEqual(theme.production_js, expected_prod_js)

    def test_createThemeFromTemplate_rel_path(self):
        from plone.app.theming.interfaces import RULE_FILENAME
        from plone.app.theming.interfaces import THEME_RESOURCE_NAME
        from plone.app.theming.utils import createThemeFromTemplate
        from plone.app.theming.utils import getAvailableThemes
        from plone.app.theming.utils import getTheme

        title = "copy of test theme with custom prefix"
        description = "test theme creation"
        themeName = createThemeFromTemplate(title, description, baseOn="another-theme")
        titles = [theme.title for theme in getAvailableThemes()]
        self.assertTrue(title in titles)

        theme = getTheme(themeName)
        expected_prefix = "/++{}++{}".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        self.assertEqual(theme.absolutePrefix, expected_prefix)

        expected_rules = "/++{}++{}/{}".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-"), RULE_FILENAME
        )
        self.assertEqual(theme.rules, expected_rules)

        self.assertEqual(theme.enabled_bundles, ["plone"])
        self.assertEqual(theme.disabled_bundles, ["foobar"])

        expected_dev_css = "++{}++{}/css/barceloneta.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_prod_css = "++{}++{}/css/barceloneta.min.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_tinymce_content_css = "++{}++{}/css/barceloneta.min.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_tinymce_styles_css = "++{}++{}/css/custom-format-styles.css".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        self.assertEqual(theme.development_css, expected_dev_css)
        self.assertEqual(theme.production_css, expected_prod_css)
        self.assertEqual(theme.tinymce_content_css, expected_tinymce_content_css)
        self.assertEqual(theme.tinymce_styles_css, expected_tinymce_styles_css)

        expected_dev_js = "++{}++{}/script.js".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        expected_prod_js = "++{}++{}/script.min.js".format(
            THEME_RESOURCE_NAME, title.replace(" ", "-")
        )
        self.assertEqual(theme.development_js, expected_dev_js)
        self.assertEqual(theme.production_js, expected_prod_js)

    def test_createThemeFromTemplate_ja_str_title(self):
        from plone.app.theming.utils import createThemeFromTemplate

        title = "copy of test theme by 日本語"
        description = "test theme by 日本語"
        try:
            createThemeFromTemplate(title, description, baseOn="another-theme")
        except UnicodeEncodeError:
            self.fail(msg="Unicode Encode Error")

    def test_createThemeFromTemplate_ja_unicode_title(self):
        from plone.app.theming.utils import createThemeFromTemplate

        title = "copy of test theme by 日本語"
        description = "test theme by 日本語"
        try:
            createThemeFromTemplate(title, description, baseOn="another-theme")
        except UnicodeEncodeError:
            self.fail(msg="Unicode Encode Error")


class TestUnit(unittest.TestCase):
    def _open_zipfile(self, filename):
        """Helper that opens a zip file in our test directory"""
        path = os.path.join(os.path.dirname(__file__), "zipfiles", filename)
        return open(path, "rb")

    def test_extractThemeInfo_default_rules(self):
        with self._open_zipfile("default_rules.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "default_rules")
            self.assertEqual(theme.rules, "/++theme++default_rules/rules.xml")
            self.assertEqual(theme.absolutePrefix, "/++theme++default_rules")

    def test_extractThemeInfo_manifest_rules(self):
        with self._open_zipfile("manifest_rules.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "manifest_rules")
            self.assertEqual(theme.rules, "other.xml")
            self.assertEqual(theme.absolutePrefix, "/++theme++manifest_rules")
            self.assertEqual(theme.title, "Test theme")

    def test_extractThemeInfo_manifest_prefix(self):
        with self._open_zipfile("manifest_prefix.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "manifest_prefix")
            self.assertEqual(theme.rules, "/++theme++manifest_prefix/rules.xml")
            self.assertEqual(theme.absolutePrefix, "/foo")
            self.assertEqual(theme.title, "Test theme")

    def test_extractThemeInfo_manifest_default_rules(self):
        with self._open_zipfile("manifest_default_rules.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "manifest_default_rules")
            self.assertEqual(theme.rules, "/++theme++manifest_default_rules/rules.xml")
            self.assertEqual(theme.absolutePrefix, "/++theme++manifest_default_rules")
            self.assertEqual(theme.title, "Test theme")

    def test_extractThemeInfo_manifest_preview(self):
        with self._open_zipfile("manifest_preview.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "manifest_preview")
            self.assertEqual(theme.rules, "/++theme++manifest_preview/rules.xml")
            self.assertEqual(theme.absolutePrefix, "/++theme++manifest_preview")
            self.assertEqual(theme.title, "Test theme")
            self.assertEqual(theme.preview, "preview.png")

    def test_extractThemeInfo_manifest_default_rules_override(self):
        with self._open_zipfile("manifest_default_rules_override.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "manifest_default_rules_override")
            self.assertEqual(theme.rules, "other.xml")
            self.assertEqual(
                theme.absolutePrefix, "/++theme++manifest_default_rules_override"
            )
            self.assertEqual(theme.title, "Test theme")

    def test_extractThemeInfo_nodir(self):
        with self._open_zipfile("nodir.zip") as fp:
            zf = zipfile.ZipFile(fp)
            self.assertRaises(ValueError, extractThemeInfo, zf)

    def test_extractThemeInfo_multiple_dir(self):
        with self._open_zipfile("multiple_dir.zip") as fp:
            zf = zipfile.ZipFile(fp)
            self.assertRaises(ValueError, extractThemeInfo, zf)

    def test_extractThemeInfo_ignores_dotfiles_resource_forks(self):
        with self._open_zipfile("ignores_dotfiles_resource_forks.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "default_rules")
            self.assertEqual(theme.rules, "/++theme++default_rules/rules.xml")
            self.assertEqual(theme.absolutePrefix, "/++theme++default_rules")

    def test_extractThemeInfo_with_subdirectories(self):
        with self._open_zipfile("subdirectories.zip") as fp:
            zf = zipfile.ZipFile(fp)

            theme = extractThemeInfo(zf)

            self.assertEqual(theme.__name__, "subdirectories")
            self.assertEqual(theme.rules, "/++theme++subdirectories/rules.xml")
            self.assertEqual(theme.absolutePrefix, "/++theme++subdirectories")


class TestAttackVector(unittest.TestCase):
    layer = THEMING_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        rules_fd, self.rules_file = tempfile.mkstemp(
            suffix=".xml", prefix="rules", text=True
        )
        with open(self.rules_file, "w") as myfile:
            myfile.write(MESSAGE)

    def tearDown(self):
        os.remove(self.rules_file)

    def get_admin_browser(self):
        browser = Browser(self.layer["app"])
        browser.handleErrors = False
        browser.addHeader(
            "Authorization",
            f"Basic {SITE_OWNER_NAME}:{SITE_OWNER_PASSWORD}",
        )
        return browser

    def get_anon_browser(self):
        browser = Browser(self.layer["app"])
        browser.handleErrors = False
        return browser

    def test_failing_file_protocol_resolver(self):
        from plone.app.theming.utils import FailingFileProtocolResolver

        resolver = FailingFileProtocolResolver()
        with self.assertRaises(ValueError):
            resolver.resolve("file:///etc/passwd", "public_id", "context")
        with self.assertRaises(ValueError):
            resolver.resolve(
                "file:" + os.path.relpath("/etc/passwd"), "public_id", "context"
            )
        with self.assertRaises(ValueError):
            resolver.resolve("file://" + self.rules_file, "public_id", "context")
        with self.assertRaises(ValueError):
            resolver.resolve(
                "file:" + os.path.relpath(self.rules_file), "public_id", "context"
            )

    def test_failing_file_system_resolver(self):
        from plone.app.theming.utils import FailingFileSystemResolver

        resolver = FailingFileSystemResolver()
        with self.assertRaises(ValueError):
            resolver.resolve("/etc/passwd", "public_id", "context")
        with self.assertRaises(ValueError):
            resolver.resolve(os.path.relpath("/etc/passwd"), "public_id", "context")
        with self.assertRaises(ValueError):
            resolver.resolve(self.rules_file, "public_id", "context")
        with self.assertRaises(ValueError):
            resolver.resolve(os.path.relpath(self.rules_file), "public_id", "context")

    def new_theme(self, theme_path):
        from plone.app.theming.utils import createThemeFromTemplate
        from plone.resource.directory import PersistentResourceDirectory

        # Start with an empty theme.
        # Pass title and description
        theme_name = createThemeFromTemplate("Security", "")
        theme = getTheme(theme_name)
        directory = PersistentResourceDirectory()
        directory.writeFile(
            "/".join(["theme", theme_name, "rules.xml"]), RULES.format(theme_path)
        )
        applyTheme(theme)
        transaction.commit()

    def test_theme_file_system_absolute(self):
        self.new_theme(self.rules_file)
        browser = self.get_anon_browser()
        browser.open(self.portal.absolute_url())
        self.assertNotIn(MESSAGE, browser.contents)

    def test_theme_file_system_relative(self):
        self.new_theme(os.path.relpath(self.rules_file))
        browser = self.get_anon_browser()
        browser.open(self.portal.absolute_url())
        self.assertNotIn(MESSAGE, browser.contents)

    def test_theme_file_protocol_absolute(self):
        self.new_theme("file://" + self.rules_file)
        browser = self.get_anon_browser()
        browser.open(self.portal.absolute_url())
        self.assertNotIn(MESSAGE, browser.contents)

    def test_theme_file_protocol_relative(self):
        # This is actually handled by the InternalResolver.
        # Well, in fact it gives an error because it cannot resolve it in the Plone Site:
        # AttributeError: 'PersistentResourceDirectory' object has no attribute 'getPhysicalPath'
        # This can be seen when previewing the theme in the theme editor.
        self.new_theme("file:" + os.path.relpath(self.rules_file))
        browser = self.get_anon_browser()
        browser.open(self.portal.absolute_url())
        self.assertNotIn(MESSAGE, browser.contents)

    def test_theme_python_protocol(self):
        # Since our example rules file is in a Python package,
        # we can use the python resolver to access it.
        # I don't think we can avoid this.
        self.new_theme("python://plone.app.theming/tests/" + PACKAGE_THEME_FILENAME)
        with open(PACKAGE_THEME) as myfile:
            contents = myfile.read()
        browser = self.get_anon_browser()
        browser.open(self.portal.absolute_url())
        self.assertIn(contents, browser.contents)

    def test_available_themes(self):
        """Test that all available themes render properly.

        Our security fixes should not break them.
        """
        from plone.app.theming.utils import getAvailableThemes

        for theme in getAvailableThemes():
            applyTheme(theme)
            transaction.commit()
            # Can you view the portal anonymously?
            browser = self.get_anon_browser()
            browser.open(self.portal.absolute_url())
            # Can you view the portal as admin anonymously?
            browser = self.get_admin_browser()
            browser.open(self.portal.absolute_url())
