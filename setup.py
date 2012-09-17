from setuptools import setup, find_packages
import os

version = '1.1b1'

setup(name='plone.app.theming',
      version=version,
      description="Integrates the Diazo theming engine with Plone",
      long_description=open("README.txt").read() + "\n\n" +
                       open(os.path.join("src", "plone", "app", "theming", "browser", "resources", "userguide.rst")).read() + "\n\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
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
          'setuptools',
          'diazo',
          'docutils',
          'roman',
          'lxml>=2.2.4',
          'plone.app.registry>=1.0a2',
          'plone.subrequest',
          'plone.transformchain',
          'plone.resource>=1.0b5',
          'plone.resourceeditor',
          'repoze.xmliter>=0.3',
          'five.globalrequest',
          'Products.CMFPlone',
          'zope.traversing',
          'plone.app.controlpanel',
      ],
      extras_require={
        'test': ['plone.app.testing'],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
