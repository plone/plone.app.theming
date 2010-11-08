from plone.resource.traversal import ResourceTraverser

class ThemeTraverser(ResourceTraverser):
    """The theme traverser.
    
    Allows traveral to /++theme++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """
    
    name = u'theme'
