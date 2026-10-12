from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import PloneSandboxLayer
from plone.app.testing.layers import FunctionalTesting
from plone.app.testing.layers import IntegrationTesting
from zope.configuration import xmlconfig

try:
    from plone.restapi.testing import PLONE_RESTAPI_DX_FIXTURE
    from plone.testing import zope

    HAS_RESTAPI = True
except ImportError:
    HAS_RESTAPI = False


class Theming(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.theming.tests

        xmlconfig.file(
            "configure.zcml", plone.app.theming.tests, context=configurationContext
        )

        # Run the startup hook
        from plone.app.theming.plugins.hooks import onStartup

        onStartup(None)

    def setUpPloneSite(self, portal):
        # install into the Plone site
        applyProfile(portal, "plone.app.theming:default")


THEMING_FIXTURE = Theming()
THEMING_INTEGRATION_TESTING = IntegrationTesting(
    bases=(THEMING_FIXTURE,), name="Theming:Integration"
)
THEMING_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(THEMING_FIXTURE,), name="Theming:Functional"
)


if HAS_RESTAPI:

    class ThemingRestAPI(PloneSandboxLayer):
        defaultBases = (PLONE_RESTAPI_DX_FIXTURE,)

        def setUpZope(self, app, configurationContext):
            import plone.app.theming

            xmlconfig.file(
                "configure.zcml", plone.app.theming, context=configurationContext
            )

            from plone.app.theming.plugins.hooks import onStartup

            onStartup(None)

        def setUpPloneSite(self, portal):
            applyProfile(portal, "plone.app.theming:default")

    THEMING_RESTAPI_FIXTURE = ThemingRestAPI()
    THEMING_RESTAPI_FUNCTIONAL_TESTING = FunctionalTesting(
        bases=(THEMING_RESTAPI_FIXTURE, zope.WSGI_SERVER_FIXTURE),
        name="Theming:RESTAPIFunctional",
    )
