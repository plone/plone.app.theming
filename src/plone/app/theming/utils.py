import pkg_resources

from ConfigParser import SafeConfigParser

from lxml import etree

from zope.site.hooks import getSite
from zope.component import getUtility
from zope.globalrequest import getRequest

from plone.subrequest import subrequest

from plone.resource.interfaces import IResourceDirectory
from plone.resource.directory import FILTERS

from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.interfaces import MANIFEST_FILENAME
from plone.app.theming.interfaces import RULE_FILENAME

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

def getOrCreatePersistentResourceDirectory():
    """Obtain the 'theme' persistent resource directory, creating it if
    necessary.
    """
    
    persistentDirectory = getUtility(IResourceDirectory, name="persistent")
    if THEME_RESOURCE_NAME not in persistentDirectory:
        persistentDirectory.makeDirectory(THEME_RESOURCE_NAME)
    
    return persistentDirectory[THEME_RESOURCE_NAME]

def extractThemeInfo(zipfile):
    """Return a tuple (themeName, rulesFile, absolutePrefix), where themeName
    is the name of the theme and rulesFile is a relative path to the rules.xml
    file.
    
    Will throw a ValueError if the theme directory does not contain a single
    top level directory or the rules file cannot be found.
    """
    
    themeName = None
    rulesFile = None
    absolutePrefix = None
    
    haveManifestRules = False
    
    for name in zipfile.namelist():
        member = zipfile.getinfo(name)
        path = member.filename.lstrip('/')
        
        if any(any(filter.match(n) for filter in FILTERS) for n in path.split('/')):
            continue
        
        lastSegment = path.rstrip('/').split('/')[-1]
        if path.endswith('/'):
            if themeName is not None:
                raise ValueError("More than one top level directory")
            
            themeName = lastSegment
            absolutePrefix = "/++theme++%s" % themeName
        
        elif themeName is not None:
            
            if not haveManifestRules and path == "%s/%s" % (themeName, RULE_FILENAME,):
                rulesFile = RULE_FILENAME
            
            elif path == "%s/%s" % (themeName, MANIFEST_FILENAME,):
                manifest = zipfile.open(member)
                try:
                    parser = SafeConfigParser({
                            'rules': rulesFile,
                            'prefix': absolutePrefix,
                        })
                    parser.readfp(manifest)
                    
                    rulesFile = parser.get('theme', 'rules')
                    if rulesFile:
                        haveManifestRules = True
                    
                    absolutePrefix = parser.get('theme', 'prefix')
                finally:
                    manifest.close()
    
    if rulesFile is None:
        raise ValueError("Could not find theme name and rules file")
    
    return themeName, rulesFile, absolutePrefix
