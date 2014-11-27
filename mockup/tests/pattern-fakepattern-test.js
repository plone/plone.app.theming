// tests for fakepattern
//
// @author Eric BREHAULT
// @version 0.0.1
// @licstart  The following is the entire license notice for the JavaScript
//            code in this page.
//
// Copyright (C) 2010 Plone Foundation
//
// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation; either version 2 of the License.
//
// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along with
// this program; if not, write to the Free Software Foundation, Inc., 51
// Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
//
// @licend  The above is the entire license notice for the JavaScript code in
//          this page.
//

define([
  'chai',
  'jquery',
  'mockup-registry',
  'thememapperbundle-patterns-fakepattern'
], function(chai, $, registry, CookieDirective) {
  "use strict";

  var expect = chai.expect,
      mocha = window.mocha;

  mocha.setup('bdd');
  $.fx.off = true;

/* ==========================
   TEST: fakepattern
  ========================== */

  describe("fakepattern", function () {
    afterEach(function() {
      // Put here code that executes after each test
    });
    beforeEach(function() {
      // Put here code that executes before each test
      this.$el = $('' +
        '<div class="pat-fakepattern">' +
        '</div>');
    });
    it("test case 1", function() {
      expect(this.$el.hasClass("pat-fakepattern")).to.be.equal(true);
      registry.scan(this.$el);
      expect(this.$el.hasClass("pat-fakepattern")).to.be.equal(true);
    });
  });

});
