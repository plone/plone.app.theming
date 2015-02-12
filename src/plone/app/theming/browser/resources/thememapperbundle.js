/* globals requirejs, require */

(function() {
  'use strict';
  require(['jquery'], function($){
    $(document).ready(function() {
      requirejs.config({
        paths: {
          'mockup-patterns-thememapper-url': '++resource++mockup/thememapper',
          'mockup-patterns-filemanager-url': '++resource++mockup/filemanager',
          'mockup-patterns-filemanager': '++resource++mockup/filemanager/pattern',
        }
      });
      require(['++resource++mockup/thememapper/pattern.js', 'pat-registry'], function(mapper, registry){
        if (!registry.initialized) {
          registry.init();
        }
      });
    });
  });

}());
