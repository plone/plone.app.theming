# See http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError: # pragma: no cover
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)

# Some systems have a broken/missing ``roman`` module; monkey patch one in

try:
    import roman
except ImportError:
    from plone.app.theming import _roman
    import sys
    sys.modules['roman'] = _roman
