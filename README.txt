============
Introduction
============

This package offers a simple way to develop and deploy Plone themes using
the `Diazo`_ theming engine. If you are not familiar with Diazo,
check out the `Diazo documentation <http://diazo.org>`_.

.. contents:: Contents

Installation
============

``plone.app.theming`` depends on:

  * `Plone`_ 4.0 or later.
  * `plone.transformchain`_ to hook the transformation into the publisher
  * `plone.registry`_ and `plone.app.registry`_ to manage settings
  * `plone.autoform`_, `plone.z3cform`_ and `plone.app.z3cform`_ to render the 
    control panel
  * `five.globalrequest`_ and `zope.globalrequest`_ for internal request
    access
  * `Diazo`_, the theming engine
  * `lxml`_ to transform Plone's output into a themed page

These will all be pulled in automatically if you are using zc.buildout and
follow the installation instructions.

To install ``plone.app.theming`` into your Plone instance, locate the file
``buildout.cfg`` in the root of your Plone instance directory on the file
system, and open it in a text editor. Locate the section that looks like
this::

    # extends = http://dist.plone.org/release/3.3/versions.cfg
    extends = versions.cfg
    versions = versions

It may also have a URL in the "extends" section, similar to the commented-out
first line, depending on whether you pull the Plone configuration from the
network or locally.

To add ``plone.app.theming`` to our setup, we need some slightly different
versions of a couple of the packages, so we extend the base config with a
version list from the good-py service, so change this part of the
configuration so it looks like this::

    extends =
        versions.cfg
        http://good-py.appspot.com/release/diazo/1.0b1
    versions = versions

Note that the last part of the URL above is the Diazo version number. There
may be a newer version by the time you read this, so check out the `overview
page <http://good-py.appspot.com/release/plone.app.theming>`_ for the known
good set.

What happens here is that the dependency list for ``plone.app.theming``
specifies some new versions for you via the good-py URL. This way, you don't
have to worry about getting the right versions, Buildout will handle it for
you.

Next step is to add the actual ``plone.app.theming`` add-on to the "eggs"
section of ``buildout.cfg``. Look for the section that looks like this::

    eggs =
        Plone

This section might have additional lines if you have other add-ons already
installed. Just add the ``plone.app.theming`` on a separate line, like this::

    eggs =
        Plone
        plone.app.theming

(Note that there is no need to add a ZCML slug as ``plone.app.theming`` uses
``z3c.autoinclude`` to configure itself automatically.)

Once you have added these lines to your configuration file, it's time to run
buildout, so the system can add and set up ``plone.app.theming`` for you. Go
to the command line, and from the root of your Plone instance (same directory
as buildout.cfg is located in), run buildout like this::

    $ bin/buildout

You will see output similar to this::

    Getting distribution for 'plone.app.theming==1.0b1'.
    Got plone.app.theming 1.0b1.
    Getting distribution for 'plone.app.registry'.
    Got plone.app.registry 1.0b2.
    ...

If everything went according to plan, you now have ``plone.app.theming``
installed in your Zope instance.

Next, start up Zope, e.g with::

    $ bin/instance fg

Then go to the "Add-ons" control panel in Plone as an administrator, and
install the "Diazo theme support" product. You should then notice a new
"Diazo theme" control panel in Plone's site setup.

Usage
=====

In the "Diazo Theme" control panel, you can set the following options:

  Enabled yes/no
    Whether or not the transform is enabled.

  Rules
    URL referencing the Diazo rules file. This file in turn references your
    theme. The URL may be a filesystem or remove URL (in which case you want
    to enable "read network access" - see below). It can also be an absolute
    path, starting with a ``/``, in which case it will be resolved relative
    to the Plone site root, or a special ``python://`` URL - see below.
  
  Absolute prefix 
    If given, any relative URL in an ``<img />``, ``<link />``, ``<style />``
    or ``<script />`` in the theme HTML file will be prefixed by this URL
    snippet when the theme is compiled. This makes it easier to develop theme
    HTML/CSS on the file system using relative paths that still work on any
    URL on the server.
    
  Read network
    By default, Diazo will not attempt to resolve external URLs referenced in
    the control panel or in the rules file, as this can have a performance
    impact. If you need to access external URLs, enable the "read network"
    setting.

Development aids
----------------

Note that when Zope is in development mode (e.g. running in the foreground
in a console with ``bin/instance fg``), the theme will be re-compiled on each
request. In non-development mode, it is compiled once when first accessed, and
then only re-compiled the control panel values are changed.

Also, in development mode, it is possible to temporarily disable the theme
by appending a query string parameter ``diazo.off=1``. For example::
    
    http://localhost:8080/Plone/some-page?diazo.off=1

The parameter is ignored in non-development mode.

Finally, note that a site accessed via the host name ``127.0.0.1`` will never
be themed. By default, ``localhost`` *will* be themed, of course.

Resources in Python packages
----------------------------

When specifying rules or referenced resources (such as the theme), you can use
a special ``python://`` URI scheme to specify a path relative to the
installation of a Python package distribution, as installed using
Distribute/setuptools (e.g. a standard Plone package installed via buildout).

For example, if your package is called ``my.theme`` and it contains a
directory ``static``, you could reference the file ``rules.xml`` in that
file as::

    ``python://my.theme/static/rules.xml``

This will be resolved to an absolute ``file://`` URL by ``plone.app.theming``.

Static files and CSS
--------------------

Typically, the theme will reference static resources such as images or
stylesheets. It is usually a good idea to keep all of these in a single,
top-level directory to minimise the risk of clashes with Plone content paths.

If you are using Zope/Plone standalone, you will need to make your static
resources available through Zope, or serve them from a separate (sub-)domain.
Here, you have a few options:

 * Create the static resources as ``File`` content objects through Plone.
 * Create the resources inside the ``portal_skins/custom`` folder in the ZMI.
 * Install the resources through a filesystem product.

The latter is most the appropriate option if you are distributing your theme
as a Python package. In this case, you can register a resource directory in
ZCML like so::

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:browser="http://namespaces.zope.org/browser">
        
        ...
        
        <browser:resourceDirectory
            name="my.theme"
            directory="static"
            />
        
        ...

    </configure>

The ``static`` directory should be in the same directory as the
``configure.zcml`` file. You can now put your theme, rules and static
resources here.

If you make sure that your theme uses only relative URLs to reference any
stylesheets, JavaScript files, or images that it needs (including those
referenced from stylesheets), you should now be able to view your static
theme by going to a URL like::

    http://localhost:8080/Plone/++resource++my.theme/theme.html

You can now set the "Absolute prefix" configuration option to be
'/++resource++my.theme'. ``plone.app.theming`` will then turn relative URLs
into appropriate absolute URLs with this prefix.

If you have put Apache, nginx or IIS in front of Zope, you may want to serve
the static resources from the web server directly instead.

Using portal_css to manage your CSS
-----------------------------------

Plone's "resource registries", including the ``portal_css`` tool, can be used
to manage CSS stylesheets. This offers several advantages over simply linking
to your stylesheets in the template, such as:

* Detailed control over the ordering of stylesheets
* Merging of stylesheets to reduce the number of downloads required to render
  your page
* On-the-fly stylesheet compression (e.g. whitespace removal)
* The ability to include or exclude a stylesheet based on an expression

It is usually desirable (and sometimes completely necessary) to leave the
theme file untouched, but you can still use ``portal_css`` to manage your
stylesheets. The trick is to drop the theme's styles and then include all
styles from Plone. For example, you could add the following rules::

    <drop theme="/html/head/link" />
    <drop theme="/html/head/style" />
    
    <!-- Pull in Plone CSS -->
    <append theme="/html/head" content="/html/head/link | /html/head/style" />

The use of an "or" expression for the content in the ``<append />`` rule means
that the precise ordering is maintained.

For an example of how to register stylesheets upon product installation using
GenericSetup, see below. In short - use the ``cssregistry.xml`` import step
in your GenericSetup profile directory.

There is one important caveat, however. Your stylesheet may include relative
URL references of the following form:

    background-image: url(../images/bg.jpg);
    
If your stylesheet lives in a resource directory (e.g. it is registered in
``portal_css`` with the id ``++resource++my.package/css/styles.css``), this
will work fine so long as the registry (and Zope) is in debug mode. The
relative URL will be resolved by the browser to
``++resource++my.package/images/bg.jpg``.

However, you may find that the relative URL breaks when the registry is put
into production mode. This is because resource merging also changes the URL
of the stylesheet to be something like::

    /plone-site/portal_css/Suburst+Theme/merged-cachekey-1234.css

To correct for this, you must set the ``applyPrefix`` flag to ``true`` when
installing your CSS resource using ``cssregistry.xml``. There is a
corresponding flag in the ``portal_css`` user interface.

Controlling Plone's default CSS
-------------------------------

It is sometimes useful to show some of Plone's CSS in the styled site. You
can achieve this by using an Diazo ``<append />`` rule or similar to copy the
CSS from Plone's generated ``<head />`` into the theme. You can use the
portal_css tool to turn off the style sheets you do not want.

However, if you also want the site to be usable in non-themed mode (e.g. on a
separate URL), you may want to have a larger set of styles enabled when Diazo
is not used. To make this easier, you can use the following expressions as
conditions in the portal_css tool (and ``portal_javascripts``,
``portal_kss``), in portal_actions, in page templates, and other places that
use TAL expression syntax::

    request/HTTP_X_THEME_ENABLED | nothing

This expression will return True if Diazo is currently enabled, in which case
an HTTP header "X-Theme-Enabled" will be set.

If you later deploy the theme to a fronting web server such as nginx, you can
set the same request header there to get the same effect, even if
``plone.app.theming`` is uninstalled.

Use::

    not: request/HTTP_X_THEME_ENABLED | nothing
    
to 'hide' a style sheet from the themed site.

A worked example
=================

There are many ways to set up an Diazo theme. For example, you could upload
the theme and rules as content in Plone use absolute paths to configure them.
You could also serve them from a separate static web server, or even load
them from the filesystem.

To create a deployable theme, however, it is often best to create a simple
Python package. This also provides a natural home for theme-related 
customisations such as template overrides.

Although a detailed tutorial is beyond the scope of this help file, a brief,
worked example is shown below.

1. Create a package and install it in your buildout::

    $ cd src
    $ paster create -t plone my.theme

See `the buildout manual`_ for details

If you have a recent ``ZopeSkel`` installed, this should work. Pick ``easy``
mode. Answer "yes" when asked if you want to register a profile.

Then edit ``buildout.cfg`` to add your new package (``my.theme`` above) to the
``develop`` and ``eggs`` lists.

2. Edit ``setup.py`` inside the newly created package

The ``install_requires`` list should be::

    install_requires=[
          'setuptools',
          'plone.app.theming',
      ],

Re-run buildout::

    $ bin/buildout

3. Edit ``configure.zcml`` inside the newly created package.

Add a resource directory inside the ``<configure />`` tag. Note that you may
need to add the ``browser`` namespace, as shown.

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:browser="http://namespaces.zope.org/browser"
        xmlns:i18n="http://namespaces.zope.org/i18n"
        xmlns:genericsetup="http://namespaces.zope.org/genericsetup"
        i18n_domain="my.theme">

        <genericsetup:registerProfile
            name="default"
            title="My theme"
            directory="profiles/default"
            description="Installs the my.theme package"
            provides="Products.GenericSetup.interfaces.EXTENSION"
            />

        <browser:resourceDirectory
            name="my.theme"
            directory="static"
            />
  
    </configure>

Here, we have used the package name, ``my.theme``, for the resource directory
name. Adjust as appropriate.

4. Add a ``static`` directory next to ``configure.zcml``.

5. Put your theme and rules files into this directory.

For example, you may have a ``theme.html`` that references images in a
sub-directory ``images/`` and stylesheets in a sub-directory ``css/``. Place
this file and the two directories inside the newly created ``static``
directory.

Make sure the theme uses relative URLs (e.g. ``<img src="images/foo.jpg" />``)
to reference its resources. This means you can open theme up from the
filesystem and view it in its splendour.

Also place a ``rules.xml`` file there. See the `Diazo`_ documentation for
details about its syntax. You can start with some very simple rules if
you just want to test::

    <?xml version="1.0" encoding="UTF-8"?>
    <rules
        xmlns="http://namespaces.plone.org/diazo"
        xmlns:css="http://namespaces.plone.org/diazo+css">

        <!-- The default theme, used for standard Plone web pages -->
        <theme href="theme.html" css:if-content="#visual-portal-wrapper" />
    
        <!-- Rules applying to a standard Plone web page -->
        <rules css:if-content="#visual-portal-wrapper">
            
            <!-- Add meta tags -->
            <drop theme="/html/head/meta" />
            <append content="/html/head/meta" theme="/html/head" />
    
            <!-- Copy style, script and link tags in the order they appear in the content -->
            <append
                content="/html/head/style | /html/head/script | /html/head/link"
                theme="/html/head"
                />
    
            <drop theme="/html/head/style" />
            <drop theme="/html/head/script" />
            <drop theme="/html/head/link" />

            <!-- Copy over the id/class attributes on the body tag.
                 This is important for per-section styling -->
            <prepend content="/html/body/@class" theme="/html/body" />
            <prepend content="/html/body/@id"    theme="/html/body" />
            <prepend content="/html/body/@dir"   theme="/html/body" />

            <!-- Logo (link target) -->
            <prepend content='//*[@id="portal-logo"]/@href' css:theme="#logo" />
            
            <!-- Site actions -->
            <copy css:content="#portal-siteactions li" css:theme="#actions" />

            <!-- Global navigation -->
            <copy css:content='#portal-globalnav li' css:theme='#global-navigation' />

            <!-- Breadcrumbs -->
            <copy css:content='#portal-breadcrumbs > *' css:theme='#breadcrumbs' />

            <!-- Document Content -->
            <copy css:content="#content > *" css:theme="#document-content" />
            <before css:content="#edit-bar" css:theme="#document-content" />
            <before css:content=".portalMessage" css:theme="#document-content" />

            <!-- Columns -->
            <copy css:content="#portal-column-one > *" css:theme="#column-one" />
            <copy css:content="#portal-column-two > *" css:theme="#column-two" />
            
        </rules>

    </rules>

In this example, we have referenced the theme HTML file relative to the
directory where the ``rules.xml`` resides. We make this theme conditional
on the ``#visual-portal-wrapper`` element being present in the content (i.e.
the web page generated by Plone). This ensures we do not apply the theme to
things like pop-ups or special pages.

We apply the same condition to the rules. The first few rules are probably
useful in most Plone themes. The remainder of the rules are examples that
may or may not apply, pulling in the logo, breadcrumbs, site actions,
document content, and left/right hand side columns.

See below for some more useful rules.

6. Create the installation profile

The generated code above for the ``<genericsetup:registerProfile />`` tag
contains a reference to a directory ``profiles/default``. You may need to
create this next to ``configure.zcml`` if it doesn't exist already, i.e.
create a new directory ``profiles`` and inside it another directory
``default``.

In this directory, add a file called ``metadata.xml`` containing::

    <metadata>
        <version>1</version>
        <dependencies>
            <dependency>profile-plone.app.theming:default</dependency>
        </dependencies>
    </metadata>

This will install plone.app.theming into Plone when my.theme is installed via
the add-on control panel later.

Also create a file called ``registry.xml``, with the following contents::

    <registry>
    
        <!-- plone.app.theming settings -->

        <record interface="plone.app.theming.interfaces.IThemeSettings" field="rules">
            <value>python://my.theme/static/rules.xml</value>
        </record>
    
        <record interface="plone.app.theming.interfaces.IThemeSettings" field="absolutePrefix">
            <value>/++resource++my.theme</value>
        </record>

    </registry>

Replace ``my.theme`` with your own package name, and ``rules.xml`` and
``theme.html`` as appropriate.

This file configures the settings behind the Diazo control panel.

Hint: If you have played with the control panel and want to export your
settings, you can create a snapshot in the ``portal_setup`` tool in the ZMI.
Examine the ``registry.xml`` file this creates, and pick out the records that
relate to ``plone.app.theming``. You should strip out the ``<field />`` tags
in the export, so that you are left with ``<record />`` and ``<value />`` tags
as shown above.

Also, add a ``cssregistry.xml`` in the ``profiles/default`` directory to
configure the ``portal_css`` tool::

    <?xml version="1.0"?>
    <object name="portal_css">
 
     <!-- Set conditions on stylesheets we don't want to pull in -->
     <stylesheet
         expression="not:request/HTTP_X_THEME_ENABLED | nothing"
         id="public.css"
         />
     
     <!-- Add new stylesheets -->
     <!-- Note: applyPrefix is not available in Plone < 4.0b3 -->
 
     <stylesheet title="" authenticated="False" cacheable="True"
        compression="safe" conditionalcomment="" cookable="True" enabled="on"
        expression="request/HTTP_X_THEME_ENABLED | nothing"
        id="++resource++my.theme/css/styles.css" media="" rel="stylesheet"
        rendering="link"
        applyPrefix="True"
        />

    </object>

This shows how to set a condition on an existing stylesheet, as well as
registering a brand new one. We've set ``applyPrefix`` to True here, as
explained above.

7. Test

Start up Zope and go to your Plone site. Your new package should show as
installable in the add-on product control panel. When installed, it should
install ``plone.app.theming`` as a dependency and pre-configure it to use your
theme and rule set. By default, the theme is not enabled, so you will need to
go to the control panel to switch it on.

You can now compare your untouched theme, the unstyled Plone site, and the
themed site by using the following URLs:

* ``http://localhost:8080`` (or whatever you have configured as the styled
  domain) for a styled Plone. If you used the sample rule above, this will
  look almost exactly like your theme, but with the ``<title />`` tag
  (normally shown in the title bar of your web browser) taken from Plone.
* ``http://127.0.0.1:8080`` (presuming this is the port where Plone is
  running) for an unstyled Plone.
* ``http://localhost:8080/++resource++my.theme/theme.html`` for the pristine
  theme. This is served as a static resource, almost as if it is being
  opened on the filesystem.

Common rules
============

To copy the page title::

    <!-- Head: title -->
    <replace theme="/html/head/title" content="/html/head/title" />

To copy the ``<base />`` tag (necessary for Plone's links to work)::

    <!-- Base tag -->
    <replace theme="/html/head/base" content="/html/head/base" />

To drop all styles and JavaScript resources from the theme and copy them
from Plone's ``portal_css`` tool instead::

    <!-- Drop styles in the head - these are added back by including them from Plone -->
    <drop theme="/html/head/link" />
    <drop theme="/html/head/style" />
    
    <!-- Pull in Plone CSS -->
    <append theme="/html/head" content="/html/head/link | /html/head/style" />

To copy Plone's JavaScript resources::

    <!-- Pull in Plone CSS -->
    <append theme="/html/head" content="/html/head/script" />

To copy the class of the ``<body />`` tag (necessary for certain Plone
JavaScript functions and styles to work properly)::

    <!-- Body -->
    <prepend theme="/html/body" content="/html/body/attribute::class" />    

Other tips
==========

* Firebug is an excellent tool for inspecting the theme and content when
  building rules. It even has an XPath extractor.
* Read up on XPath. It's not as complex as it looks and very powerful.
* Run Zope in debug mode whilst developing so that you don't need to restart
  to see changes to theme, rules or, resources.

.. _Diazo: http://diazo.org
.. _Plone: http://plone.org
.. _plone.transformchain: http://pypi.python.org/pypi/plone.transformchain
.. _repoze.zope2: http://pypi.python.org/pypi/repoze.zope2
.. _plone.transformchain: http://pypi.python.org/pypi/plone.transformchain
.. _plone.registry: http://pypi.python.org/pypi/plone.registry
.. _plone.app.registry: http://pypi.python.org/pypi/plone.app.registry
.. _plone.autoform: http://pypi.python.org/pypi/plone.autoform
.. _plone.z3cform: http://pypi.python.org/pypi/plone.z3cform
.. _plone.app.z3cform: http://pypi.python.org/pypi/plone.app.z3cform
.. _lxml: http://pypi.python.org/pypi/lxml
.. _five.globalrequest: http://pypi.python.org/pypi/five.globalrequest
.. _zope.globalrequest: http://pypi.python.org/pypi/zope.globalrequest
.. _the buildout manual: http://plone.org/documentation/manual/developer-manual/managing-projects-with-buildout
