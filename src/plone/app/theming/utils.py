import pkg_resources

from lxml import etree

from zope.site.hooks import getSite
from zope.globalrequest import getRequest

from plone.subrequest import subrequest

from Products.CMFCore.utils import getToolByName

class NetworkResolver(etree.Resolver):
    """Resolver for network urls
    """
    def resolve(self, system_url, public_id, context):
        if '://' in system_url and system_url != 'file:///__diazo__':
            return self.resolve_filename(system_url, context)

class PythonResolver(etree.Resolver):
    """Resolver for python:// paths
    """
    
    def resolve(self, system_url, public_id, context):
        if not system_url.lower().startswith('python://'):
            return None
        filename = resolvePythonURL(system_url)
        return self.resolve_filename(filename, context)


def resolvePythonURL(url):
    """Resolve the python resource url to it's path
    
    This can resolve python://dotted.package.name/file/path URLs to paths.
    """
    assert url.lower().startswith('python://')
    spec = url[9:]
    package, resource_name = spec.split('/', 1)
    return pkg_resources.resource_filename(package, resource_name)


class InternalResolver(etree.Resolver):
    """Resolver for internal absolute and relative paths (excluding protocol).
    If the path starts with a /, it will be resolved relative to the Plone
    site navigation root.
    """
    
    def resolve(self, system_url, public_id, context):
        request = getRequest()
        if request is None:
            return None
        
        # Ignore URLs with a scheme
        if '://' in system_url:
            return None
        
        # Ignore the special 'diazo:' resolvers
        if system_url.startswith('diazo:'):
            return None
        
        portal = getPortal()
        if portal is None:
            return None

        response = subrequest(system_url, root=portal)
        if response.status != 200:
            return None
        result = response.body or response.stdout.getvalue()
        return self.resolve_string(result, context)


def getPortal():
    """Return the portal object
    """
    # is site ever not the portal?
    site = getSite()
    if site is None:
        return None
    portal_url = getToolByName(site, 'portal_url', None)
    if portal_url is None:
        return None
    return portal_url.getPortalObject()

def expandAbsolutePrefix(prefix):
    """Prepend the Plone site URL to the prefix if it starts with /
    """
    if not prefix or not prefix.startswith('/'):
        return prefix
    portal = getPortal()
    if portal is None:
        return ''
    path = portal.absolute_url_path()
    if path and path.endswith('/'):
        path = path[:-1]
    return path + prefix
