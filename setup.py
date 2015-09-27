# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup
import os

version = '1.2.14'

longdescription = open("README.rst").read()
longdescription += "\n\n"
longdescription += open(
    os.path.join(
        "src",
        "plone",
        "app",
        "theming",
        "browser",
        "resources",
        "userguide.rst"
    )
).read()
longdescription += open("CHANGES.rst").read()

setup(
    name='plone.app.theming',
    version=version,
    description="Integrates the Diazo theming engine with Plone",
    long_description=longdescription,
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 5.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='plone diazo xdv deliverance theme transform xslt',
    author='Martin Aspeli and Laurence Rowe',
    author_email='optilude@gmail.com',
    url='http://pypi.python.org/pypi/plone.app.theming',
    license='GPL',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Products.CMFPlone',
        'diazo>=1.0.3',
        'docutils',
        'five.globalrequest',
        'lxml>=2.2.4',
        'plone.app.registry>=1.0a2',
        'plone.resource>=1.0b5',
        'plone.resourceeditor>=2.0.0.dev',
        'plone.subrequest',
        'plone.transformchain',
        'repoze.xmliter>=0.3',
        'roman',
        'setuptools',
        'zope.traversing',
    ],
    extras_require={
        'test': ['plone.app.testing'],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
