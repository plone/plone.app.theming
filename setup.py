from pathlib import Path
from setuptools import find_packages
from setuptools import setup


version = "5.0.14.dev0"

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
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="plone diazo xdv deliverance theme transform xslt",
    author="Martin Aspeli and Laurence Rowe",
    author_email="optilude@gmail.com",
    url="https://pypi.org/project/plone.app.theming",
    license="GPL",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["plone", "plone.app"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "diazo>=1.0.3",
        "docutils",
        "lxml>=2.2.4",
        "plone.app.registry>=1.0",
        "plone.base",
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
        "setuptools",
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
