Changelog
=========

1.3.4 (2016-12-30)
------------------

Bug fixes:

- Make diazo.debug work again when DIAZO_ALWAYS_CACHE_RULES is set.
  [ale-rt]


1.3.3 (2016-12-02)
------------------

Bug fixes:

- Remove roman monkey patch.
  [gforcada]

1.3.2 (2016-09-23)
------------------

New features:

- Add Update -button for theming control panel making it possible to
  reload modified theme manifest without deactivating theme at first.
  [datakurre]


1.3.1 (2016-09-07)
------------------

Fixes:

- Enable unload protection by using pattern class ``pat-formunloadalert`` instead ``enableUnloadProtection``.
  [thet]

- Small fix in documentation
  [staeff]

- Fix issue where theming control panel errored when a packaged
  theme was overidden with a global resource directory theme
  [datakurre]

1.3.0 (2016-06-07)
------------------

New:

- Control theme compilation in development mode
  through the environment variable ``DIAZO_ALWAYS_CACHE_RULES``
  [ale-rt]

Fixes:

- Small fixes to documentaion
  [ale-rt]

1.2.19 (2016-03-31)
-------------------

New:

- For the theming controlpanel, change base URLs from portal URL to what getSite returns, but don't change the controlpanels context binding.
  This allows for more flexibility when configuring it to be allowed on a sub site with a local registry.
  [thet]


1.2.18 (2016-03-03)
-------------------

Fixes:

- Fixed html validation: element nav does not need a role attribute.
  [maurits]

- Handle potential scenarios where wrong theme would show selected in the theming
  control panel
  [vangheem]


1.2.17 (2016-02-11)
-------------------

New:

- Documented how to disable diazo transform by setting the
  ``X-Theme-Disabled`` header.  [ale-rt]

Fixes:

- Rebuild resources so they work with latest mockup/patternslib
  integration changes.  [vangheem]

- Removed github dependancies in thememapper.  [Gagaro]


1.2.16 (2015-11-26)
-------------------

Fixes:

- Updated Site Setup link in all control panels.
  Fixes https://github.com/plone/Products.CMFPlone/issues/1255
  [davilima6]


1.2.15 (2015-10-28)
-------------------

Fixes:

- Do not fail in ``isThemeEnabled`` when we have no settings, for
  example when migrating from Plone 3 to Plone 5, but maybe also in
  other cases.
  [maurits]

- Fixed Unicode Encode Error when to copy into multi-byte title / description
  [terapyon]


1.2.14 (2015-09-27)
-------------------

- Fix i18n in mapper.pt
  [vincentfretin]


1.2.13 (2015-09-20)
-------------------

- Pull mark_special_links, external_links_open_new_window values
  from configuration registry.
  [esteele]

- Fix visual glitch on Safari
  [davilima6]

- Show active theme at the top of the theme list.
  Fixes https://github.com/plone/plone.app.theming/issues/70
  [tmassman]


1.2.12 (2015-09-15)
-------------------

- Remove bundled twitter bootstrap theme 'example'.
  Fixes https://github.com/plone/Products.CMFPlone/issues/877
  [pbauer]

- Remove duplicate type attribute for theming control panel delete modal.
  [esteele]


1.2.11 (2015-09-11)
-------------------

- rewrite manifest from copied theme with relative paths also
  [vangheem]


1.2.10 (2015-09-08)
-------------------

- theme mapper fixes for odd behavior in save files at times
  [swartz]


1.2.9 (2015-08-22)
------------------

- Build thememapper resources.
  [vangheem]

- Added cache invalidation option.
  [swartz]


1.2.8 (2015-08-20)
------------------

- change link from plone.org to plone.com.
  [tkimnguyen]

- fix toolbar on control panel
  [vangheem]

- fix less building
  [obct537]

- Fixed copy modal for themes with a dot in the name.
  [Gagaro]


1.2.7 (2015-07-18)
------------------

- Provide better styling to themeing control panel, less build, finish implementation
  [obct537]

- make sure when copying themes that you try to modify the base urls
  to match the new theme are all the manifest.cfg settings
  [vangheem]

- implement switchable theming policy API, re-implement theme caching
  [gyst]

- fixed configuration of copied theme
  [vmaksymiv]

- implemented upload for theme manager
  [schwartz]

- Change the category of the configlet to 'plone-general'.
  [sneridagh]


1.2.6 (2015-06-05)
------------------

- removed irrelevant theme renaming code
  [schwartz]

- Filesystem themes are now correctly overridden. TTW themes can no longer be overriden
  [schwartz]

- re-added manifest check
  [schwartz]

- Fixed broken getTheme method
  [schwartz]

- Minor ReStructuredText fixes for documentation.
  [maurits]


1.2.5 (2015-05-13)
------------------

- Fix RestructuredText representation on PyPI by bringing back a few
  example lines in the manifest.
  [maurits]


1.2.4 (2015-05-12)
------------------

- Add setting for tinymce automatically detected styles
  [vangheem]

1.2.3 (2015-05-04)
------------------

- fix AttributeError: 'NoneType' object has no attribute 'getroottree' when the result is not
  html / is empty.
  [sunew]

- make control panel usable again. Fixed problem where skins
  control panel is no longer present.
  [vangheem]

- unified different getTheme functions.
  [jensens]

- pep8ified, housekeeping, cleanup
  [jensens]

- Specify i18n:domain in controlpanel.pt.
  [vincentfretin]

- pat-modal pattern has been renamed to pat-plone-modal
  [jcbrand]

- Fix load pluginSettings for the enabled theme before calling plugins for
  onEnabled and call onEnabled plugins with correct parameters
  [datakurre]


1.2.2 (2015-03-22)
------------------

- Patch the ZMI only for available ZMI pages.
  [thet]

- Change deprecated import of ``zope.site.hooks.getSite`` to
  ``zope.component.hooks.getSite``.
  [thet]

- Add an error log if the subrequest failed (probably a relative xi:include)
  instead of silently returning None (and so having a xi:include returning
  nothing).
  [vincentfretin]

- Fix transform to not affect the result when theming is disabled
  [datakurre]

- Integrate thememapper mockup pattern and fix theming control panel
  to be more usable
  [ebrehault]


1.2.1 (2014-10-23)
------------------

- Remove DL's from portal message in templates.
  https://github.com/plone/Products.CMFPlone/issues/153
  [khink]

- Fix "Insufficient Privileges" for "Site Administrators" on the control panel.
  [@rpatterson]

- Add IThemeAppliedEvent
  [vangheem]

- Put themes in a separate zcml file to be able to exclude them
  [laulaz]

- #14107 bot requests like /widget/oauth_login/info.txt causes
  problems finding correct context with plone.app.theming
  [anthonygerrard]

- Added support for ++theme++ to traverse to the contents of the
  current activated theme.
  [bosim]


1.2.0 (2014-03-02)
------------------

- Disable theming for manage_shutdown view.
  [davisagli]

- Fix reference to theme error template
  [afrepues]

- Add "Test Styles" button in control panel to expose, test_rendering template.
  [runyaga]

1.1.1 (2013-05-23)
------------------

- Fixed i18n issues.
  [thomasdesvenain]

- Fixed i18n issues.
  [jianaijun]

- This fixed UnicodeDecodeError when Theme Title is Non-ASCII
  in the manifest.cfg file.
  [jianaijun]


1.1 (2013-04-06)
----------------

- Fixed i18n issues.
  [vincentfretin]

- Make the template theme do what it claims to do: copy styles as
  well as scripts.
  [smcmahon]

- Change the label and description for the example theme to supply useful
  information.
  [smcmahon]

- Upgrades from 1.0 get the combined "Theming" control panel that was added in
  1.1a1.
  [danjacka]


1.1b2 (2013-01-01)
------------------

- Ensure host blacklist utilises SERVER_URL to correctly determine hostname
  for sites hosted as sub-folders at any depth.
  [davidjb]

- Add test about plone.app.theming / plone.app.caching integration when
  using GZIP compression for anonymous
  (see ticket `12038 <https://dev.plone.org/ticket/12038>`_). [ebrehault]


1.1b1 (2012-10-16)
------------------

- Add diazo.debug option, route all error_log output through
  this so debugging can be displayed
  [lentinj]

- Make example Bootstrap-based theme use the HTML5 DOCTYPE.
  [danjacka]

- Demote ZMI patch log message to debug level.
  [hannosch]

- Upgrade to ACE 1.0 via plone.resourceeditor
  [optilude]

- Put quotes around jQuery attribute selector values to appease
  jQuery 1.7.2.
  [danjacka]

1.1a2 (2012-08-30)
------------------

- Protect the control panel with a specific permission so it can be
  delegated.
  [davisagli]

- Advise defining ajax_load as ``request.form.get('ajax_load')`` in
  manifest.cfg.  For instance, the login_form has an hidden empty
  ajax_load input, which would give an unthemed page after submitting
  the form.
  [maurits]

- Change theme editor page templates to use main_template rather than
  prefs_main_template to avoid inserting CSS and JavaScript too early
  under plonetheme.classic.
  [danjacka]

1.1a1 (2012-08-08)
------------------

- Replace the stock "Themes" control panel with a renamed "Theming" control
  panel, which incorporates the former's settings under its "Advanced" tab.
  [optilude]

- Add a full in-Plone theme authoring environment
  [optilude, vangheem]

- Update IBeforeTraverseEvent import to zope.traversing.
  [hannosch]

- On tab "Manage themes", change table header to
  better describe what's actually listed.
  [kleist]

1.0 (2012-04-15)
----------------

* Prevent AttributeError when getRequest returns None.
  [maurits]

* Calculate subrequests against navigation root rather than portal.
  [elro]

* Supply closest context found for 404 pages.
  [elro]

* Lookup portal state with correct context.
  [elro]

1.0b9 - 2011-11-02
------------------

* Patch App.Management.Navigation to disable theming of ZMI pages.
  [elro]

1.0b8 - 2011-07-04
------------------

* Evaluate theme parameters regardless of whether there is a valid context or
  not (e.g. when templating a 404 page).
  [lentinj]

1.0b7 - 2011-06-12
------------------

* Moved the *views* and *overrides* plugins out into a separate package
  ``plone.app.themingplugins``. If you want to use those features, you need
  to install that package in your buildout. Themes attempting to register
  views or overrides in environments where ``plone.app.themingplugins`` is not
  installed will install, but views and overrides will not take effect.
  [optilude]

1.0b6 - 2011-06-08
------------------

* Support for setting arbitrary Doctypes.
  [elro]

* Upgrade step to update plone.app.registry configuration.
  [elro]

* Fixed plugin initialization when applying a theme.
  [maurits]

* Query the resource directory using the 'currentTheme' name instead
  of the Theme object (updating the control panel was broken).
  [maurits]

* Fix zip import (plugin initialization was broken.)
  [elro]

1.0b5 - 2011-05-29
------------------

* Make sure the control panel is never themed, by setting the X-Theme-Disabled
  response header.
  [optilude]

* Add support for registering new views from Zope Page Templates and
  overriding existing templates. See README for more details.
  [optilude]

1.0b4 - 2011-05-24
------------------

* Add support for ``X-Theme-Disabled`` response header.
  [elro]

* Make "Replace existing theme" checkbox default to off.
  [elro]

* Fix control panel to correctly display a newly uploaded theme.
  [elro]

* Fix zip import to work correctly when no manifest is supplied.
  [elro]

1.0b3 - 2011-05-23
------------------

* Show theme name along with title in control panel.
  [elro]

1.0b2 - 2011-05-16
------------------

* Encode internally resolved documents to support non-ascii characters
  correctly.
  [elro]

* Fix control panel to use theme name not id.
  [optilude]

1.0b1 - 2011-04-22
------------------

* Wrap internal subrequests for css or js in style or script tags to
  facilitate inline includes.
  [elro]

* Add ``theme.xml`` import step (see README).
  [optilude]

* Add support for ``[theme:parameters]`` section in ``manifest.cfg``, which
  can be used to set parameters and the corresponding TALES expressions to
  calculate them.
  [optilude]

* Add support for parameter expressions based on TALES expressions
  [optilude]

* Use plone.subrequest 1.6 features to work with IStreamIterator from
  plone.resource.
  [elro]

* Depend on ``Products.CMFPlone`` instead of ``Plone``.
  [elro]

* Added support for uploading themes as Zip archives.
  [optilude]

* Added theme off switch: Add a query string parameter ``diazo.off=1`` to a
  request whilst Zope is in development mode to turn off the theme.
  [optilude]

* Removed 'theme' and alternative themes support: Themes should be referenced
  using the ``<theme />`` directive in the Diazo rules file.
  [optilude]

* Removed 'domains' support: This can be handled with the rules file syntax
  by using the ``host`` parameter.
  [optilude]

* Removed 'notheme' support: This can be handled within the rules file syntax
  by using the ``path`` parameter.
  [optilude]

* Added ``path`` and ``host`` as parameters to the Diazo rules file. These
  can now be used as conditional expressions.
  [optilude]

* Removed dependency on XDV in favour of dependency on Diazo (which is the
  new name for XDV).
  [optilude]

* Forked from collective.xdv 1.0rc11.
  [optilude]
