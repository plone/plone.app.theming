# -*- coding: utf-8 -*-
# make this a namespace packages (plone.app.theming.plugins is an
# extensible python namespace
__import__('pkg_resources').declare_namespace(__name__)

# Some systems have a broken/missing ``roman`` module; monkey patch one in
# XXX: DO we still need this?
try:
    import roman
except ImportError:
    from plone.app.theming import _roman
    import sys
    sys.modules['roman'] = _roman
