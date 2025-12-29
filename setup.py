from pathlib import Path
from setuptools import setup


version = "7.0.0a3"

long_description = (
    f"{Path('README.rst').read_text()}\n"
    f"{(Path('src') / 'plone' / 'app' / 'theming' / 'browser' / 'resources' / 'userguide.rst').read_text()}\n"
    f"{Path('CHANGES.rst').read_text()}"
)

setup(
    name="plone.app.theming",
    version=version,
    description="Integrates the Diazo theming engine with Plone",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # Get more strings from
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 6.2",
        "Framework :: Plone :: Core",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="plone diazo xdv deliverance theme transform xslt",
    author="Martin Aspeli and Laurence Rowe",
    author_email="optilude@gmail.com",
    url="https://pypi.org/project/plone.app.theming",
    license="GPL",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "diazo>=1.0.3",
        "docutils",
        "lxml>=2.2.4",
        "plone.app.registry>=1.0",
        "plone.base>=4.0.0a1",
        "plone.i18n",
        "plone.memoize",
        "plone.registry",
        "plone.resource",
        "plone.resourceeditor>=2.0.0",
        "plone.staticresources",
        "plone.subrequest",
        "plone.transformchain",
        "python-dateutil",
        "Products.GenericSetup",
        "Products.statusmessages",
        "repoze.xmliter>=0.3",
        "Zope",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            "plone.app.contenttypes[test]",
            "plone.testing",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
