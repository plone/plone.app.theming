============
Introduction
============

This package offers a simple way to develop and deploy Plone themes using
the `Diazo`_ theming engine. If you are not familiar with Diazo,
check out the `Diazo documentation <http://diazo.org>`_.

.. contents:: Contents

Installation
============

``plone.app.theming`` works with Plone 4.1 or later.

To install ``plone.app.theming`` into your Plone instance, locate the file
``buildout.cfg`` in the root of your Plone instance directory on the file
system, and open it in a text editor. Locate the section that looks like
this::

    # extends = http://dist.plone.org/release/4.1/versions.cfg
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
        http://good-py.appspot.com/release/plone.app.theming/1.0b1
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

In the "Diazo Theme" control panel, you can turn the theming engine on or
off, and select from a list of pre-registered themes (more on how to
register your own themes shortly).

You can also upload a theme packaged as a ZIP archive from the control panel,
under the "Import" tab. See below for more information about how to create
a valid theme archive.

Alternatively, you can configure a theme manually, under the "Advanced" tab.
The options here are:

Rules
    URL referencing the Diazo rules file. This file in turn references your
    theme. The URL may be a filesystem or remote URL (in which case you want
    to enable "read network access" - see below). It can also be an absolute
    path, starting with a ``/``, in which case it will be resolved relative
    to the Plone site root, or a special ``python://`` URL - see below.
    
    The most common type of URL will be a relative path using the
    ``++theme++`` traversal namespace. See below.
  
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

Unthemed host names
    You can list hostnames here that will never be themed. By default, this
    list contains ``127.0.0.1``, which means that if you access your Plone
    site using that IP address (as opposed to ``localhost`` or some other
    domain name), you will see an unthemed site. This is useful for theme
    development, or scenarios where you want your content authors to be able
    to access a "plain" Plone site.

Parameter expressions
    Some themes will use parameters in their rules files. Available parameters
    can be set up here, using TALES expressions. Each parameter should be
    entered on its own line, in the form ``<parameter name> = <expression>``.
    More on expressions below.

Packaging themes
----------------

There are several ways to package and distribute themes:

ZIP file format
~~~~~~~~~~~~~~~

A theme packaged for import as a ZIP archive must adhere to the following
rules:

  * The ZIP file must contain a single top level directory. This will be
    used as the theme id. Only one theme with a given id may exist in any
    given Plone site, though you are given the option to replace an existing
    theme on import if you upload an archive with a theme that already exists.
  * Inside this top level directory, there should be a ``rules.xml`` file with
    the Diazo rules. Any other resources, such as the theme HTML file or
    static resources, will normally also live in this directory or any
    subdirectories you wish to create inside it.
  * Optionally, you can add a ``manifest.cfg`` with a theme title and
    description for the theme. If you want to use a different absolute path
    prefix or rules file, you can also specify this in ``manifest.cfg``. See
    the next section for an example.

The easiest way to create a compliant ZIP file is usually to start with a
standalone theme built as a static web page in a top level directory,
referencing its resources (images, stylesheets, JavaScript files, etc) using
relative URLs. Then, place a ``rules.xml`` file in this same top level
directory, containing the relevant Diazo directives. Finally, create a ZIP
archive of the top level directory using the compression features built into
your operating system or a program such as 7Zip for Windows.

Themes in resources directories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package integrates with `plone.resource`_ to enable the ``theme``
resource type. This enables themes to be deployed:

  * On the filesystem using the global resource directory (if one is
    configured);
  * In the ZODB inside the ``theme`` directory of the
    ``portal_resources`` tool (perhaps initially imported via a ZIP archive
    as described above); or
  * In Python package that use the ``<plone:static />`` ZCML directive to
    register their own resource directory

Provided they contains a ``rules.xml`` file, themes in such directories will
appear in the control panel.

For example:

  * If you had configured a global resource directory inside your buildout
    root called ``resources``, you could add a directory
    ``resources/theme/mytheme``. If this contained a ``rules.xml`` file,
    it would show up in the theme control panel as a pre-registered,
    installable theme.
    you could configure the rules path in the Diazo control panel to be
    ``/++theme++mytheme/rules.xml``, and the absolute prefix to be
    ``/++theme++mytheme``.

  * If you had uploaded your theme to the ZMI inside
    ``portal_resources/theme/mytheme`` and placed a ``rules.xml`` file here,
    you could again configure the rules path in the Diazo control panel to be
    ``/++theme++mytheme/rules.xml``, and the absolute prefix to be
    ``/++theme++mytheme``.

  * If you had a filesystem package ``my.theme`` you could create a
    subdirectory of this package called ``static/`` containing the
    ``rules.xml`` file then add the following to the ``configure.zcml``
    file in the package root::
    
        <configure
            xmlns:plone="http://namespaces.plone.org/plone"
            xmlns="http://namespaces.zope.org/zope">
            
            ...
            
            <plone:static directory="static" type="theme" />
            
        </configure>
    
    With this, you could configure the Diazo control panel to use the rules
    path ``/++theme++my.theme/rules.xml`` and the absolute prefix
    ``/++theme++my.theme``. The theme name here is taken from the package
    name where ``configure.zcml`` is found. To specify an alternative name,
    use the ``name`` attribute to the ``<plone:static />`` directive.
    
    See the worked example below for a more detailed example.
    
When themes are deployed in this way, they become available in the control
panel, provided the resource directory contains a ``rules.xml`` file.

If there is a ``manifest.cfg`` file inside the top level resource directory,
this may contain a manifest giving information about the theme. This file
may look like this::

    [theme]
    title = My theme
    description = A test theme

As shown here, the manifest file can be used to provide a more user friendly
title and a longer description for the theme, for use in the control panel.
Only the ``[theme]`` header is required - all other keys are optional.

You can also set::

    rules = myrules.xml
    
to use a different rule file name than ``rules.xml``, and::

    prefix = /some/prefix

to change the absolute path prefix (see above).

Note that when you set ``rules`` and ``prefix``, these are absolute URLs or
file paths. To reference the theme directory you can use the following
format::

    rules = /++theme++my.theme/myrules.xml

The default is to use ``/++theme++<theme name>/rules.xml`` for the rules and
``/++theme++<theme name>`` as the absolute path prefix, which is probably
the right approach for most self-contained themes.

Resources in Python packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When specifying rules or referenced resources (such as the theme), you can use
a special ``python://`` URI scheme to specify a path relative to the
installation of a Python package distribution, as installed using
Distribute/setuptools (e.g. a standard Plone package installed via buildout).

For example, if your package is called ``my.theme`` and it contains a
directory ``static``, you could reference the file ``rules.xml`` in that
file as::

    ``python://my.theme/static/rules.xml``

This will be resolved to an absolute ``file://`` URL by ``plone.app.theming``.

**Note:** In most cases, it will be easier to use the ``<plone:static />``
directive as described above.

Theme parameters
----------------

It is possible to pass arbitrary parameters to your theme, which can be
referenced as variables in XPath expressions.

For example, you could have a parameter ``mode`` that could be set to the
string ``live`` or ``test``. In your rules, you could do something like this
to insert a warning when you are on the test server::

    <before css:theme-children="body" if="$mode = 'test'">
        <span class="warning">Warning: This is the test server</span>
    </before>

You could even use the parameter value directly, e.g.::

    <before css:theme-children="body">
        <span class="info">This is the <xsl:value-of select="$mode" /> server</span>
    </before>
    
See the `Diazo documentation`_ for more details about rules that support
``if`` parameters and inline HTML and XSL.

The following parameters are always available when using
``plone.app.theming``:

``scheme``
    The scheme portion of the inbound URL, usually ``http`` or ``https``.
``host``
    The hostname in the inbound URL.
``path``
    The path segment of the inbound URL. This will not include any virtual
    hosting tokens, i.e. it is the path the end user sees.
``base``
    The Zope base url (the ``BASE1`` request variable).

You can add additional parameters through the control panel, using TALES
expressions. Parameters are listed on the *Advanced* tab, one per line, in
the form ``<name> = <expression>``.

For example, if you want to avoid theming any pages that are loaded by Plone's
overlays, you can make use of the ``ajax_load`` request parameter that they
set. Your rules file might include::

    <notheme if="$ajax_load" />

To add this parameter as well as the ``mode`` parameter outlined earlier, you
could add the following in the control panel::

    ajax_load = python: 'ajax_load' in request.form
    mode = string: test

The right hand side is a TALES expression. It *must* evaluate to a string,
integer, float, boolean or ``None``: lists, dicts and objects are not
supported. ``python:``, ``string:`` and path expressions work as they do
in page templates.

The following variables are available:

  ``context``
    The context of the current request, usually a content object.
  ``request``
    The current request.
  ``portal``
    The portal root object.
  ``context_state``
    The ``@@plone_context_state`` view, from which you can look up additional
    values such as the context's URL or default view.
  ``portal_state``
    The ``@@plone_portal_state`` view, form which you can look up additional
    values such as the navigation root URL or whether or not the current
    user is logged in.

See ``plone.app.layout`` for details about the ``@@plone_context_state`` and
``@@plone_portal_state`` views.

Theme parameters are really integral to a theme, and will therefore be set
based on a theme's manifest when a theme is imported from a Zip file or
enabled from a resource directory. This is done using the
``[theme:parameters]`` section in the manifest file. For example::

    [theme]
    title = My theme
    description = A test theme

    [theme:parameters]
    ajax_load = python: 'ajax_load' in request.form
    mode = string: test

Temporarily disabling the theme
-------------------------------

Note that when Zope is in development mode (e.g. running in the foreground
in a console with ``bin/instance fg``), the theme will be re-compiled on each
request. In non-development mode, it is compiled once when first accessed, and
then only re-compiled the control panel values are changed.

Also, in development mode, it is possible to temporarily disable the theme
by appending a query string parameter ``diazo.off=1``. For example::
    
    http://localhost:8080/Plone/some-page?diazo.off=1

The parameter is ignored in non-development mode.

Disabling the theme for a particular view, script or template
-------------------------------------------------------------

To disable theming for a particular view, script or template set the
``X-Theme-Disabled`` header. ::

    request.response.setHeader('X-Theme-Disabled', 'True')

Or directly from a template::

    tal:define="dummy python:request.response.setHeader('X-Theme-Disabled', 'True')"

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
as a Python package. In this case, you can register a static resource
directory in ZCML as outlined above::

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:plone="http://namespaces.plone.org/plone">
        
        ...
        
        <plone:static
            directory="static"
            type="theme"
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

    http://localhost:8080/Plone/++theme++my.theme/theme.html

You can now set the "Absolute prefix" configuration option to be
'/++theme++my.theme'. ``plone.app.theming`` will then turn relative URLs
into appropriate absolute URLs with this prefix.

If you have put Apache, nginx or IIS in front of Zope, you may want to serve
the static resources from the web server directly instead.

Using portal_css to manage your CSS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    <after theme-children="/html/head" content="/html/head/link | /html/head/style" />

The use of an "or" expression for the content in the ``after />`` rule means
that the precise ordering is maintained.

For an example of how to register stylesheets upon product installation using
GenericSetup, see below. In short - use the ``cssregistry.xml`` import step
in your GenericSetup profile directory.

There is one important caveat, however. Your stylesheet may include relative
URL references of the following form:

    background-image: url(../images/bg.jpg);
    
If your stylesheet lives in a resource directory (e.g. it is registered in
``portal_css`` with the id ``++theme++my.theme/css/styles.css``), this
will work fine so long as the registry (and Zope) is in debug mode. The
relative URL will be resolved by the browser to
``++theme++my.theme/images/bg.jpg``.

However, you may find that the relative URL breaks when the registry is put
into production mode. This is because resource merging also changes the URL
of the stylesheet to be something like::

    /plone-site/portal_css/Suburst+Theme/merged-cachekey-1234.css

To correct for this, you must set the ``applyPrefix`` flag to ``true`` when
installing your CSS resource using ``cssregistry.xml``. There is a
corresponding flag in the ``portal_css`` user interface.

Controlling Plone's default CSS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is sometimes useful to show some of Plone's CSS in the styled site. You
can achieve this by using an Diazo ``after />`` rule or similar to copy the
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

GenericSetup syntax for enabling a theme
----------------------------------------

To enable the theme upon installation of a GenericSetup extension profile,
you can use the ``theme.xml`` import step.

Place a file like this in the profile directory – usually ``profiles/default``
inside a package that registers a GenericSetup extension profile::

    <theme>
        <name>my.theme</name>
        <enabled>true</enabled>
    </theme>

The ``<name />`` element is used to give the name of the theme to enable. The
``<enabled />`` element is used to enable or disable theming, and may contain
either ``true`` or ``false``. Both are optional.

Note that this is an import step only. The actual state is stored in the
``portal_registry`` tool provided by ``plone.app.registry``. Upon export (and
in a base profile), it can be found in the profile in ``registry.xml``.

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
        xmlns:plone="http://namespaces.plone.org/plone"
        i18n_domain="my.theme">

        <genericsetup:registerProfile
            name="default"
            title="My theme"
            directory="profiles/default"
            description="Installs the my.theme package"
            provides="Products.GenericSetup.interfaces.EXTENSION"
            />

        <plone:static
            type="theme"
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
        xmlns:css="http://namespaces.plone.org/diazo/css"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

        <!-- The default theme, used for standard Plone web pages -->
        <theme href="theme.html" css:if-content="#visual-portal-wrapper" />
    
        <!-- Rules applying to a standard Plone web page -->
        <rules css:if-content="#visual-portal-wrapper">
            
            <!-- Add meta tags -->
            <drop theme="/html/head/meta" />
            <after content="/html/head/meta" theme-children="/html/head" />
    
            <!-- Copy style, script and link tags in the order they appear in the content -->
            <after
                content="/html/head/style | /html/head/script | /html/head/link"
                theme-children="/html/head"
                />
    
            <drop theme="/html/head/style" />
            <drop theme="/html/head/script" />
            <drop theme="/html/head/link" />

            <!-- Copy over the id/class attributes on the body tag.
                 This is important for per-section styling -->
            <merge attributes="class" css:content="body" css:theme="body" />
            <copy attributes="id dir" css:content="body" css:theme="body" />

            <!-- Logo (link target) -->
            <copy attributes="href" css:content='#portal-logo' css:theme="#logo" />
            
            <!-- Site actions -->
            <replace css:content="#portal-siteactions li" css:theme-children="#actions" />

            <!-- Global navigation -->
            <replace css:content='#portal-globalnav li' css:theme-children='#global-navigation' />

            <!-- Breadcrumbs -->
            <replace css:content-children='#portal-breadcrumbs' css:theme-children='#breadcrumbs' />

            <!-- Document Content -->
            <replace css:content-children="#content" css:theme-children="#document-content" />
            <before css:content="#edit-bar" css:theme="#document-content" />
            <before css:content=".portalMessage" css:theme="#document-content" />

            <!-- Columns -->
            <replace css:content-children="#portal-column-one > *" css:theme-children="#column-one" />
            <replace css:content-children="#portal-column-two > *" css:theme-children="#column-two" />
            
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

Finally, put a ``manifest.cfg`` file alongside ``rules.xml`` in the
``static`` directory, containing::

    [theme]
    title = My theme
    description = A demo theme from the plone.app.theming README

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

Also create a file called ``theme.xml``, with the following contents::

    <theme>
        <name>my.theme</name>
        <enabled>true</enabled>
    </theme>

Replace ``my.theme`` with your own package name.

This file configures the settings behind the Diazo control panel.

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
        id="++theme++my.theme/css/styles.css" media="" rel="stylesheet"
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
* ``http://localhost:8080?diazo.off=1`` (presuming this is the port where
  Plone is running) for an unstyled Plone.
* ``http://localhost:8080/++theme++my.theme/theme.html`` for the pristine
  theme. This is served as a static resource, almost as if it is being
  opened on the filesystem.

Common rules
============

To copy the page title::

    <replace css:theme="title" css:content="title" />

To copy the ``<base />`` tag (necessary for Plone's links to work)::

    <replace css:theme="base" css:content="base" />

If there is no ``<base />`` tag in the theme, you can do:

    <before css:theme-children="head" css:content="base" />

To drop all styles and JavaScript resources from the theme and copy them
from Plone's ``portal_css`` tool instead::

    <!-- Drop styles in the head - these are added back by including them from Plone -->
    <drop theme="/html/head/link" />
    <drop theme="/html/head/style" />
    
    <!-- Pull in Plone CSS -->
    <after theme-children="/html/head" content="/html/head/link | /html/head/style" />

To copy Plone's JavaScript resources::

    <!-- Pull in Plone CSS -->
    <after theme-children="/html/head" content="/html/head/script" />

To copy the class of the ``<body />`` tag (necessary for certain Plone
JavaScript functions and styles to work properly)::

    <!-- Body -->
    <merge attributes="class" css:theme="body" css:content="body" />

Other tips
==========

* Firebug is an excellent tool for inspecting the theme and content when
  building rules. It even has an XPath extractor.
* Read up on XPath. It's not as complex as it looks and very powerful.
* Run Zope in debug mode whilst developing so that you don't need to restart
  to see changes to theme, rules or, resources.

Migrating from collective.xdv
=============================

``plone.app.theme`` has evolved from the ``collective.xdv`` package.
Similarly, Diazo is an evolution of ``xdv``.

Migrating XDV rules to Diazo rules
----------------------------------

The Diazo ``rules.xml`` syntax is very similar to the XDV one, and your XDV
rules should continue to work unchanged once the namespace is updated. Where
in XDV you would have::

    <rules
        xmlns="http://namespaces.plone.org/xdv"
        xmlns:css="http://namespaces.plone.org/xdv+css"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
        ...
    
    </rules>

you should now use::

    <rules
        xmlns="http://namespaces.plone.org/diazo"
        xmlns:css="http://namespaces.plone.org/diazo/css"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
        ...
    
    </rules>

In addition, some rules have been changed to simplify the rule set:

* ``<copy />`` should only be used for copying attributes. For the use case
  that ``<copy />`` used to cover, use ``<replace />`` with ``theme-children``
  instead.
* ``<prepend />`` has similarly been replaced by ``<before />`` with
  ``theme-children``.
* ``<append />`` has similarly been replaced by ``<after />`` with
  ``theme-children``.

Please see the `Diazo`_ documentation for more details about the available
rules, including new rules only available in Diazo.

Plone integration changes
-------------------------

If you have installed a theme using ``collective.xdv``, and you wish to
migrate to ``plone.app.theming``, you should use the following steps.

1. Start up your Plone site, go to the ``portal_quickinstaller`` tool in
   the ZMI and uninstall the XDV theme integration package.

2. Stop your Plone site, and remove ``collective.xdv`` from your buildout,
   by removing any references in ``buildout.cfg`` (or a file it extends),
   and any references in an ``install_requires`` line in a ``setup.py`` file
   you control.

3. Install ``plone.app.theming`` as described above, adjusting your theme
   package as required.

You will notice that ``plone.app.theming`` exposes fewer options than
``collective.xdv``. This is mainly because the relevant features have moved
into ``Diazo`` itself and can be configured in the ``rules.xml`` file.

.. _Diazo: http://diazo.org
.. _Plone: http://plone.org
.. _plone.resource: http://pypi.python.org/pypi/plone.resource
.. _the buildout manual: http://plone.org/documentation/manual/developer-manual/managing-projects-with-buildout
.. _z3c.jbot: http://pypi.python.org/pypi/z3c.jbot
