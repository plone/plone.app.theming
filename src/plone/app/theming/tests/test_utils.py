from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.theming.testing import THEMING_FUNCTIONAL_TESTING
from plone.app.theming.testing import THEMING_INTEGRATION_TESTING
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import extractThemeInfo
from plone.app.theming.utils import getTheme
from plone.app.theming.utils import InternalResolver
from plone.base.interfaces import INavigationRoot
from plone.testing.zope import Browser
from Products.CMFCore.utils import getToolByName
from zExceptions import Unauthorized
from zope.interface import alsoProvides

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


class InternalResolverAsString(InternalResolver):
    """InternalResolver with some simplicifications.

    InternalResolver has this main method:

        def resolve(self, system_url, public_id, context):

    At the end it calls:

        return self.resolve_string(result, context)

    This turns a string into some internal lxml document, and I don't know how
    to turn that back into a string for easier testing.  So override that
    method to simply return the original string.
    """

    def resolve_string(self, result, context):
        return result


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


class TestInternalResolverNavigationRoot(unittest.TestCase):
    """Test how the InternalResolver handles navigation roots."""

    layer = THEMING_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

    def resolve(self, system_url):
        """Resolve the system_url.

        The standard resolve method ignores the public_id and the context,
        so I don't want to pass it in all tests.
        """
        resolver = InternalResolverAsString()
        return resolver.resolve(system_url, public_id=None, context=None)

    def setup_public(self):
        # Create a public navigation root containing a public page.
        setRoles(self.portal, TEST_USER_ID, ("Manager",))
        self.portal.invokeFactory("Folder", "public", title="Public Folder")
        folder = self.portal.public
        alsoProvides(folder, INavigationRoot)
        folder.invokeFactory("Document", "page", title="Public page in public folder")
        wftool = getToolByName(self.portal, "portal_workflow")
        wftool.doActionFor(folder, action="publish")
        wftool.doActionFor(folder.page, action="publish")

        # If we want a page in the site root:
        # self.portal.invokeFactory("Document", "page", title="Public page")
        # wftool.doActionFor(self.portal.page, action="publish")
        setRoles(self.portal, TEST_USER_ID, ("Member",))
        return folder

    def setup_private(self):
        # Create a private navigation root containing a public page.
        setRoles(self.portal, TEST_USER_ID, ("Manager",))
        self.portal.invokeFactory("Folder", "private", title="Private Folder")
        folder = self.portal.private
        alsoProvides(folder, INavigationRoot)
        folder.invokeFactory("Document", "page", title="Public page in private folder")
        wftool = getToolByName(self.portal, "portal_workflow")
        wftool.doActionFor(folder.page, action="publish")
        setRoles(self.portal, TEST_USER_ID, ("Member",))
        return folder

    def test_internal_resolver_site_root(self):
        self.request.traverse("/plone")
        # absolute
        self.assertEqual("Plone site", self.resolve("/@@test-title"))
        self.assertIn(
            "A CSS file",
            self.resolve("/++theme++plone.app.theming.tests/resource.css"),
        )
        # relative
        self.assertEqual("Plone site", self.resolve("@@test-title"))
        self.assertIn(
            "A CSS file",
            self.resolve("++theme++plone.app.theming.tests/resource.css"),
        )

    def test_internal_resolver_navigation_root_public(self):
        self.setup_public()
        self.request.traverse("/plone/public")
        # absolute
        self.assertEqual("Public Folder", self.resolve("/@@test-title"))
        self.assertIn(
            "A CSS file",
            self.resolve("/++theme++plone.app.theming.tests/resource.css"),
        )
        # relative
        self.assertEqual("Public Folder", self.resolve("@@test-title"))
        self.assertIn(
            "A CSS file",
            self.resolve("++theme++plone.app.theming.tests/resource.css"),
        )

    def test_internal_resolver_navigation_root_public_page(self):
        self.setup_public()
        self.request.traverse("/plone/public/page")
        # absolute
        self.assertEqual("Public Folder", self.resolve("/@@test-title"))
        self.assertIn(
            "A CSS file",
            self.resolve("/++theme++plone.app.theming.tests/resource.css"),
        )
        # relative
        self.assertEqual("Public page in public folder", self.resolve("@@test-title"))
        self.assertIn(
            "A CSS file",
            self.resolve("++theme++plone.app.theming.tests/resource.css"),
        )

    def test_internal_resolver_navigation_root_private(self):
        self.setup_private()
        # A traverse to "/plone/private" fails, because we are anonymous and
        # cannot access this private navigation root:
        with self.assertRaises(Unauthorized):
            self.request.traverse("/plone/private")
        self.request.traverse("/plone/private/page")
        # An absolute browser view would fail, because we are not authorized
        # to access this view on the private navigation root.  But we fall back
        # to accessing it on the site root.
        self.assertEqual("Plone site", self.resolve("/@@test-title"))
        # A publicly available version of the same browser view works fine though:
        self.assertEqual("Private Folder", self.resolve("/@@test-public-title"))
        # absolute resource
        self.assertIn(
            "A CSS file",
            self.resolve("/++theme++plone.app.theming.tests/resource.css"),
        )
        # relative
        self.assertEqual("Public page in private folder", self.resolve("@@test-title"))
        self.assertIn(
            "A CSS file",
            self.resolve("++theme++plone.app.theming.tests/resource.css"),
        )


class TestUnit(unittest.TestCase):
    def _open_zipfile(self, filename):
        """Helper that opens a zip file in our test directory"""
        path = os.path.join(os.path.dirname(__file__), "zipfiles", filename)
        return open(path, "rb")

    def test_yesno(self):
        """Test the `yesno` utility function with different inputs."""
        from plone.app.theming.utils import yesno

        self.assertTrue(yesno(True))
        self.assertTrue(yesno(1))
        self.assertTrue(yesno("1"))
        self.assertTrue(yesno("TRUE"))
        self.assertTrue(yesno("tRUE"))
        self.assertTrue(yesno("true"))
        self.assertTrue(yesno("y"))
        self.assertTrue(yesno("Y"))
        self.assertTrue(yesno("yEs"))
        self.assertTrue(yesno("yes"))
        self.assertTrue(yesno("on"))

        self.assertFalse(yesno(None))
        self.assertFalse(yesno(False))
        self.assertFalse(yesno(0))
        self.assertFalse(yesno("0"))
        self.assertFalse(yesno("FALSE"))
        self.assertFalse(yesno("fALSE"))
        self.assertFalse(yesno("false"))
        self.assertFalse(yesno("n"))
        self.assertFalse(yesno("NO"))
        self.assertFalse(yesno("no"))

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
