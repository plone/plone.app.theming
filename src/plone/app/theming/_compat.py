# coding=utf-8
import sys


PY3 = sys.version_info[0] == 3
if PY3:
    from configparser import SafeConfigParser
    from io import StringIO
    from urllib.parse import parse_qs
    from urllib.parse import urljoin
    from urllib.parse import urlsplit
    from urllib.parse import urlparse
else:
    from ConfigParser import SafeConfigParser  # noqa
    from StringIO import StringIO  # noqa
    from urlparse import parse_qs  # noqa
    from urlparse import urljoin  # noqa
    from urlparse import urlparse  # noqa
    from urlparse import urlsplit  # noqa
