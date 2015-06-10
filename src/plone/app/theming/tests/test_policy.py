# -*- coding: utf-8 -*-
from plone.app.theming.testing import THEMING_FUNCTIONAL_TESTING
import unittest2 as unittest

from plone.app.theming.utils import theming_policy


class TestFunctional(unittest.TestCase):

    layer = THEMING_FUNCTIONAL_TESTING

    def tearDown(self):
        request = self.layer['request']
        policy = theming_policy(request)
        # static class attribute is cached across test runs
        policy.invalidateCache()

    def test_getSettings(self):
        request = self.layer['request']
        policy = theming_policy(request)
        settings = policy.getSettings()
        self.assertEqual(settings.currentTheme,
                         u'barceloneta')
        self.assertEqual(settings.rules,
                         u'/++theme++barceloneta/rules.xml')

    def test_getCurrentTheme(self):
        request = self.layer['request']
        policy = theming_policy(request)
        self.assertEqual(policy.getCurrentTheme(),
                         u'barceloneta')

    def test_isThemeEnabled(self):
        request = self.layer['request']
        policy = theming_policy(request)
        self.assertTrue(policy.isThemeEnabled())

    def test_isThemeEnabled_blacklist(self):
        request = self.layer['request']
        request.set('BASE1', 'http://nohost/path/to/site')
        policy = theming_policy(request)
        settings = policy.getSettings()
        # Should pay no attention to BASE1 and only use SERVER_URL
        settings.hostnameBlacklist.append('nohost')
        self.assertFalse(policy.isThemeEnabled())

    def test_getCache(self):
        request = self.layer['request']
        policy = theming_policy(request)
        cache = policy.getCache()
        self.assertEqual(cache.themeObj, None)

    def test_getCacheKey(self):
        request = self.layer['request']
        policy = theming_policy(request)
        self.assertEqual(policy.getCacheKey(),
                         u'http://nohost/plone::barceloneta')

    def test_getCacheStorage(self):
        request = self.layer['request']
        policy = theming_policy(request)
        self.assertEqual(policy.getCacheStorage(), {})
        cache = policy.getCache()
        storage = policy.getCacheStorage()
        self.assertEqual(
            storage.items(),
            [(u'http://nohost/plone::barceloneta', cache)])

    def test_caching(self):
        """roundtrip"""
        request = self.layer['request']
        policy = theming_policy(request)
        theme = policy.get_theme()
        cache = policy.getCache()
        storage = policy.getCacheStorage()
        self.assertEqual(
            storage.items(),
            [(u'http://nohost/plone::barceloneta', cache)])
        self.assertEqual(cache.themeObj, theme)
        policy.set_theme(u'barceloneta', 'faketheme')
        self.assertEqual(policy.get_theme(), 'faketheme')
        policy.invalidateCache()
        self.assertEqual(policy.getCacheStorage(), {})
        theme2 = policy.get_theme()
        # different objects but both are barceloneta
        self.assertEqual(theme.title, theme2.title)
