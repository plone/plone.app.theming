/* global require, window, OPEN_OVERLAY */
/* jshint quotmark: false */

if(require === undefined){
    require = function(reqs, torun){  // jshint ignore:line
        'use strict';
        return torun(window.jQuery);
    };
}

require([ // jshint ignore:line
    'jquery',
    'resource-plone-app-jquerytools-js'
], function($) {
    'use strict';

    $().ready(function() {

        $('.previewImageContainer').click(function() {
            window.open($(this).attr("href"), "preview");
            return false;
        });

        // move to top so overlays work
        $(".overlay").appendTo("body");

        // Help overlay
        $("#helpButtonForm").prepOverlay({
            subtype: 'iframe'
        });

        // Test Styles /test_rendering
        $("#testStylesButton").click(function() {
                window.open($("base").attr("href") + 'test_rendering#top', "_blank");
                return false;
        });
        // Create/copy overlay
        $("#overlay-new-theme").overlay();
        $("#overlayTitleNewTheme").show();
        $("#overlayTitleCopyTheme").hide();

        $("#createButton").click(function() {
            $("#baseOn").val('template');
            $("#overlayTitleNewTheme").show();
            $("#overlayTitleCopyTheme").hide();
            $("#overlay-new-theme").data('overlay').load();


            $("#overlay-new-theme .field.error").removeClass('error');
            $("#overlay-new-theme .errorMessage").remove();

            return false;
        });

        $(".copyButton").click(function() {
            $("#baseOn").val($(this).parents(".themeEntry").attr('data-theme'));
            $("#overlayTitleNewTheme").hide();
            $("#overlayTitleCopyTheme span").html($(this).parents(".themeEntry").attr('data-theme-title'));
            $("#overlayTitleCopyTheme").show();
            $("#overlay-new-theme").data('overlay').load();

            $("#overlay-new-theme .field.error").removeClass('error');
            $("#overlay-new-theme .errorMessage").remove();

            return false;
        });

        $("#overlay-new-theme input[name='form.button.Cancel']").click(function() {
            $("#overlay-new-theme").data('overlay').close();
            return false;
        });

        // Delete confirm overlay
        $("#overlay-delete-confirm").overlay();

        $(".deleteLink").click(function() {
            $("#deleteConfirmTheme").val($(this).parents(".themeEntry").attr('data-theme'));
            $("#overlayTitleDeleteConfirm span").html($(this).parents(".themeEntry").attr('data-theme-title'));
            $("#overlay-delete-confirm").data('overlay').load();
            return false;
        });

        $("#overlay-delete-confirm input[name='form.button.Cancel']").click(function() {
            $("#overlay-delete-confirm").data('overlay').close();
            return false;
        });

        // Upload overlay
        $("#overlay-upload").overlay();

        $("#uploadButton").click(function() {

            $("#overlay-upload .field.error").removeClass('error');
            $("#overlay-upload .errorMessage").remove();

            $("#overlay-upload").data('overlay').load();
            return false;
        });

        $("#overlay-upload input[name='form.button.Cancel']").click(function() {
            $("#overlay-upload").data('overlay').close();
            return false;
        });

        // Open overlay if there was an error
        if(OPEN_OVERLAY) {

            if(OPEN_OVERLAY == 'new-theme') {
                var baseOn = $("#baseOn").val();
                if(baseOn != 'template') { // operation was a copy
                    $("#overlayTitleNewTheme").hide();
                    $("#overlayTitleCopyTheme span").html($("#themeEntry-" + baseOn).attr('data-theme-title'));
                    $("#overlayTitleCopyTheme").show();
                }
            }

            var triggeredOverlay = $("#overlay-" + OPEN_OVERLAY).data('overlay');
            if(triggeredOverlay) triggeredOverlay.load();
        }

    });
});