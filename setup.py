# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os


version = '4.1.6'

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
longdescription += "\n\n"
longdescription += open("CHANGES.rst").read()

setup(
    name='plone.app.theming',
    version=version,
    description="Integrates the Diazo theming engine with Plone",
    long_description=longdescription,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: Core",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='plone diazo xdv deliverance theme transform xslt',
    author='Martin Aspeli and Laurence Rowe',
    author_email='optilude@gmail.com',
    url='https://pypi.org/project/plone.app.theming',
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
        'lxml>=2.2.4',
        'plone.app.registry>=1.0a2',
        'plone.resourceeditor>=2.0.0.dev',
        'plone.staticresources',
        'plone.subrequest',
        'plone.transformchain',
        'python-dateutil',
        'repoze.xmliter>=0.3',
        'roman',
        'setuptools',
        'six',
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
