from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE

from plone.app.testing import applyProfile

from zope.configuration import xmlconfig
from plone.app.testing.layers import IntegrationTesting
from plone.app.testing.layers import FunctionalTesting

from plone.testing.z2 import ZSERVER_FIXTURE


class Theming(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.theming.tests
        xmlconfig.file(
            'configure.zcml',
            plone.app.theming.tests,
            context=configurationContext
        )

        # Run the startup hook
        from plone.app.theming.plugins.hooks import onStartup
        onStartup(None)

    def setUpPloneSite(self, portal):
        # install into the Plone site
        applyProfile(portal, 'plone.app.theming:default')


class ThemingAcceptance(Theming):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Run the startup hook
        from plone.app.theming.plugins.hooks import onStartup
        onStartup(None)


class ThemingWithCaching(Theming):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.theming.tests
        import plone.app.caching
        xmlconfig.file(
            'configure.zcml', plone.app.caching, context=configurationContext)
        xmlconfig.file(
            'configure.zcml', plone.app.theming.tests, context=configurationContext)

        # Run the startup hook
        from plone.app.theming.plugins.hooks import onStartup
        onStartup(None)

    def setUpPloneSite(self, portal):
        # install into the Plone site
        applyProfile(portal, 'plone.app.caching:default')
        applyProfile(portal, 'plone.app.theming:default')
        portal['portal_workflow'].setDefaultChain(
            'simple_publication_workflow')

THEMING_FIXTURE = Theming()
THEMING_INTEGRATION_TESTING = IntegrationTesting(
    bases=(THEMING_FIXTURE,),
    name="Theming:Integration"
)
THEMING_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(THEMING_FIXTURE,),
    name="Theming:Functional"
)
THEMING_ACCEPTANCE_FIXTURE = ThemingAcceptance()
THEMING_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(THEMING_ACCEPTANCE_FIXTURE, ZSERVER_FIXTURE),
    name="Theming:Acceptance"
)
THEMINGWITHCACHING_FIXTURE = ThemingWithCaching()
THEMINGWITHCACHING_TESTING = IntegrationTesting(
    bases=(THEMINGWITHCACHING_FIXTURE,),
    name="Theming:IntegrationWithCaching"
)
