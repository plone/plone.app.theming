/**
 *	Filemanager JS core
 *
 *	filemanager.js
 *
 *	@license	MIT License
 *	@author		Jason Huck - Core Five Labs
 *	@author		Simon Georget <simon (at) linea21 (dot) com>
 *	@copyright	Authors
 */

(function($) {
$(function(){


var prompt = $('#pb_prompt');
prompt.overlay({
	mask: {
		color: '#DDDDDD',
		loadSpeed: 200,
		opacity: 0.9
	},
	top : 0,
    fixed : false,
    closeOnClick: false
});

var showPrompt = function(options){
	if(options.description === undefined){ options.description = '';}
	if(options.buttons === undefined){ options.buttons = ['OK'];}
	if(options.callback === undefined){ options.callback = function(){};}
	if(options.prompt === undefined){ options.prompt = false;}
	if(options.inputValue === undefined){ options.inputValue = '';}

	// Clear old values
	$('h1.documentFirstHeading,.documentDescription,.formControls', prompt).html('');
	$('input[type="text"]', prompt).val(options.inputValue);

	//fill new values
	$('h1.documentFirstHeading', prompt).html(options.title);
	$('.documentDescription', prompt).html(options.description);
	for(var i=0; i<options.buttons.length; i++){
		var button = options.buttons[i];
		$('.formControls', prompt).append(
			'<input class="context" type="submit" name="form.button.' + 
			button + '" value="' + button + '">');
	}
	if(options.prompt){
		$('.input', prompt).show();
	}else{
		$('.input', prompt).hide();
	}
	$('input[type="submit"]', prompt).click(function(){
		if(options.prompt){
			result = options.callback($(this).val(), $('input[type="text"]', prompt).val());
		}else{
			result = options.callback($(this).val());
		}
		prompt.overlay().close();
		if(typeof(result) == 'function'){
			result();
		}
		return false;
	});
	prompt.overlay().load();
}


var HTMLMode = require("ace/mode/html").Mode;
var CSSMode  = require("ace/mode/css").Mode;
var XMLMode  = require("ace/mode/xml").Mode;
var JSMode   = require("ace/mode/javascript").Mode;
var TextMode = require("ace/mode/text").Mode;

var extensionModes = {
    css: new CSSMode(),
    js: new JSMode(),
    htm: new HTMLMode(),
    html: new HTMLMode(),
    xml: new XMLMode()
};
var defaultMode = new TextMode();
var EDITORS = {};
 
// function to retrieve GET params
$.urlParam = function(name){
	var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
	if (results)
		return results[1]; 
	else
		return 0;
}

var getAuthenicator = function(){
    return $('input[name="_authenticator"]').eq(0).val();
}

/*---------------------------------------------------------
  Setup, Layout, and Status Functions
---------------------------------------------------------*/

// Forces columns to fill the layout vertically.
// Called on initial page load and on resize.
var setDimensions = function(){
	var newH = $(window).height() - $('#uploader').height() - 30;	
	$('#splitter, #filetree, #fileeditor, .vsplitbar').height(newH);
}

// Display Min Path
var displayPath = function(path) {
	if(showFullPath == false)
		return path.replace(fileRoot, "/");
	else 
		return path;
}

// preg_replace
// Code from : http://xuxu.fr/2006/05/20/preg-replace-javascript/
var preg_replace = function(array_pattern, array_pattern_replace, str)  {
	var new_str = String (str);
		for (i=0; i<array_pattern.length; i++) {
			var reg_exp= RegExp(array_pattern[i], "g");
			var val_to_replace = array_pattern_replace[i];
			new_str = new_str.replace (reg_exp, val_to_replace);
		}
		return new_str;
	}

// nameFormat (), separate filename from extension
// nameFormat
var nameFormat = function(input) {
	filename = '';
	if(input.lastIndexOf('.') != -1) {
		filename  = input.substr(0, input.lastIndexOf('.'));
		filename += '.' + input.split('.').pop();
	} else {
		filename = input;
	}
	return filename;
}


// Handle Error. Freeze interactive buttons and display
// error message. Also called when auth() function return false (Code == "-1")
var handleError = function(errMsg) {
	$('#newfile').attr("disabled", "disabled");
	$('#upload').attr("disabled", "disabled");
	$('#addnew').attr("disabled", "disabled");
    $('#newfolder').attr("disabled", "disabled");
}

// Test if Data structure has the 'cap' capability
// 'cap' is one of 'select', 'rename', 'delete', 'download'
function has_capability(data, cap) {
	if (data['File Type'] == 'dir' && cap == 'download') return false;
	if (typeof(data['Capabilities']) == "undefined") return true;
	else return $.inArray(cap, data['Capabilities']) > -1;
}

// from http://phpjs.org/functions/basename:360
var basename = function(path, suffix) {
    var b = path.replace(/^.*[\/\\]/g, '');

    if (typeof(suffix) == 'string' && b.substr(b.length-suffix.length) == suffix) {
        b = b.substr(0, b.length-suffix.length);
    }
    
    return b;
}

// Sets the folder status, upload, and new folder functions 
// to the path specified. Called on initial page load and 
// whenever a new directory is selected.
var setUploader = function(path){
	$('#currentpath').val(path);
	$('#uploader h1').text(lg.current_folder + displayPath(path));

    // New
    $('#addnew').unbind().click(function(){
        var filename = '';
        var msg = lg.prompt_filename + ' : <input id="fname" name="fname" type="text" value="' + filename + '" />';
        
        var getFileName = function(button, fname){
            if(button != lg.create_file){ return false;}

            if(fname != ''){
                filename = fname;
                $.ajax({
                    url: fileConnector,
                    data: {
                        mode: 'addnew',
                        path: $('#currentpath').val(),
                        name: filename,
                        _authenticator: getAuthenicator()
                    },
                    type: 'POST',
                    success: function(result){
                        if(result['Code'] == 0){
                            // addNewFile(result['Parent'], result['Name']);
                            // getFolderInfo(result['Parent']);
                            addNode(result['Parent'], result['Name']);
                        } else {
                            showPrompt({title:result['Error']});
                        }
                    }
                });
            } else {
                showPrompt({title: lg.no_filename});
            }
        }
        var btns = [lg.create_file, lg.cancel];
        showPrompt({title: msg, callback: getFileName, buttons: btns, prompt: true}); 
    }); 

	$('#newfolder').unbind().click(function(){
		var foldername =  lg.default_foldername;
		var msg = lg.prompt_foldername + ' : <input id="fname" name="fname" type="text" value="' + foldername + '" />';
		
		var getFolderName = function(button, fname){
			if(button != lg.create_folder){return false;}

			if(fname != ''){
				foldername = fname;
				$.getJSON(fileConnector, {
                        mode: 'addfolder',
                        path: $('#currentpath').val(),
                        name: foldername,
                        _authenticator: getAuthenicator()
                    }, function(result){
				       if(result['Code'] == 0){
					      addFolder(result['Parent'], result['Name']);
					      getFolderInfo(result['Parent']);
				       } else {
					      showPrompt({title:result['Error']});
				       }				
				    }
            );
			} else {
				showPrompt({title: lg.no_foldername});
			}
		}
		var btns = [lg.create_folder, lg.cancel];
		showPrompt({title: msg, callback: getFolderName, buttons: btns, prompt: true});	
	});	
}


// Converts bytes to kb, mb, or gb as needed for display.
var formatBytes = function(bytes){
	var n = parseFloat(bytes);
	var d = parseFloat(1024);
	var c = 0;
	var u = [lg.bytes,lg.kb,lg.mb,lg.gb];
	
	while(true){
		if(n < d){
			n = Math.round(n * 100) / 100;
			return n + u[c];
		} else {
			n /= d;
			c += 1;
		}
	}
}

// Renames the current item and returns the new name.
// Called by clicking the "Rename" button in detail views
// or choosing the "Rename" contextual menu option in 
// list views.
var renameItem = function(data){
	var finalName = '';

	var getNewName = function(button, rname){
		if(button != lg.rename){ return false; }
		var deffered = function(){};

		if(rname != ''){
			var givenName = nameFormat(rname);	
			var oldPath = data['Path'];	
		
			$.ajax({
				type: 'POST',
				url: fileConnector,
                data: {
                    mode: 'rename',
                    old: data['Path'],
                    new: givenName,
                    _authenticator: getAuthenicator()
                },
				dataType: 'json',
				async: false,
				success: function(result){
					finalName = result['New Name'];
					if(result['Code'] == 0){
						var newPath = result['New Path'];
						var newName = result['New Name'];
						updateNode(oldPath, newPath, newName);
						deffered = function(){ showPrompt({title: lg.successful_rename}); }
					} else {
						deffered = function(){ showPrompt({title: result['Error']}); }
					}
				}
			});	
		}
		return deffered
	}
	var btns = [lg.rename, lg.cancel];
	showPrompt({
		title: lg.new_filename,
		callback: getNewName,
		buttons: btns,
		inputValue: data['Filename'], 
		prompt: true});
	
	return finalName;
}

// Prompts for confirmation, then deletes the current item.
// Called by clicking the "Delete" button in detail views
// or choosing the "Delete contextual menu item in list views.
var deleteItem = function(data){
	var isDeleted = false;
	var msg = lg.confirmation_delete;
	
	var doDelete = function(button, value){
		if(button != lg.yes) return false;
	
		$.ajax({
			type: 'POST',
			url: fileConnector,
			dataType: 'json',
            data: {
                mode: 'delete',
                path: encodeURIComponent(data['Path']),
                _authenticator: getAuthenicator()
            },
			async: false,
			success: function(result){
				if(result['Code'] == 0){
					removeNode(result['Path']);
					var rootpath = result['Path'].substring(0, result['Path'].length-1); // removing the last slash
					rootpath = rootpath.substr(0, rootpath.lastIndexOf('/') + 1);
					$('#uploader h1').text(lg.current_folder + displayPath(rootpath));
					isDeleted = true;
					showPrompt({title: lg.successful_delete});
				} else {
					isDeleted = false;
					showPrompt({title: result['Error']});
				}			
			}
		});	
	}
	var btns = [lg.yes, lg.no];
	showPrompt({title: msg, callback: doDelete, buttons: btns});
	
	return isDeleted;
}


/*---------------------------------------------------------
  Functions to Update the File Tree
---------------------------------------------------------*/

// Adds a new node as the first item beneath the specified
// parent node. Called after a successful file upload.
var addNode = function(path, name){
	var ext = name.substr(name.lastIndexOf('.') + 1);
	var thisNode = $('#filetree').find('a[rel="' + path + '"]');
	var parentNode = thisNode.parent();
	var newNode = '<li class="file ext_' + ext + '"><a rel="' + path + name + '" href="#">' + name + '</a></li>';
	
	if(!parentNode.find('ul').size()) parentNode.append('<ul></ul>');		
	parentNode.find('ul').prepend(newNode);
	thisNode.click().click();

	getFolderInfo(path);

	showPrompt({title: lg.successful_added_file});
}

// Updates the specified node with a new name. Called after
// a successful rename operation.
var updateNode = function(oldPath, newPath, newName){
	var thisNode = $('#filetree').find('a[rel="' + oldPath + '"]');
	var parentNode = thisNode.parent().parent().prev('a');
	thisNode.attr('rel', newPath).text(newName);
	parentNode.click().click();

}

// Removes the specified node. Called after a successful 
// delete operation.
var removeNode = function(path){
    $('#filetree')
        .find('a[rel="' + path + '"]')
        .parent()
        .fadeOut('slow', function(){ 
            $(this).remove();
        });
    // remove fileinfo when item to remove is currently selected
    if ($('#preview').length) {
    	getFolderInfo(path.substr(0, path.lastIndexOf('/') + 1));
	}
}


// Adds a new folder as the first item beneath the
// specified parent node. Called after a new folder is
// successfully created.
var addFolder = function(parent, name){
	var newNode = '<li class="directory collapsed"><a rel="' + parent + name + '/" href="#">' + name + '</a><ul class="jqueryFileTree" style="display: block;"></ul></li>';
	var parentNode = $('#filetree').find('a[rel="' + parent + '"]');
	if(parent != fileRoot){
		parentNode.next('ul').prepend(newNode).prev('a').click().click();
	} else {
		$('#filetree > ul').prepend(newNode); 
		$('#filetree').find('li a[rel="' + parent + name + '/"]').click(function(){
				getFolderInfo(parent + name + '/');
			}).each(function() {
				$(this).contextMenu(
					{ menu: getContextMenuOptions($(this)) }, 
					function(action, el, pos){
						var path = $(el).attr('rel');
						setMenus(action, path);
					});
				}
			);
	}
	
	showPrompt({title: lg.successful_added_folder});
}

/*---------------------------------------------------------
  Functions to Retrieve File and Folder Details
---------------------------------------------------------*/


function getContextMenuOptions(elem) {
	var optionsID = elem.attr('class').replace(/ /g, '_');
	if (optionsID == "") return 'itemOptions';
	if (!($('#' + optionsID).length)) {
		// Create a clone to itemOptions with menus specific to this element
		var newOptions = $('#itemOptions').clone().attr('id', optionsID);
		if (!elem.hasClass('cap_download')) $('.download', newOptions).remove();
		if (!elem.hasClass('cap_rename')) $('.rename', newOptions).remove();
		if (!elem.hasClass('cap_delete')) $('.delete', newOptions).remove();
		$('#itemOptions').after(newOptions);
	}
	return optionsID;
}

// Binds contextual menus to items in list and grid views.
var setMenus = function(action, path){
	var d = new Date(); // to prevent IE cache issues
	$.getJSON(fileConnector + '?mode=getinfo&path=' + path + '&time=' + d.getMilliseconds(), function(data){
        switch(action){
            case 'download':
                window.location = fileConnector + '?mode=download&path=' + data['Path'];
                break;
                
            case 'rename':
                var newName = renameItem(data);
                break;
                
            case 'delete':
                deleteItem(data);
                break;
        }
	});
}

// Retrieves data for all items within the given folder and
// creates a list view. Binds contextual menu options.
// TODO: consider stylesheet switching to switch between grid
// and list views with sorting options.
var getFolderInfo = function(path){
	// Update location for status, upload, & new folder functions.
	setUploader(path);

	// Retrieve the data and generate the markup.
	var d = new Date(); // to prevent IE cache issues
	var url = fileConnector + '?path=' + encodeURIComponent(path) + '&mode=getfolder&showThumbs=' + showThumbs + '&time=' + d.getMilliseconds();
	if ($.urlParam('type')) url += '&type=' + $.urlParam('type');
	$.getJSON(url, function(data){
		var result = '';
		
		// Is there any error or user is unauthorized?
		if(data.Code=='-1') {
			handleError(data.Error);
			return;
		};
	});
}

// Retrieve data (file/folder listing) for jqueryFileTree and pass the data back
// to the callback function in jqueryFileTree
var populateFileTree = function(path, callback){
	var d = new Date(); // to prevent IE cache issues
	var url = fileConnector + '?path=' + encodeURIComponent(path) + '&mode=getfolder&showThumbs=' + showThumbs + '&time=' + d.getMilliseconds();
	if ($.urlParam('type')) url += '&type=' + $.urlParam('type');
	$.getJSON(url, function(data) {
		var result = '';
		// Is there any error or user is unauthorized?
		if(data.Code=='-1') {
			handleError(data.Error);
			return;
		};
		
		if(data) {
			result += "<ul class=\"jqueryFileTree\" style=\"display: none;\">";
			for(key in data) {
				var cap_classes = "";
				for (cap in capabilities) {
					if (has_capability(data[key], capabilities[cap])) {
						cap_classes += " cap_" + capabilities[cap];
					}
				}
				if (data[key]['File Type'] == 'dir') {
					result += "<li class=\"directory collapsed\"><a href=\"#\" class=\"" + cap_classes + "\" rel=\"" + data[key]['Path'] + "\">" + data[key]['Filename'] + "</a></li>";
				} else {
					result += "<li class=\"file ext_" + data[key]['File Type'].toLowerCase() + "\"><a href=\"#\" class=\"" + cap_classes + "\" rel=\"" + data[key]['Path'] + "\">" + data[key]['Filename'] + "</a></li>";
				}
			}
			result += "</ul>";
		} else {
			result += '<h1>' + lg.could_not_retrieve_folder + '</h1>';
		}
		callback(result);
	});
}

var setSaveState = function(){
    var li = $("#fileselector li.selected");
    if(li.hasClass('dirty')){
        $("#save")[0].disabled = false;
    }else{
        $("#save")[0].disabled = true;
    }
}


/*---------------------------------------------------------
  Initialization
---------------------------------------------------------*/

// Adjust layout.
setDimensions();
$(window).resize(setDimensions);

// we finalize the FileManager UI initialization 
// with localized text if necessary
if(autoload == true) {
	$('#upload').append(lg.upload);
	$('#addnew').append(lg.add_new);
    $('#save').append(lg.savemsg);
    $('#saveall').append(lg.saveallmsg);
    $('#newfolder').append(lg.new_folder);
	$('#itemOptions a[href$="#download"]').append(lg.download);
	$('#itemOptions a[href$="#rename"]').append(lg.rename);
	$('#itemOptions a[href$="#delete"]').append(lg.del);
}

// Provides support for adjustible columns.
$('#splitter').splitter({
	sizeLeft: 200
});

// cosmetic tweak for buttons
$('button').wrapInner('<span></span>');

// Provide initial values for upload form, status, etc.
setUploader(fileRoot);

$('#uploader').attr('action', fileConnector);

$('#uploader').ajaxForm({
	target: '#uploadresponse',
	beforeSubmit: function(arr, form, options) {
		var doUpload = function(){
			$('#upload').attr('disabled', true);
			$('#upload span').addClass('loading').text(lg.loading_data);
			if ($.urlParam('type').toString().toLowerCase() == 'images') {
				// Test if uploaded file extension is in valid image extensions
				var newfileSplitted = $('#newfile', form).val().toLowerCase().split('.');
				for (key in imagesExt) {
					if (imagesExt[key] == newfileSplitted[newfileSplitted.length-1]) {
						return true;
					}
				}
				showPrompt({title: lg.UPLOAD_IMAGES_ONLY});
				return false;
			}
		}
        if($("#fileselector li.selected").size() > 0){
        	showPrompt({
	        	title: lg.prompt_replacefile,
	        	buttons: ['Yes', 'No'],
	        	callback: function(button){
	        		if(button == 'Yes'){
	        			form.append('<input name="replacepath" value="' + $("#fileselector li.selected").attr('rel') + '" />');
	        		}
	        		doUpload();
	        	}
	       });
        }else{
        	doUpload();
        }
	},
	success: function(result){
        $('input[name="replacepath"]').remove();
		var data = jQuery.parseJSON($('#uploadresponse').find('textarea').text());
		
		if(data['Code'] == 0){
			addNode(data['Path'], data['Name']);
		} else {
			showPrompt({title: data['Error']});
		}
		$('#upload').removeAttr('disabled');
		$('#upload span').removeClass('loading').text(lg.upload);
		
		// clear data in browse input
        $("#newfile").replaceWith('<input id="newfile" type="file" name="newfile">');
	}
});

// Creates file tree.
$('#filetree').fileTree({
	root: fileRoot,
	datafunc: populateFileTree,
	multiFolder: false,
	folderCallback: function(path){
        getFolderInfo(path); 
    },
	after: function(data){
		$('#filetree').find('li a').each(function() {
			$(this).contextMenu(
				{ menu: getContextMenuOptions($(this)) },
				function(action, el, pos){
					var path = $(el).attr('rel');
					setMenus(action, path);
				}
			)
		});
	}
}, function(file){
    var relselector = 'li[rel="' + file + '"]';
    $("#fileselector li.selected,#aceeditors li.selected").removeClass('selected');
    if($('#fileselector ' + relselector).size() == 0){
        var tab = $('<li class="selected" rel="' + file + '">' + file + '</li>');
        var close = $('<a href="#close" class="closebtn"> x </a>');
        tab.click(function(){
            $("#fileselector li.selected,#aceeditors li.selected").removeClass('selected');
            $(this).addClass('selected');
            $("#aceeditors li[rel='" + $(this).attr('rel') + "']").addClass('selected');
            setSaveState();
        });
        close.click(function(){
            var tabel = $(this).parent()
            var remove_tab = function(){
                if(tabel.hasClass('selected')){
                    var other = tabel.siblings().eq(0);
                    other.addClass('selected');
                    $("#aceeditors li[rel='" + other.attr('rel') + "']").addClass('selected'); 
                }
                $("#aceeditors li[rel='" + tabel.attr('rel') + "']").remove();
                tabel.remove();
            }
            var dirty = $('#fileselector li.selected').hasClass('dirty');
            if(dirty){
            	showPrompt({
            		title: 'Unsaved Changes',
            		description: 'You have unsaved changes. Would you like to save first?',
            		buttons: ['Yes', 'No', 'Cancel'],
            		callback: function(button){
            			if(button == 'Yes'){
            				$("#save").trigger('click');
                            remove_tab();
            			}else if(button == 'No'){
            				remove_tab();
            			}
            		}
            	});
            }
            if(!dirty){
                remove_tab();
            }
            setSaveState();
            return false;
        })
        tab.append(close);
        $("#fileselector").append(tab);
        $.ajax({
            url: baseUrl + '/@@theming-controlpanel-filemanager-getfile',
            data: {path: file},
            dataType: 'json',
            success: function(data){
                var editorId = 'id' + Math.floor(Math.random()*999999);
                var li = $('<li class="selected" data-editorid="' + editorId + '" rel="' + file + '"></li>');
                if(data.contents !== undefined){
                    var extension = data.ext;
                    var container = '<pre id="' + editorId + '" name="' + file + '">' + data.contents + '</pre>';
                    li.append(container);
                    $("#aceeditors").append(li);
                    var editor = ace.edit(editorId);
                    editor.setTheme("ace/theme/textmate");
                    editor.getSession().setTabSize(4);
                    editor.getSession().setUseSoftTabs(true);
                    editor.getSession().setUseWrapMode(false);
                    var mode = defaultMode;
                    if (extension in extensionModes) {
                        mode = extensionModes[extension];
                    }
                    editor.getSession().setMode(mode);
                    editor.setShowPrintMargin(false);

                    editor.getSession().setValue(data.contents);
                    editor.navigateTo(0, 0);
                    EDITORS[file] = editor;
                    var markDirty = function(){
                        $("#fileselector li[rel='" + file + "']").addClass('dirty'); 
                        setSaveState();
                    }
                    editor.getSession().on('change', markDirty);
                }else{
                    li.append(data.info);
                    $("#aceeditors").append(li);
                }
            }
        })
    }
    $("#fileselector " + relselector + ",#aceeditors " + relselector).addClass('selected');
});

$("#save").live('click', function(){
    var li = $("#fileselector li.selected");
    var path = li.attr('rel');
    var editor = EDITORS[path];
    $.ajax({
        url: baseUrl + '/@@theming-controlpanel-filemanager-savefile',
        data: {path: path, value: editor.getSession().getValue()},
        type: 'POST',
        success: function(){
            $("#fileselector li[rel='" + path + "']").removeClass('dirty'); 
            setSaveState();
        }
    });
    return false;
});

$("#rootNode a").click(function(){
    $('#filetree>ul>li.expanded>a').trigger('click');
    getFolderInfo(fileRoot);
    return false;
})

// Disable select function if no window.opener
if(window.opener == null) $('#itemOptions a[href$="#select"]').remove();


window.onbeforeunload = function() {
	if($('#fileselector li.dirty').size() > 0){
		return "You have unsaved changes.";	
	}
};

});
})(jQuery);
