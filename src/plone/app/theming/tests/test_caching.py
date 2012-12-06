import unittest2 as unittest
from plone.testing.z2 import Browser
from plone.app.testing import applyProfile, setRoles
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, TEST_USER_PASSWORD

import cStringIO
import gzip

from zope.component import getUtility
from zope.globalrequest import setRequest
from plone.registry.interfaces import IRegistry

from plone.app.caching.interfaces import IPloneCacheSettings
from plone.caching.interfaces import ICacheSettings
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.testing import THEMINGWITHCACHING_TESTING


class TestIntegration(unittest.TestCase):

    layer = THEMINGWITHCACHING_TESTING

    def setUp(self):
        self.settings = getUtility(IRegistry).forInterface(IThemeSettings)

        self.settings.enabled = True
        self.settings.rules = u'python://plone.app.theming/tests/rules.xml'
        self.settings.parameterExpressions = {
            'stringParam': 'string:string param value',
            'boolParam': 'python:False',
            'contextParam': 'context/absolute_url | string:no context',
            'requestParam': 'request/useother | string:off',
        }

        self.portal = self.layer['portal']
        setRequest(self.portal.REQUEST)

        applyProfile(self.portal, 'plone.app.caching:without-caching-proxy')

        self.cacheSettings = getUtility(IRegistry).forInterface(ICacheSettings)
        self.cacheSettings.enabled = True
        self.cacheSettings.operationMapping = {
            'plone.content.folderView': 'plone.app.caching.weakCaching'}
        registry = getUtility(IRegistry)
        registry['plone.app.caching.weakCaching.ramCache'] = True

        import transaction
        transaction.commit()

    def tearDown(self):
        setRequest(None)

    def test_cache_without_GZIP(self):
        ploneSettings = getUtility(IRegistry).forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = False

        app = self.layer['app']
        portal = self.layer['portal']

        # Folder content
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1')
        portal['f1'].setTitle(u"Folder one")
        portal['f1'].setDescription(u"Folder one description")
        portal['f1'].reindexObject()

        # Publish the folder
        portal.portal_workflow.doActionFor(portal['f1'], 'publish')

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.open(portal['f1'].absolute_url())

        # Title - pulled in with rules.xml
        self.assertTrue(portal['f1'].Title() in browser.contents)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in browser.contents)

        # The theme
        self.assertTrue("This is the theme" in browser.contents)

    def test_cache_with_GZIP_anonymous(self):
        ploneSettings = getUtility(IRegistry).forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = True

        app = self.layer['app']
        portal = self.layer['portal']

        # Folder content
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f2')
        portal['f2'].setTitle(u"Folder two")
        portal['f2'].setDescription(u"Folder two description")
        portal['f2'].reindexObject()

        # Publish the folder
        portal.portal_workflow.doActionFor(portal['f2'], 'publish')

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.addHeader('Accept-Encoding', 'gzip')
        browser.open(portal['f2'].absolute_url())
        content_handler = cStringIO.StringIO(browser.contents)
        uncompressed = gzip.GzipFile(fileobj=content_handler).read()

        # Title - pulled in with rules.xml
        self.assertTrue(portal['f2'].Title() in uncompressed)

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

        # Folder content
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f3')
        portal['f3'].setTitle(u"Folder three")
        portal['f3'].setDescription(u"Folder three description")
        portal['f3'].reindexObject()

        # Publish the folder
        portal.portal_workflow.doActionFor(portal['f3'], 'publish')

        import transaction
        transaction.commit()

        browser = Browser(app)
        browser.addHeader('Accept-Encoding', 'gzip')
        browser.addHeader('Authorization', 'Basic %s:%s' % (
            TEST_USER_NAME, TEST_USER_PASSWORD))
        browser.open(portal['f3'].absolute_url())
        content_handler = cStringIO.StringIO(browser.contents)
        uncompressed = gzip.GzipFile(fileobj=content_handler).read()

        # Title - pulled in with rules.xml
        self.assertTrue(portal['f3'].Title() in uncompressed)

        # Elsewhere - not pulled in
        self.assertFalse("Accessibility" in uncompressed)

        # The theme
        self.assertTrue("This is the theme" in uncompressed)

        # headers
        self.assertTrue('Accept-Encoding' in browser.headers['Vary'])
        self.assertEqual('gzip', browser.headers['Content-Encoding'])
