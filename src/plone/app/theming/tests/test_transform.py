from App.config import getConfiguration
from diazo.compiler import compile_theme
from lxml import etree
from os import environ
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.testing import THEMING_FUNCTIONAL_TESTING
from plone.app.theming.transform import ThemeTransform
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import getTheme
from plone.app.theming.utils import PythonResolver
from plone.app.theming.utils import resolvePythonURL
from plone.registry.interfaces import IRegistry
from plone.testing.zope import Browser
from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import getExprContext
from Products.CMFCore.utils import getToolByName
from urllib.error import HTTPError
from zope.component import getUtility

import os.path
import re
import transaction
import unittest


class TestCase(unittest.TestCase):
    layer = THEMING_FUNCTIONAL_TESTING

    def setUp(self):
        # Enable debug mode always to ensure cache is disabled by default
        getConfiguration().debug_mode = True

        self.settings = getUtility(IRegistry).forInterface(IThemeSettings)

        self.settings.enabled = False
        self.settings.rules = "python://plone.app.theming/tests/rules.xml"
        self.settings.parameterExpressions = {
            "stringParam": "string:string param value",
            "boolParam": "python:False",
            "contextParam": "context/absolute_url | string:no context",
            "requestParam": "request/useother | string:off",
        }

        transaction.commit()

    def tearDown(self):
        getConfiguration().debug_mode = False

    def evaluate(self, context, expression):
        ec = getExprContext(context, context)
        expr = Expression(expression)
        return expr(ec)

    def test_no_effect_if_not_enabled(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertTrue("Accessibility" in browser.contents)

        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    def test_theme_enabled(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_develop_theme(self):
        """Check if the rules are developed"""
        # First we check the status of our environment variables
        var_name = "DIAZO_ALWAYS_CACHE_RULES"
        env_had_var = var_name in environ
        # and clean it up
        env_var_backup = environ.pop(var_name, None)

        transform = ThemeTransform(None, {})
        # This evaluates to True because we set
        # getConfiguration().debug_mode to True in the test setup
        self.assertTrue(transform.develop_theme())

        # But we can anyway force the cache
        environ[var_name] = "true"
        self.assertFalse(transform.develop_theme())

        # If we require to debug.diazo the variable will be ignored
        transform = ThemeTransform(None, {"diazo.debug": "1"})
        self.assertTrue(transform.develop_theme())

        # Then we reset our env variables before leaving
        if env_had_var:
            environ[var_name] = env_var_backup
        else:
            del environ[var_name]

    def test_theme_enabled_resource_directory(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        theme = getTheme("plone.app.theming.tests")
        applyTheme(theme)
        self.assertEqual(
            self.settings.rules, "/++theme++plone.app.theming.tests/rules.xml"
        )
        self.assertEqual(self.settings.currentTheme, "plone.app.theming.tests")
        self.assertEqual(self.settings.doctype, "<!DOCTYPE html>")
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

        # Doctype
        self.assertTrue(re.match(r"<!DOCTYPE html>\s+<html", browser.contents))

    def test_theme_enabled_query_string_off_switch(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + "?diazo.off=1")

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertTrue("Accessibility" in browser.contents)

        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    def test_theme_enabled_query_string_off_switch_production_mode(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        getConfiguration().debug_mode = False

        self.settings.enabled = True
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + "?diazo.off=1")

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_theme_enabled_header_off(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + "/@@header-disabled")

        self.assertTrue("Theme disabled" in browser.contents)

        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    def test_python_resolver(self):
        # The rules contain a python:// link, so we need a python resolver.
        parser = etree.HTMLParser()
        parser.resolvers.add(PythonResolver())
        theme = resolvePythonURL("python://plone.app.theming.tests/theme.html")
        rules = resolvePythonURL("python://plone.app.theming/tests/rules.xml")
        compile_theme(rules, theme, parser=parser)

    def test_theme_stored_in_plone_site(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        # We'll upload the theme files to the Plone site root
        here = os.path.split(__file__)[0]
        with open(os.path.join(here, "localrules.xml")) as rules_contents:
            portal.manage_addDTMLMethod("rules.xml", file=rules_contents)
        with open(os.path.join(here, "theme.html")) as theme_contents:
            portal.manage_addDTMLMethod("theme.html", file=theme_contents)

        # These paths should be relative to the Plone site root
        self.settings.rules = "/rules.xml"
        self.settings.enabled = True

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_theme_stored_in_plone_site_works_with_virtual_host(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        # We'll upload the theme files to the Plone site root
        here = os.path.split(__file__)[0]
        with open(os.path.join(here, "localrules.xml")) as rules_contents:
            portal.manage_addDTMLMethod("rules.xml", file=rules_contents)
        with open(os.path.join(here, "theme.html")) as theme_contents:
            portal.manage_addDTMLMethod("theme.html", file=theme_contents)

        # These paths should be relative to the Plone site root
        self.settings.rules = "/rules.xml"
        self.settings.enabled = True

        from Products.SiteAccess import VirtualHostMonster

        VirtualHostMonster.manage_addVirtualHostMonster(app, "virtual_hosting")

        transaction.commit()

        portalURL = portal.absolute_url()
        prefix = "/".join(portalURL.split("/")[:-1])
        suffix = portalURL.split("/")[-1]

        vhostURL = (
            "{:s}/VirtualHostBase/http/example.org:80/{:s}/VirtualHostRoot"
            "/_vh_fizz/_vh_buzz/_vh_fizzbuzz/".format(prefix, suffix)
        )

        browser = Browser(app)
        browser.open(vhostURL)

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_absolutePrefix_disabled(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.absolutePrefix = None

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        self.assertTrue('<img src="relative.jpg" />' in browser.contents)

    def test_absolutePrefix_enabled_uri(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.absolutePrefix = "http://example.com"

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        self.assertFalse('<img src="relative.jpg" />' in browser.contents)
        self.assertTrue(
            '<img src="http://example.com/relative.jpg" />' in browser.contents
        )

    def test_absolutePrefix_enabled_path(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.absolutePrefix = "/foo"

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        self.assertFalse('<img src="relative.jpg" />' in browser.contents)
        self.assertTrue('<img src="/plone/foo/relative.jpg" />' in browser.contents)

    def test_absolutePrefix_enabled_path_vhosting(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        from Products.SiteAccess import VirtualHostMonster

        VirtualHostMonster.manage_addVirtualHostMonster(app, "virtual_hosting")

        transaction.commit()

        self.settings.enabled = True
        self.settings.absolutePrefix = "/foo"

        portalURL = portal.absolute_url()
        prefix = "/".join(portalURL.split("/")[:-1])
        suffix = portalURL.split("/")[-1]

        vhostURL = (
            "{:s}/VirtualHostBase/http/example.org:80/{:s}/VirtualHostRoot"
            "/_vh_fizz/_vh_buzz/_vh_fizzbuzz/".format(prefix, suffix)
        )

        transaction.commit()

        browser = Browser(app)
        browser.open(vhostURL)

        self.assertFalse('<img src="relative.jpg" />' in browser.contents)
        self.assertTrue(
            '<img src="/fizz/buzz/fizzbuzz/foo/relative.jpg" />' in browser.contents
        )

    def test_theme_installed_invalid_config(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.rules = "invalid"

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertTrue("Accessibility" in browser.contents)

        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    def test_non_html_content(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + "/document_icon.png")
        # The theme
        self.assertFalse(b"This is the theme" in browser.contents)

    # XXX: This relies on a _v_ attribute; the test is too brittle
    #
    # def test_non_debug_mode_cache(self):
    #     app = self.layer['app']
    #     portal = self.layer['portal']
    #
    #     getConfiguration().debug_mode = False
    #     self.settings.enabled = True
    #
    #     # Sneakily seed the cache with dodgy data
    #
    #     otherrules = unicode(os.path.join(os.path.split(__file__)[0],
    #                          'otherrules.xml'))
    #
    #     compiled_theme = compile_theme(otherrules)
    #     transform = etree.XSLT(compiled_theme)
    #
    #     getCache(
    #         self.settings, portal.absolute_url()
    #     ).updateTransform(transform)
    #
    #     transaction.commit()
    #
    #     browser = Browser(app)
    #     browser.open(portal.absolute_url())
    #
    #     # Title - pulled in with rules.xml
    #     self.assertTrue(portal.title in browser.contents)
    #
    #     # Elsewhere - not pulled in
    #     self.assertFalse("Accessibility" in browser.contents)
    #
    #     # The theme
    #     self.assertTrue("This is the other theme" in browser.contents)
    #
    #     # Now invalidate the cache by touching the settings utility
    #
    #     self.settings.enabled = False
    #     self.settings.enabled = True
    #
    #     transaction.commit()
    #
    #     browser.open(portal.absolute_url())
    #
    #     # Title - pulled in with rules.xml
    #     self.assertTrue(portal.title in browser.contents)
    #
    #     # Elsewhere - not pulled in
    #     self.assertFalse("Accessibility" in browser.contents)
    #
    #     # The theme
    #     self.assertTrue("This is the theme" in browser.contents)

    # XXX need to be rewritten with latest plone 5 resource registries in mind
    # def test_resource_condition(self):
    #     app = self.layer['app']
    #     portal = self.layer['portal']

    #     portal_css = getToolByName(portal, 'portal_css')
    #     portal_css.setDebugMode(True)

    #     # shown in both
    #     thirdLastResource = portal_css.resources[-3]
    #     thirdLastResource.setExpression('')
    #     thirdLastResource.setRendering('link')
    #     thirdLastResource.setEnabled(True)
    #     thirdLastResource.setConditionalcomment('')

    #     # only show in theme
    #     secondToLastResource = portal_css.resources[-2]
    #     secondToLastResource.setExpression(
    #         'request/HTTP_X_THEME_ENABLED | nothing')
    #     secondToLastResource.setRendering('link')
    #     secondToLastResource.setEnabled(True)
    #     secondToLastResource.setConditionalcomment('')

    #     # only show when theme is disabled
    #     lastResource = portal_css.resources[-1]
    #     lastResource.setExpression(
    #         'not:request/HTTP_X_THEME_ENABLED | nothing')
    #     lastResource.setRendering('link')
    #     lastResource.setEnabled(True)
    #     lastResource.setConditionalcomment('')

    #     portal_css.cookResources()

    #     # First try without the theme
    #     self.settings.enabled = False

    #     transaction.commit()

    #     browser = Browser(app)
    #     browser.open(portal.absolute_url())

    #     self.assertTrue(thirdLastResource.getId() in browser.contents)
    #     self.assertFalse(secondToLastResource.getId() in browser.contents)
    #     self.assertTrue(lastResource.getId() in browser.contents)

    #     self.assertTrue(portal.title in browser.contents)
    #     self.assertTrue("Accessibility" in browser.contents)
    #     self.assertFalse("This is the theme" in browser.contents)

    #     # Now enable the theme and try again
    #     self.settings.enabled = True

    #     transaction.commit()

    #     browser = Browser(app)
    #     browser.open(portal.absolute_url())

    #     self.assertTrue(thirdLastResource.getId() in browser.contents)
    #     self.assertTrue(secondToLastResource.getId() in browser.contents)
    #     self.assertFalse(lastResource.getId() in browser.contents)

    #     self.assertTrue(portal.title in browser.contents)
    #     self.assertFalse("Accessibility" in browser.contents)
    #     self.assertTrue("This is the theme" in browser.contents)

    def test_theme_different_path(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        setRoles(portal, TEST_USER_ID, ("Manager",))
        portal.invokeFactory("Folder", "news", title="News")
        wftool = getToolByName(portal, "portal_workflow")
        wftool.doActionFor(portal.news, action="publish")
        setRoles(portal, TEST_USER_ID, ("Member",))

        self.settings.enabled = True

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

        browser.open(portal["news"].absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue("News" in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the other theme" in browser.contents)

    def test_theme_params(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.rules = "python://plone.app.theming/tests/paramrules.xml"  # noqa
        self.settings.parameterExpressions = {
            "stringParam": "string:string param value",
            "boolParam": "python:False",
            "contextParam": "context/absolute_url | string:no context",
            "requestParam": "request/someParam | string:off",
        }

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

        # Value of string param
        self.assertTrue("string param value" in browser.contents)

        # Would be here if bool param was false
        self.assertFalse("<script>bool param on</script>" in browser.contents)

        # Not present in this request
        self.assertFalse("<script>request param on</script>" in browser.contents)

        # Context was available for parameter expressions
        self.assertTrue(
            '<script id="contextParam">http://nohost/plone</script>' in browser.contents
        )

        # ... but present with the request param on
        browser.open(portal.absolute_url() + "?someParam=on")
        self.assertTrue("<script>request param on</script>" in browser.contents)

    def test_theme_for_404(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True

        transaction.commit()

        browser = Browser(app)
        browser.addHeader("Accept", "text/html")
        error = None
        try:
            browser.open(f"{portal.absolute_url():s}/404_page")
        except HTTPError as e:
            error = e
        self.assertEqual(error.code, 404)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_theme_params_on_404(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.rules = "python://plone.app.theming/tests/paramrules.xml"  # noqa
        self.settings.parameterExpressions = {
            "stringParam": "string:string param value",
            "boolParam": "python:False",
            "contextParam": "context/absolute_url | string:no context",
            "requestParam": "request/someParam | string:off",
        }

        transaction.commit()

        browser = Browser(app)
        browser.addHeader("Accept", "text/html")
        error = None
        try:
            browser.open(f"{portal.absolute_url():s}/404_page")
        except HTTPError as e:
            error = e
        self.assertEqual(error.code, 404)

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

        # Value of string param
        self.assertTrue("string param value" in browser.contents)

        # Would be here if bool param was false
        self.assertFalse("<script>bool param on</script>" in browser.contents)

        # Not present in this request
        self.assertFalse("<script>request param on</script>" in browser.contents)

        # Context is the last found parent
        self.assertTrue(
            '<script id="contextParam">http://nohost/plone</script>' in browser.contents
        )

    def test_navroot_params_on_404_widget_in_path(self):
        app = self.layer["app"]
        portal = self.layer["portal"]
        setRoles(portal, TEST_USER_ID, ["Contributor"])
        portal.invokeFactory("Folder", "subfolder")

        self.settings.enabled = True
        self.settings.parameterExpressions = {
            "navigation_root_id": "python:portal_state.navigation_root().getId()"  # noqa
        }

        transaction.commit()

        browser = Browser(app)
        browser.addHeader("Accept", "text/html")
        error = None
        try:
            browser.open(
                "{:s}/widget/oauth_login/info.txt".format(
                    portal["subfolder"].absolute_url()
                )
            )
        except HTTPError as e:
            error = e
        self.assertEqual(error.code, 404)

        self.assertTrue("This is the theme" in browser.contents)

    # XXX need to be rewritten with latest resource registries in mind
    # def test_resource_condition_404(self):
    #     app = self.layer['app']
    #     portal = self.layer['portal']

    #     portal_css = getToolByName(portal, 'portal_css')
    #     portal_css.setDebugMode(True)

    #     # shown in both
    #     thirdLastResource = portal_css.resources[-3]
    #     thirdLastResource.setExpression('')
    #     thirdLastResource.setRendering('link')
    #     thirdLastResource.setEnabled(True)
    #     thirdLastResource.setConditionalcomment('')

    #     # only show in theme
    #     secondToLastResource = portal_css.resources[-2]
    #     secondToLastResource.setExpression(
    #         'request/HTTP_X_THEME_ENABLED | nothing')
    #     secondToLastResource.setRendering('link')
    #     secondToLastResource.setEnabled(True)
    #     secondToLastResource.setConditionalcomment('')

    #     # only show when theme is disabled
    #     lastResource = portal_css.resources[-1]
    #     lastResource.setExpression(
    #         'not:request/HTTP_X_THEME_ENABLED | nothing')
    #     lastResource.setRendering('link')
    #     lastResource.setEnabled(True)
    #     lastResource.setConditionalcomment('')

    #     portal_css.cookResources()

    #     self.settings.enabled = True

    #     transaction.commit()

    #     browser = Browser(app)

    #     try:
    #         browser.open('{0:s}/404_page'.format(portal.absolute_url()))
    #     except HTTPError as e:
    #         error = e
    #     self.assertEqual(error.code, 404)

    #     self.assertTrue(thirdLastResource.getId() in browser.contents)
    #     self.assertTrue(secondToLastResource.getId() in browser.contents)
    #     self.assertFalse(lastResource.getId() in browser.contents)

    #     self.assertTrue("This is the theme" in browser.contents)

    def test_includes(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        setRoles(portal, TEST_USER_ID, ("Manager",))

        # Create some test content in the portal root
        here = os.path.split(__file__)[0]
        with open(os.path.join(here, "one.html")) as one:
            portal.manage_addDTMLMethod("alpha", file=one)
        with open(os.path.join(here, "two.html")) as two:
            portal.manage_addDTMLMethod("beta", file=two)

        # Create some different content in a subfolder
        portal.invokeFactory("Folder", "subfolder")
        portal.portal_workflow.doActionFor(portal.subfolder, "publish")

        with open(os.path.join(here, "one.html")) as one:
            portal["subfolder"].manage_addDTMLMethod("beta", file=one)
        with open(os.path.join(here, "two.html")) as two:
            portal["subfolder"].manage_addDTMLMethod("alpha", file=two)

        # Set up transformation
        self.settings.rules = "python://plone.app.theming/tests/includes.xml"
        self.settings.enabled = True

        transaction.commit()

        browser = Browser(app)

        # At the root if the site, we should pick up 'one' for alpha (absolute
        # path, relative to site root) and 'two' for beta (relative path,
        # relative to current directory)

        browser.open(portal.absolute_url())
        self.assertTrue('<div id="alpha">Number one</div>' in browser.contents)
        self.assertTrue('<div id="beta">Number two</div>' in browser.contents)

        # In the subfolder, we've reversed alpha and beta. We should now get
        # 'one' twice, since we still get alpha from the site root.
        browser.open(portal["subfolder"].absolute_url())
        self.assertTrue('<div id="alpha">Number one</div>' in browser.contents)
        self.assertTrue('<div id="beta">Number one</div>' in browser.contents)

    def test_include_non_ascii(self):
        # A Diazo theme with non-ascii subrequest can show characters wrong with Python 3.
        # See https://github.com/plone/Products.CMFPlone/issues/3068
        # These are the same French characters:
        # 'Actualités'
        # b'Actualit\xc3\xa9s'
        # u'Actualit\xe9s'
        # 'Actualit&#195;&#169;s'

        app = self.layer["app"]
        portal = self.layer["portal"]

        setRoles(portal, TEST_USER_ID, ("Manager",))

        # Create some test content in the portal root
        here = os.path.split(__file__)[0]
        with open(os.path.join(here, "french.html"), "rb") as french:
            portal.manage_addDTMLMethod("french", file=french)

        # Set up transformation
        self.settings.rules = "python://plone.app.theming/tests/nonascii.xml"
        self.settings.enabled = True

        transaction.commit()

        browser = Browser(app)

        # At the root if the site, we should pick up 'one' for alpha (absolute
        # path, relative to site root) and 'two' for beta (relative path,
        # relative to current directory)

        browser.open(portal.absolute_url())
        # browser.contents is always string.  On Py 2 this means bytes, on Py 3 text.
        self.assertIn('<div id="content">Actualit\xe9s</div>', browser.contents)

    def test_css_js_includes(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.rules = "/++theme++plone.app.theming.tests/css-js.xml"
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # CSS - pulled in with rules
        self.assertTrue(
            """<style type="text/css">/* A CSS file */\n</style>""" in browser.contents
        )

        # JS pulled in with rules
        self.assertTrue(
            """<script type="text/javascript">/* A JS file */\n</script>"""
            in browser.contents
        )

    def test_non_ascii_includes(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        self.settings.rules = "/++theme++plone.app.theming.tests/nonascii.xml"
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # browser.contents is always string.  On Py 2 this means bytes, on Py 3 text.
        self.assertIn("<div>N\xfamero uno</div>", browser.contents)

    def test_theme_enabled_query_string_debug_switch(self):
        app = self.layer["app"]
        portal = self.layer["portal"]

        self.settings.enabled = True
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + "?diazo.debug=1")

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # The theme
        self.assertTrue('id="diazo-debug-iframe"' in browser.contents)
