// Rule builder

var RuleBuilder = function(callback) {

    this.callback = callback;

    this.active = false;
    this.currentScope = null;

    this.ruleType = null;
    this.subtype = null;

    this._contentElement = null;
    this._themeElement = null;
};

RuleBuilder.prototype.select = function(element) {
        if(this.currentScope == "theme") {
            this._themeElement = element;
        } else if(this.currentScope == "content") {
            this._contentElement = element;
        }
    };

RuleBuilder.prototype.start = function(ruleType) {
        this._contentElement = null;
        this._themeElement = null;
        this.currentScope = "theme";

        // Drop rules get e.g. drop:content or drop:theme,
        // which predetermines the scope
        var ruleSplit = ruleType.split(':');
        if(ruleSplit.length >= 2) {
            this.ruleType = ruleSplit[0];
            this.subtype = ruleSplit[1];
            this.currentScope = this.subtype;
        } else{
            this.ruleType = ruleType;
            this.subtype = null;
        }

        this.active = true;

        this.callback(this);
    };

RuleBuilder.prototype.next = function() {

        if(this.subtype != null) {
            // Drop rules have only one scope
            this.currentScope = null;
        } else {
            // Other rules have content and theme
            if(this.currentScope == "theme") {
                this.currentScope = "content";
            } else if (this.currentScope == "content") {
                this.currentScope = null;
            }
        }

        this.callback(this);

    };

RuleBuilder.prototype.end = function() {
        this._contentElement = null;
        this._themeElement = null;
        this.currentScope = null;
        this.active = false;
        this.ruleType = null;
        this.subtype = null;

        this.callback(this);
    };

RuleBuilder.prototype.buildRule = function(contentChildren, themeChildren) {

        if(this.ruleType == null) {
            return "";
        }

        if(this.subtype != null) {

            if(this.subtype == 'content') {
                return "<" + this.ruleType + "\n    " +
                        this.calculateDiazoSelector(this._contentElement, 'content', contentChildren) +
                        "\n    />";
            } else if(this.subtype == 'theme') {
                return "<" + this.ruleType + "\n    " +
                        this.calculateDiazoSelector(this._themeElement, 'theme', themeChildren) +
                        "\n    />";
            }

        } else {
            return "<" + this.ruleType + "\n    " +
                        this.calculateDiazoSelector(this._themeElement, 'theme', themeChildren) + "\n    " +
                        this.calculateDiazoSelector(this._contentElement, 'content', contentChildren) +
                        "\n    />";
        }

        // Should never happen
        return "Error";
    };

RuleBuilder.prototype.calculateCSSSelector = function(element) {
        var selector = element.tagName.toLowerCase();

        if (element.id) {
            selector += "#" + element.id;
        } else {
            var classes = $(element).attr('class');
            if(classes != undefined) {
                var splitClasses = classes.split(/\s+/);
                for(var i = 0; i < splitClasses.length; ++i) {
                    if(splitClasses[i] != "" && !splitClasses[i].indexOf('_theming') == 0) {
                        selector += "." + splitClasses[i];
                        break;
                    }
                }
            }
        }

        return selector;
    };

RuleBuilder.prototype.calculateUniqueCSSSelector = function(element) {
        var paths = [];
        var path = null;

        var parents = $(element).parents();
        var ultimateParent = parents[parents.length - 1];

        while (element && element.nodeType == 1) {
            var selector = this.calculateCSSSelector(element);
            paths.splice(0, 0, selector);
            path = paths.join(" ");

            // The ultimateParent constraint is necessary since
            // this may be inside an iframe
            if($(path, ultimateParent).length == 1) {
                return path;
            }

            element = element.parentNode;
        }

        return null;
    };

RuleBuilder.prototype.calculateUniqueXPathExpression = function(element) {
        var pathElements = [];
        var parents = $(element).parents();

        function elementIndex(e) {
            var siblings = $(e).siblings(e.tagName.toLowerCase());
            if(siblings.length > 0) {
                return "[" + ($(e).index() + 1) + "]";
            } else {
                return "";
            }
        }

        var xpathString = "/" + element.tagName.toLowerCase();
        if(element.id) {
            return "/" + xpathString + "[@id='" + element.id + "']";
        } else {
            xpathString += elementIndex(element);
        }

        for(var i = 0; i < parents.length; ++i) {
            var p = parents[i];

            var pString = "/" + p.tagName.toLowerCase();

            if(p.id) {
                return "/" + pString + "[@id='" + p.id + "']" + xpathString;
            } else {
                xpathString = pString + elementIndex(p) + xpathString;
            }
        }

        return xpathString;
    };

RuleBuilder.prototype.calculateDiazoSelector = function(element, scope, children) {

        var selectorType = scope;
        if(children) {
            selectorType += "-children";
        }

        var cssSelector = this.calculateUniqueCSSSelector(element);
        if(cssSelector) {
            return "css:" + selectorType + "=\"" + cssSelector + "\"";
        } else {
            var xpathSelector = this.calculateUniqueXPathExpression(element);
            return selectorType + "=\"" + xpathSelector + "\"";
        }

    };

// Outline / highlight management

var FrameHighlighter = function(frame, scope, ruleBuilder, onselect, onsave) {
    this.frame = frame;
    this.scope = scope;
    this.ruleBuilder = ruleBuilder;
    this.onselect = onselect || null;
    this.onsave = onsave || null;
    this.enabled = true;
    this.saved = null;

    this.currentOutline = null;
    this.activeClass = '_theming-highlighted';
};

FrameHighlighter.prototype.bestSelector = function(element) {
        return this.ruleBuilder.calculateUniqueCSSSelector(element) ||
               this.ruleBuilder.calculateUniqueXPathExpression(element);
    };

FrameHighlighter.prototype.setOutline = function(element) {
        $(element).data('old-outline', $(element).css('outline'));
        $(element).data('old-cursor', $(element).css('cursor'));
        $(element).css('outline', 'solid red 1px');
        $(element).css('cursor', 'crosshair');

        $(element).addClass(this.activeClass);

        if(this.currentOutline != null) {
            this.clearOutline(this.currentOutline);
        }

        this.currentOutline = element;
    };

FrameHighlighter.prototype.clearOutline = function(element) {
        $(element).css('outline', $(element).data('old-outline'));
        $(element).css('cursor', $(element).data('old-cursor'));

        $(element).removeClass(this.activeClass);

        this.currentOutline = null;
    };

FrameHighlighter.prototype.save = function(element) {
        this.saved = element;
        if(this.onsave != null) {
            this.onsave(element, this.bestSelector(element));
        }
    };

FrameHighlighter.prototype.setupElements = function() {
        var highlighter = this;

        function save(element) {
            highlighter.setOutline(element);
            highlighter.save(element);
            if(highlighter.ruleBuilder.active && highlighter.ruleBuilder.currentScope == highlighter.scope) {
                highlighter.ruleBuilder.select(element);
                highlighter.ruleBuilder.next();
                highlighter.clearOutline();
            }
        }

        $(this.frame).contents().find("*").hover(
            function(event) {

                if(highlighter.enabled || highlighter.ruleBuilder.active) {
                    $(highlighter.frame).focus();
                    highlighter.setOutline(this);
                    event.stopPropagation();

                    if(highlighter.onselect != null) {
                        highlighter.onselect(this, highlighter.bestSelector(this));
                    }
                }
            },
            function(event) {
                if($(this).hasClass(highlighter.activeClass)) {
                    highlighter.clearOutline(this);
                    if(highlighter.onselect != null) {
                        highlighter.onselect(null, null);
                    }
                }
            }
        ).click(function (event) {
            if(highlighter.ruleBuilder.active && highlighter.ruleBuilder.currentScope == highlighter.scope) {
                event.stopPropagation();
                event.preventDefault();

                highlighter.save(this);

                highlighter.ruleBuilder.select(this);
                highlighter.ruleBuilder.next();

                highlighter.clearOutline();
                if(highlighter.onselect != null) {
                    highlighter.onselect(null, null);
                }

                return false;
            } else if(highlighter.enabled) {
                event.stopPropagation();
                event.preventDefault();

                save(this);

                return false;
            }

            return true;
        });

        $(this.frame).contents().keyup(function (event) {

            if(!highlighter.enabled)
                return true;

            // ESC -> Move selection to parent node
            if(event.keyCode == 27 && highlighter.currentOutline != null) {
                event.stopPropagation();
                event.preventDefault();

                var parent = highlighter.currentOutline.parentNode;
                if(parent != null && parent.tagName != undefined) {
                    highlighter.setOutline(parent);
                    if(highlighter.onselect != null) {
                        highlighter.onselect(parent, highlighter.bestSelector(parent));
                    }
                }
            }

            // Enter -> Equivalent to clicking on selected node
            if(event.keyCode == 13 && highlighter.currentOutline != null) {

                event.stopPropagation();
                event.preventDefault();

                save(highlighter.currentOutline);

                return false;
            }
        });
    };

// Link management

var LinkManager = function(frame, themeMode, base, prefix) {
    this.frame = frame;
    this.themeMode = themeMode;
    this.modifiedClass = "_theming-modified";
    this.base = base;
    this.prefix = prefix;
};

LinkManager.prototype.isInternal = function(url) {
        if (url.slice(0, this.base.length) == this.base) {
            return true;
        } else {
            return false;
        }
    };

LinkManager.prototype.setupLinks = function() {
        var manager = this;
        $(this.frame).contents().find("a").each(function() {
            var href = $(this).attr('href');

            if(!$(this).hasClass(manager.modifiedClass)) {
                $(this).addClass(manager.modifiedClass);
                if(manager.isInternal(href)) {
                    var path = href.slice(manager.base.length, href.length);
                    var newHref = manager.prefix + "/@@theming-controlpanel-mapper-getframe?path=" + encodeURIComponent(path) + "&amp;theme=" + manager.themeMode;
                    $(this).attr('href', newHref);
                } else {
                    $(this).click(function(event) {
                        event.preventDefault();
                        alert("External links are disabled in the theme editor");
                        return false;
                    });
                }
            }
        });
    };

LinkManager.prototype.setupForms = function() {
        var manager = this;
        $(this.frame).contents().find("form").each(function() {
            if(!$(this).hasClass(manager.modifiedClass)) {
                $(this).addClass(manager.modifiedClass);
                $(this).submit(function(event) {
                    event.preventDefault();
                    alert("Form submissions are disabled in theme editor");
                    return false;
                });
            }
        });
    };

