import unittest2 as unittest
from plone.testing.z2 import Browser
from plone.app.testing import applyProfile
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, TEST_USER_PASSWORD

import Globals
import cStringIO
import gzip

from zope.component import provideUtility, provideAdapter, getUtility
from plone.registry.interfaces import IRegistry
from plone.registry import Registry

from plone.app.caching.interfaces import IPloneCacheSettings
from plone.caching.interfaces import ICacheSettings
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.testing import THEMINGWITHCACHING_TESTING


class TestIntegration(unittest.TestCase):

    layer = THEMINGWITHCACHING_TESTING

    def setUp(self):
        self.settings = getUtility(IRegistry).forInterface(IThemeSettings)

        self.settings.enabled = False
        self.settings.rules = u'python://plone.app.theming/tests/rules.xml'
        self.settings.parameterExpressions = {
                'stringParam': 'string:string param value',
                'boolParam': 'python:False',
                'contextParam' : 'context/absolute_url | string:no context',
                'requestParam': 'request/useother | string:off',
            }
        
        portal = self.layer['portal']
        applyProfile(portal, 'plone.app.caching:without-caching-proxy')

        self.cacheSettings = getUtility(IRegistry).forInterface(ICacheSettings)
        self.cacheSettings.enabled = True

        import transaction;
        transaction.commit()

    def test_cache_without_GZIP(self):
        ploneSettings = getUtility(IRegistry).forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = False

        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        import transaction; transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_cache_with_GZIP_anonymous(self):
    	ploneSettings = getUtility(IRegistry).forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = True

        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        import transaction; transaction.commit()

        browser = Browser(app)
        browser.addHeader('Accept-Encoding', 'gzip')
        browser.open(portal.absolute_url())
        content_handler = cStringIO.StringIO(browser.contents)
        uncompressed = gzip.GzipFile(fileobj=content_handler).read()

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in uncompressed)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in uncompressed)

        # The theme
        self.assertTrue("This is the theme" in uncompressed)

        # headers
        self.assertTrue('Accept-Encoding' in browser.headers['Vary'])
        self.assertEqual('gzip', browser.headers['Content-Encoding'])

    def test_cache_with_GZIP_authenticated(self):
        ploneSettings = getUtility(IRegistry).forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = True

        app = self.layer['app']
        portal = self.layer['portal']

        self.settings.enabled = True
        import transaction; transaction.commit()

        browser = Browser(app)
        browser.addHeader('Accept-Encoding', 'gzip')
        browser.addHeader('Authorization', 'Basic %s:%s' %
                (TEST_USER_NAME, TEST_USER_PASSWORD,))
        browser.open(portal.absolute_url())
        content_handler = cStringIO.StringIO(browser.contents)
        uncompressed = gzip.GzipFile(fileobj=content_handler).read()

        # Title - pulled in with rules.xml
        self.assertTrue(portal.title in uncompressed)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in uncompressed)

        # The theme
        self.assertTrue("This is the theme" in uncompressed)

        # headers
        self.assertTrue('Accept-Encoding' in browser.headers['Vary'])
        self.assertEqual('gzip', browser.headers['Content-Encoding'])