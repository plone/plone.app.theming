from Products.CMFCore.utils import getToolByName

PROFILE_ID = "profile-plone.app.theming:default"

def update_registry(context, logger=None):
    """Method to convert float Price fields to string.
    """
    # Run the registry.xml step as that may have defined new attributes
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'plone.app.registry')
