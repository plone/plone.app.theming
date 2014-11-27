/* globals module:true */

module.exports = function(grunt) {
  'use strict';

  var MockupGrunt = require('./bower_components/mockup-core/js/grunt'),
      requirejsOptions = require('./config'),
      mockup = new MockupGrunt(requirejsOptions);

  mockup.registerBundle('thememapperbundle', {
    less: {
      options : {
        modifyVars : {
          bowerPath: '"bower_components/"',
          mockupPath: '"bower_components/plone-mockup/patterns/"',
          mockuplessPath: '"less/"'
        }
      }
    }
  }, {
    url: 'thememapperbundle'
  });

  mockup.initGrunt(grunt, {
    sed: {
      bootstrap: {
        path: 'node_modules/lcov-result-merger/index.js',
        pattern: 'throw new Error\\(\'Unknown Prefix ',
        replacement: '//throw// new Error(\'Unknown Prefix '
      }
    }
  });

};
