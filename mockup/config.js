(function() {
  'use strict';
  var tinymcePlugins = ['advlist', 'anchor', 'autolink', 'autoresize', 'autosave', 'bbcode', 'charmap',
                        'code', 'colorpicker', 'contextmenu', 'directionality', 'emoticons', 'fullpage',
                        'fullscreen', 'hr', 'image', 'importcss', 'insertdatetime', 'layer', 'legacyoutput',
                        'link', 'lists', 'media', 'nonbreaking', 'noneditable', 'pagebreak', 'paste',
                        'preview', 'print', 'save', 'searchreplace', 'spellchecker', 'tabfocus', 'table',
                        'template', 'textcolor', 'textpattern', 'visualblocks', 'visualchars', 'wordcount'];

  var requirejsOptions = {
    baseUrl: './',
    wrap: true,
    almond: true,
    optimize: 'none',
    paths: {
      'ace': 'bower_components/ace-builds/src/ace',
      'ace-theme-monokai': 'bower_components/ace-builds/src/theme-monokai',
      'ace-mode-text': 'bower_components/ace-builds/src/mode-text',
      'ace-mode-javascript': 'bower_components/ace-builds/src/mode-javascript',
      'ace-mode-css': 'bower_components/ace-builds/src/mode-css',
      'backbone': 'bower_components/backbone/backbone',
      'backbone.paginator': 'bower_components/backbone.paginator/lib/backbone.paginator',
      'bootstrap-alert': 'bower_components/bootstrap/js/alert',
      'bootstrap-collapse': 'bower_components/bootstrap/js/collapse',
      'bootstrap-dropdown': 'bower_components/bootstrap/js/dropdown',
      'bootstrap-tooltip': 'bower_components/bootstrap/js/tooltip',
      'bootstrap-transition': 'bower_components/bootstrap/js/transition',
      'chai': 'bower_components/chai/chai',
      'docs-getting-started': 'bower_components/plone-mockup/GETTING_STARTED.md',
      'docs-learn': 'bower_components/plone-mockup/LEARN.md',
      'docs-contribute': 'bower_components/plone-mockup/CONTRIBUTE.md',
      'domready': 'bower_components/domready/ready',
      'dropzone': 'bower_components/dropzone/downloads/dropzone-amd-module',
      'expect': 'bower_components/expect/index',
      'jqtree': 'bower_components/jqtree/tree.jquery',
      'jquery': 'bower_components/jquery/dist/jquery',
      'jquery.form': 'bower_components/jquery-form/jquery.form',
      'jquery.cookie': 'bower_components/jquery.cookie/jquery.cookie',
      'jquery.event.drag': 'bower_components/plone-mockup/lib/jquery.event.drag',
      'jquery.event.drop': 'bower_components/plone-mockup/lib/jquery.event.drop',
      'JSXTransformer': 'bower_components/react/JSXTransformer',
      'marked': 'bower_components/marked/lib/marked',
      'mockup-bundles-docs': 'bower_components/plone-mockup/js/bundles/docs',
      'mockup-bundles-plone': 'bower_components/plone-mockup/js/bundles/plone',
      'mockup-bundles-structure': 'bower_components/plone-mockup/js/bundles/structure',
      'mockup-bundles-tiles': 'bower_components/plone-mockup/js/bundles/tiles',
      'mockup-bundles-widgets': 'bower_components/plone-mockup/js/bundles/widgets',
      'mockup-bundles-filemanager': 'bower_components/plone-mockup/js/bundles/filemanager',
      'mockup-bundles-resourceregistry': 'bower_components/plone-mockup/js/bundles/resourceregistry',
      'mockup-docsapp': 'bower_components/plone-mockup/js/docsapp',
      'mockup-docs': 'bower_components/mockup-core/js/docs/app',
      'mockup-docs-page': 'bower_components/mockup-core/js/docs/page',
      'mockup-docs-pattern': 'bower_components/mockup-core/js/docs/pattern',
      'mockup-docs-view': 'bower_components/mockup-core/js/docs/view',
      'mockup-docs-navigation': 'bower_components/mockup-core/js/docs/navigation',
      'mockup-fakeserver': 'bower_components/plone-mockup/tests/fakeserver',
      'mockup-iframe': 'bower_components/plone-mockup/js/iframe',
      'mockup-iframe_init': 'bower_components/plone-mockup/js/iframe_init',
      'mockup-patterns-accessibility': 'bower_components/plone-mockup/patterns/accessibility/pattern',
      'mockup-patterns-autotoc': 'bower_components/plone-mockup/patterns/autotoc/pattern',
      'mockup-patterns-backdrop': 'bower_components/plone-mockup/patterns/backdrop/pattern',
      'mockup-patterns-base': 'bower_components/mockup-core/js/pattern',
      'mockup-patterns-sortable': 'bower_components/plone-mockup/patterns/sortable/pattern',
      'mockup-patterns-formautofocus': 'bower_components/plone-mockup/patterns/formautofocus/pattern',
      'mockup-patterns-formunloadalert': 'bower_components/plone-mockup/patterns/formunloadalert/pattern',
      'mockup-patterns-modal': 'bower_components/plone-mockup/patterns/modal/pattern',
      'mockup-patterns-moment': 'bower_components/plone-mockup/patterns/moment/pattern',
      'mockup-patterns-pickadate': 'bower_components/plone-mockup/patterns/pickadate/pattern',
      'mockup-patterns-preventdoublesubmit': 'bower_components/plone-mockup/patterns/preventdoublesubmit/pattern',
      'mockup-patterns-querystring': 'bower_components/plone-mockup/patterns/querystring/pattern',
      'mockup-patterns-relateditems': 'bower_components/plone-mockup/patterns/relateditems/pattern',
      'mockup-patterns-select2': 'bower_components/plone-mockup/patterns/select2/pattern',
      'mockup-patterns-structure-url': 'bower_components/plone-mockup/patterns/structure',
      'mockup-patterns-structure': 'bower_components/plone-mockup/patterns/structure/pattern',
      'mockup-patterns-texteditor': 'bower_components/plone-mockup/patterns/texteditor/pattern',
      'mockup-patterns-filemanager-url': 'bower_components/plone-mockup/patterns/filemanager',
      'mockup-patterns-filemanager': 'bower_components/plone-mockup/patterns/filemanager/pattern',
      'mockup-patterns-thememapper-url': 'bower_components/plone-mockup/patterns/thememapper',
      'mockup-patterns-thememapper': 'bower_components/plone-mockup/patterns/thememapper/pattern',
      'mockup-patterns-tablesorter': 'bower_components/plone-mockup/patterns/tablesorter/pattern',
      'mockup-patterns-tinymce-url': 'bower_components/plone-mockup/patterns/tinymce',
      'mockup-patterns-tinymce': 'bower_components/plone-mockup/patterns/tinymce/pattern',
      'mockup-patterns-toggle': 'bower_components/plone-mockup/patterns/toggle/pattern',
      'mockup-patterns-tooltip': 'bower_components/plone-mockup/patterns/tooltip/pattern',
      'mockup-patterns-tree': 'bower_components/plone-mockup/patterns/tree/pattern',
      'mockup-patterns-upload-url': 'bower_components/plone-mockup/patterns/upload',
      'mockup-patterns-upload': 'bower_components/plone-mockup/patterns/upload/pattern',
      'mockup-patterns-resourceregistry': 'bower_components/plone-mockup/patterns/resourceregistry/pattern',
      'mockup-patterns-eventedit': 'bower_components/plone-mockup/patterns/eventedit/pattern',
      'mockup-registry': 'bower_components/mockup-core/js/registry',
      'mockup-router': 'bower_components/plone-mockup/js/router',
      'mockup-utils': 'bower_components/plone-mockup/js/utils',
      'mockup-i18n': 'bower_components/plone-mockup/js/i18n',
      'mockup-ui-url': 'bower_components/plone-mockup/js/ui',
      'moment': 'bower_components/moment/moment',
      'picker': 'bower_components/pickadate/lib/picker',
      'picker.date': 'bower_components/pickadate/lib/picker.date',
      'picker.time': 'bower_components/pickadate/lib/picker.time',
      'react': 'bower_components/react/react',
      'select2': 'bower_components/select2/select2',
      'sinon': 'bower_components/sinonjs/sinon',
      'tinymce': 'bower_components/tinymce-builded/js/tinymce/tinymce',
      'tinymce-modern-theme': 'bower_components/tinymce/themes/modern/theme',
      'text': 'bower_components/requirejs-text/text',
      'mockup-bundles-thememapperbundle': 'js/bundles/thememapperbundle',
      'thememapperbundle-patterns-fakepattern': 'js/patterns/fakepattern',
      'underscore': 'bower_components/lodash/dist/lodash.underscore'
    },
    shim: {
      'JSXTransformer': { exports: 'window.JSXTransformer' },
      'backbone': { exports: 'window.Backbone', deps: ['underscore', 'jquery'] },
      'backbone.paginator': { exports: 'window.Backbone.Paginator', deps: ['backbone'] },
      'bootstrap-alert': { deps: ['jquery'] },
      'bootstrap-collapse': {exports: 'window.jQuery.fn.collapse.Constructor', deps: ['jquery']},
      'bootstrap-dropdown': { deps: ['jquery'] },
      'bootstrap-tooltip': { deps: ['jquery'] },
      'bootstrap-transition': {exports: 'window.jQuery.support.transition', deps: ['jquery']},
      'expect': {exports: 'window.expect'},
      'jqtree': { deps: ['jquery'] },
      'jquery.cookie': { deps: ['jquery'] },
      'jquery.event.drag': { deps: ['jquery'] },
      'jquery.event.drop': {
        deps: ['jquery'],
        exports: '$.drop'
      },
      'mockup-iframe_init': { deps: ['domready'] },
      'picker.date': { deps: [ 'picker' ] },
      'picker.time': { deps: [ 'picker' ] },
      'sinon': {exports: 'window.sinon'},
      'underscore': { exports: 'window._' },
      'sinon-fakexmlhttprequest': { exports: 'window.sinon',  deps: [ 'sinon' ] },
      'sinon-fakeserver': {
        exports: 'window.sinon.fakeServer',
        deps: [ 'sinon', 'sinon-fakexmlhttprequest' ]
      },
      'sinon-faketimers': {
        exports: 'window.sinon.useFakeTimers',
        deps: [ 'sinon', 'sinon-fakexmlhttprequest' ]
      },
      'tinymce': {
        exports: 'window.tinyMCE',
        init: function () {
          this.tinyMCE.DOM.events.domLoaded = true;
          return this.tinyMCE;
        }
      },
      'tinymce-modern-theme': {
        deps: ['tinymce']
      }
    },
    wrapShim: true
  };

  for(var i=0; i<tinymcePlugins.length; i=i+1){
    var plugin = tinymcePlugins[i];
    requirejsOptions.paths['tinymce-' + plugin] = 'bower_components/tinymce/plugins/' + plugin + '/plugin';
    requirejsOptions.shim['tinymce-' + plugin] = {
      deps: ['tinymce']
    };
  }

  if (typeof exports !== "undefined" && typeof module !== "undefined") {
    module.exports = requirejsOptions;
  }
  if (typeof requirejs !== "undefined" && requirejs.config) {
    requirejs.config(requirejsOptions);
  }

}());
