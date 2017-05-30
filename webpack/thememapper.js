const jQuery = require('jquery');
const registry = require('pat-registry');
const thememapper = require('mockup-patterns-thememapper');

jQuery(function($) {
  registry.scan($('body'));
});

require('./thememapper.less');
