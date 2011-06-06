from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import applyProfile

from zope.configuration import xmlconfig
from plone.app.testing.layers import IntegrationTesting
from plone.app.testing.layers import FunctionalTesting

class Theming(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.theming.tests
        xmlconfig.file('configure.zcml', plone.app.theming.tests, context=configurationContext)

        # Run the startup hook
        from plone.app.theming.plugins.hooks import onStartup
        onStartup(None)

    def setUpPloneSite(self, portal):
        # install into the Plone site
        applyProfile(portal, 'plone.app.theming:default')

THEMING_FIXTURE = Theming()
THEMING_INTEGRATION_TESTING = IntegrationTesting(bases=(THEMING_FIXTURE,), name="Theming:Integration")
THEMING_FUNCTIONAL_TESTING = FunctionalTesting(bases=(THEMING_FIXTURE,), name="Theming:Functional")
