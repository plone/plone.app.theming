# -*- coding: utf-8 -*-
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.theming.testing import THEMING_FUNCTIONAL_TESTING
from plone.testing.z2 import Browser

import unittest


class TestControlPanel(unittest.TestCase):

    layer = THEMING_FUNCTIONAL_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        import transaction
        transaction.commit()

        self.portal = portal
        self.browser = Browser(self.layer['app'])

        handleErrors = self.browser.handleErrors
        try:
            self.browser.handleErrors = False
            self.browser.open(portal.absolute_url() + '/login_form')
            self.browser.getControl(name='__ac_name').value = TEST_USER_NAME
            self.browser.getControl(
                name='__ac_password'
            ).value = TEST_USER_PASSWORD
            self.browser.getControl('Log in').click()
        finally:
            self.browser.handleErrors = handleErrors

    def goto_controlpanel(self):
        self.browser.open(
            self.portal.absolute_url() + '/@@theming-controlpanel'
        )

    def test_save_advanced(self):
        # Simply saving the advanced panel without changes could already give a WrongType error.
        # See for example https://github.com/plone/plone.app.theming/issues/179
        # but there are more.
        self.browser.handleErrors = False
        self.goto_controlpanel()
        button = self.browser.getControl(name="form.button.AdvancedSave")
        button.click()

    def test_create_theme(self):
        pass
    #     self.goto_controlpanel()
    #     self.browser.getControl(name='title').value = 'Foobar'
    #     self.browser.getControl(name='description').value = 'foobar desc'
    #     self.browser.getControl(name='baseOn').value = ['template']
    #     self.browser.getControl(
    #         name='enableImmediately:boolean:default').value = ''
    #     self.browser.getControl(name='form.button.CreateTheme').click()

    #     self.assertTrue('foobar' in [t.__name__ for t in getZODBThemes()])
    #     self.assertTrue(getTheme('foobar') is not None)


    def test_upload_theme_file_nodata(self):
        self.browser.addHeader('Accept', 'application/json')
        self.browser.post(
            self.portal.absolute_url() + '/portal_resources/themeFileUpload',
            '',
        )
        self.assertIn('Status: 200', str(self.browser.headers))
        self.assertIn(
            '{"failure": "error"}',
            str(self.browser.contents)
        )

    def test_upload_theme_file_withdata(self):
        self.browser.addHeader('Accept', 'application/json')
        self.browser.post(
            self.portal.absolute_url() + '/portal_resources/themeFileUpload',
            """
---blah---
Content-Disposition: form-data; name="file"; filename="Screen Shot 2018-02-16 at 3.08.15 pm.png"
Content-Type: image/png


---blah---
            """,
# Bug in testbrowser prevents this working
#            content_type='multipart/form-data; boundary=---blah---'

        )
        self.assertIn('Status: 200', str(self.browser.headers))
        self.assertIn(
            '{"failure": "error"}', # TODO: Should be {'success':'create'}
            str(self.browser.contents)
        )
