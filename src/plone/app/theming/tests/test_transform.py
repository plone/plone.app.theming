# -*- coding: utf-8 -*-
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
from plone.app.theming.utils import InternalResolver
from plone.app.theming.utils import PythonResolver
from plone.app.theming.utils import resolvePythonURL
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import getExprContext
from Products.CMFCore.utils import getToolByName
from urllib2 import HTTPError
from zope.component import getUtility

import Globals
import os.path
import re
import unittest2 as unittest


class TestCase(unittest.TestCase):

    layer = THEMING_FUNCTIONAL_TESTING

    def setUp(self):
        # Enable debug mode always to ensure cache is disabled by default
        Globals.DevelopmentMode = True

        self.settings = getUtility(IRegistry).forInterface(IThemeSettings)

        self.settings.enabled = False
        self.settings.rules = u'python://plone.app.theming/tests/rules.xml'
        self.settings.parameterExpressions = {
            'stringParam': 'string:string param value',
            'boolParam': 'python:False',
            'contextParam': 'context/absolute_url | string:no context',
            'requestParam': 'request/useother | string:off',
        }

        import transaction
        transaction.commit()

    def tearDown(self):
        Globals.DevelopmentMode = False

    def evaluate(self, context, expression):
        ec = getExprContext(context, context)
        expr = Expression(expression)
        return expr(ec)

    def test_no_effect_if_not_enabled(self):
        app = self.layer['app']
        portal = self.layer['portal']

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertTrue("Accessibility" in browser.contents)

        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    def test_theme_enabled(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        import transaction
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
        ''' Check if the rules are developed
        '''
        # First we check the status of our environment variables
        var_name = 'DIAZO_ALWAYS_CACHE_RULES'
        env_had_var = var_name in environ
        # and clean it up
        env_var_backup = environ.pop(var_name, None)

        transform = ThemeTransform(None, {})
        # This evaluates to True because we set
        # Globals.DevelopmentMode to True in the test setup
        self.assertTrue(transform.develop_theme())

        # But we can anyway force the cache
        environ[var_name] = 'true'
        self.assertFalse(transform.develop_theme())

        # If we require to debug.diazo the variable will be ignored
        transform = ThemeTransform(None, {'diazo.debug': '1'})
        self.assertTrue(transform.develop_theme())

        # Then we reset our env variables before leaving
        if env_had_var:
            environ[var_name] = env_var_backup
        else:
            del environ[var_name]

    def test_theme_enabled_resource_directory(self):

        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        theme = getTheme('plone.app.theming.tests')
        applyTheme(theme)
        self.assertEqual(
            self.settings.rules,
            u'/++theme++plone.app.theming.tests/rules.xml'
        )
        self.assertEqual(
            self.settings.currentTheme,
            u"plone.app.theming.tests"
        )
        self.assertEqual(
            self.settings.doctype,
            u"<!DOCTYPE html>"
        )
        import transaction
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
        self.assertTrue(re.match("<!DOCTYPE html>\s+<html", browser.contents))

    def test_theme_enabled_query_string_off_switch(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + '?diazo.off=1')

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertTrue("Accessibility" in browser.contents)

        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    def test_theme_enabled_query_string_off_switch_production_mode(self):
        app = self.layer['app']
        portal = self.layer['portal']

        Globals.DevelopmentMode = False

        self.settings.enabled = True
        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + '?diazo.off=1')

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_theme_enabled_header_off(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + '/@@header-disabled')

        self.assertTrue("Theme disabled" in browser.contents)

        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    def test_internal_resolver(self):
        compiler_parser = etree.XMLParser()
        compiler_parser.resolvers.add(InternalResolver())
        # We can use a sub-package or a directory since tests is a python
        # package
        theme = resolvePythonURL(
            u'python://plone.app.theming.tests/theme.html'
        )
        rules = resolvePythonURL(u'python://plone.app.theming/tests/rules.xml')
        compile_theme(rules, theme, compiler_parser=compiler_parser)

    def test_python_resolver(self):
        compiler_parser = etree.XMLParser()
        compiler_parser.resolvers.add(PythonResolver())
        theme = resolvePythonURL(
            u'python://plone.app.theming.tests/theme.html'
        )
        rules = resolvePythonURL(u'python://plone.app.theming/tests/rules.xml')
        compile_theme(rules, theme, compiler_parser=compiler_parser)

    def test_theme_stored_in_plone_site(self):
        app = self.layer['app']
        portal = self.layer['portal']

        # We'll upload the theme files to the Plone site root
        rules_contents = open(
            os.path.join(os.path.split(__file__)[0], 'localrules.xml')
        )
        theme_contents = open(
            os.path.join(os.path.split(__file__)[0], 'theme.html')
        )
        portal.manage_addDTMLMethod('theme.html', file=theme_contents)
        portal.manage_addDTMLMethod('rules.xml', file=rules_contents)

        # These paths should be relative to the Plone site root
        self.settings.rules = u'/rules.xml'
        self.settings.enabled = True

        import transaction
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
        app = self.layer['app']
        portal = self.layer['portal']

        # We'll upload the theme files to the Plone site root
        rules_contents = open(
            os.path.join(os.path.dirname(__file__), 'localrules.xml')
        )
        theme_contents = open(
            os.path.join(os.path.dirname(__file__), 'theme.html')
        )
        portal.manage_addDTMLMethod('theme.html', file=theme_contents)
        portal.manage_addDTMLMethod('rules.xml', file=rules_contents)

        # These paths should be relative to the Plone site root
        self.settings.rules = u'/rules.xml'
        self.settings.enabled = True

        from Products.SiteAccess import VirtualHostMonster
        VirtualHostMonster.manage_addVirtualHostMonster(app, 'virtual_hosting')

        import transaction
        transaction.commit()

        portalURL = portal.absolute_url()
        prefix = '/'.join(portalURL.split('/')[:-1])
        suffix = portalURL.split('/')[-1]

        vhostURL = (
            "{0:s}/VirtualHostBase/http/example.org:80/{1:s}/VirtualHostRoot"
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
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.absolutePrefix = None

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        self.assertTrue('<img src="relative.jpg" />' in browser.contents)

    def test_absolutePrefix_enabled_uri(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.absolutePrefix = u'http://example.com'

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        self.assertFalse('<img src="relative.jpg" />' in browser.contents)
        self.assertTrue(
            '<img src="http://example.com/relative.jpg" />' in browser.contents
        )

    def test_absolutePrefix_enabled_path(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.absolutePrefix = u'/foo'

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        self.assertFalse('<img src="relative.jpg" />' in browser.contents)
        self.assertTrue(
            '<img src="/plone/foo/relative.jpg" />' in browser.contents
        )

    def test_absolutePrefix_enabled_path_vhosting(self):
        app = self.layer['app']
        portal = self.layer['portal']

        from Products.SiteAccess import VirtualHostMonster
        VirtualHostMonster.manage_addVirtualHostMonster(app, 'virtual_hosting')

        import transaction
        transaction.commit()

        self.settings.enabled = True
        self.settings.absolutePrefix = u'/foo'

        portalURL = portal.absolute_url()
        prefix = '/'.join(portalURL.split('/')[:-1])
        suffix = portalURL.split('/')[-1]

        vhostURL = (
            "{0:s}/VirtualHostBase/http/example.org:80/{1:s}/VirtualHostRoot"
            "/_vh_fizz/_vh_buzz/_vh_fizzbuzz/".format(prefix, suffix)
        )

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(vhostURL)

        self.assertFalse('<img src="relative.jpg" />' in browser.contents)
        self.assertTrue(
            '<img src="/fizz/buzz/fizzbuzz/foo/relative.jpg" />'
            in browser.contents
        )

    def test_theme_installed_invalid_config(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.rules = u"invalid"

        import transaction
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
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + '/document_icon.png')
        # The theme
        self.assertFalse("This is the theme" in browser.contents)

    # XXX: This relies on a _v_ attribute; the test is too brittle
    #
    # def test_non_debug_mode_cache(self):
    #     app = self.layer['app']
    #     portal = self.layer['portal']
    #
    #     Globals.DevelopmentMode = False
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
    #     import transaction; transaction.commit()
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
    #     # Now invalide the cache by touching the settings utility
    #
    #     self.settings.enabled = False
    #     self.settings.enabled = True
    #
    #     import transaction; transaction.commit()
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

    #     import transaction; transaction.commit()

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

    #     import transaction; transaction.commit()

    #     browser = Browser(app)
    #     browser.open(portal.absolute_url())

    #     self.assertTrue(thirdLastResource.getId() in browser.contents)
    #     self.assertTrue(secondToLastResource.getId() in browser.contents)
    #     self.assertFalse(lastResource.getId() in browser.contents)

    #     self.assertTrue(portal.title in browser.contents)
    #     self.assertFalse("Accessibility" in browser.contents)
    #     self.assertTrue("This is the theme" in browser.contents)

    def test_theme_different_path(self):
        app = self.layer['app']
        portal = self.layer['portal']

        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'news', title=u"News")
        wftool = getToolByName(portal, "portal_workflow")
        wftool.doActionFor(portal.news, action='publish')
        setRoles(portal, TEST_USER_ID, ('Member',))

        self.settings.enabled = True

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

        browser.open(portal['news'].absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue("News" in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the other theme" in browser.contents)

    def test_theme_params(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.rules = u'python://plone.app.theming/tests/paramrules.xml'  # noqa
        self.settings.parameterExpressions = {
            'stringParam': 'string:string param value',
            'boolParam': 'python:False',
            'contextParam': 'context/absolute_url | string:no context',
            'requestParam': 'request/someParam | string:off',
        }

        import transaction
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
        self.assertTrue('string param value' in browser.contents)

        # Would be here if bool param was false
        self.assertFalse('<script>bool param on</script>' in browser.contents)

        # Not present in this request
        self.assertFalse(
            '<script>request param on</script>' in browser.contents
        )

        # Context was available for parameter expressions
        self.assertTrue(
            '<script id="contextParam">http://nohost/plone</script>'
            in browser.contents
        )

        # ... but present with the request param on
        browser.open(portal.absolute_url() + '?someParam=on')
        self.assertTrue(
            '<script>request param on</script>' in browser.contents
        )

    def test_theme_for_404(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.addHeader('Accept', 'text/html')
        error = None
        try:
            browser.open('{0:s}/404_page'.format(portal.absolute_url()))
        except HTTPError, e:
            error = e
        self.assertEqual(error.code, 404)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_theme_params_on_404(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.rules = u'python://plone.app.theming/tests/paramrules.xml'  # noqa
        self.settings.parameterExpressions = {
            'stringParam': 'string:string param value',
            'boolParam': 'python:False',
            'contextParam': 'context/absolute_url | string:no context',
            'requestParam': 'request/someParam | string:off',
        }

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.addHeader('Accept', 'text/html')
        error = None
        try:
            browser.open('{0:s}/404_page'.format(portal.absolute_url()))
        except HTTPError, e:
            error = e
        self.assertEqual(error.code, 404)

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

        # Value of string param
        self.assertTrue('string param value' in browser.contents)

        # Would be here if bool param was false
        self.assertFalse('<script>bool param on</script>' in browser.contents)

        # Not present in this request
        self.assertFalse(
            '<script>request param on</script>' in browser.contents
        )

        # Context is the last found parent
        self.assertTrue(
            '<script id="contextParam">http://nohost/plone</script>'
            in browser.contents
        )

    def test_navroot_params_on_404_widget_in_path(self):
        app = self.layer['app']
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('Folder', 'subfolder')

        self.settings.enabled = True
        self.settings.parameterExpressions = {
            'navigation_root_id': 'python:portal_state.navigation_root().getId()'  # noqa
        }

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.addHeader('Accept', 'text/html')
        error = None
        try:
            browser.open(
                '{0:s}/widget/oauth_login/info.txt'.format(
                    portal['subfolder'].absolute_url()
                )
            )
        except HTTPError, e:
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

    #     import transaction; transaction.commit()

    #     browser = Browser(app)

    #     try:
    #         browser.open('{0:s}/404_page'.format(portal.absolute_url()))
    #     except HTTPError, e:
    #         error = e
    #     self.assertEqual(error.code, 404)

    #     self.assertTrue(thirdLastResource.getId() in browser.contents)
    #     self.assertTrue(secondToLastResource.getId() in browser.contents)
    #     self.assertFalse(lastResource.getId() in browser.contents)

    #     self.assertTrue("This is the theme" in browser.contents)

    def test_includes(self):
        app = self.layer['app']
        portal = self.layer['portal']

        setRoles(portal, TEST_USER_ID, ('Manager',))

        one = open(os.path.join(os.path.split(__file__)[0], 'one.html'))
        two = open(os.path.join(os.path.split(__file__)[0], 'two.html'))

        # Create some test content in the portal root
        portal.manage_addDTMLMethod('alpha', file=one)
        portal.manage_addDTMLMethod('beta', file=two)

        one.seek(0)
        two.seek(0)

        # Create some different content in a subfolder
        portal.invokeFactory('Folder', 'subfolder')
        portal.portal_workflow.doActionFor(portal.subfolder, 'publish')

        portal['subfolder'].manage_addDTMLMethod('alpha', file=two)
        portal['subfolder'].manage_addDTMLMethod('beta', file=one)

        # Set up transformation
        self.settings.rules = u'python://plone.app.theming/tests/includes.xml'
        self.settings.enabled = True

        import transaction
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
        browser.open(portal['subfolder'].absolute_url())
        self.assertTrue('<div id="alpha">Number one</div>' in browser.contents)
        self.assertTrue('<div id="beta">Number one</div>' in browser.contents)

    def test_css_js_includes(self):

        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.rules = u'/++theme++plone.app.theming.tests/css-js.xml'
        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # CSS - pulled in with rules
        self.assertTrue(
            '''<style type="text/css">/* A CSS file */\n</style>'''
            in browser.contents)

        # JS pulled in with rules
        self.assertTrue(
            '''<script type="text/javascript">/* A JS file */\n</script>'''
            in browser.contents)

    def test_non_ascii_includes(self):

        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        self.settings.rules = u'/++theme++plone.app.theming.tests/nonascii.xml'
        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        self.assertTrue(
            '''<div>N\xc3\xbamero uno</div>'''
            in browser.contents)

    def test_theme_enabled_query_string_debug_switch(self):
        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + '?diazo.debug=1')

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # The theme
        self.assertTrue("id=\"diazo-debug-iframe\"" in browser.contents)
