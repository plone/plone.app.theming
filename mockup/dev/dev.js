(function($) {
  "use strict";

  $(document).ready(function() {

    var splitted_location = document.URL.split('/');
    var current_folder = splitted_location.splice(2, splitted_location.length-4).join('/');

    var style1 = document.createElement('style');
    style1.setAttribute('type', 'text/less');
    style1.innerHTML = '\n\
                        @import (less) "../less/thememapperbundle.less";\n\
                        @isBrowser: true;\n\
                        @pathPrefix: \'../less/\';\n\
                        @bowerPath: \''+current_folder+'/bower_components\';\n\
                        @mockupPath: \'../bower_components/plone-mockup/patterns"\';\n\
                        @mockuplessPath: \'"less/"\';';
    document.getElementsByTagName("head")[0].appendChild(style1);

    var script_less = document.createElement('script');
    script_less.setAttribute('type', 'text/javascript');
    script_less.setAttribute('src', '../node_modules/less/dist/less-1.7.5.js');
    document.getElementsByTagName("head")[0].appendChild(script_less);
    script_less.onload = function() {
        var script_require = document.createElement('script');
        script_require.setAttribute('type', 'text/javascript');
        script_require.setAttribute('src', '../node_modules/requirejs/require.js');
        document.getElementsByTagName("head")[0].appendChild(script_require);
        script_require.onload = function() {
            var script_config = document.createElement('script');
            script_config.setAttribute('type', 'text/javascript');
            script_config.setAttribute('src', '../config.js');
            document.getElementsByTagName("head")[0].appendChild(script_config);
            script_config.onload = function() {
                requirejs.config({ baseUrl: '../' });
                require(['mockup-bundles-thememapperbundle']);
            };
        };
    };

  });

}(jQuery));
