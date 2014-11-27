GIT = git
NPM = npm
NPM_VERSION = $(shell npm -v)

GRUNT = ./node_modules/grunt-cli/bin/grunt
BOWER = ./node_modules/bower/bin/bower
NODE_PATH = ./node_modules

DEBUG =
ifeq ($(debug), true)
	DEBUG = --debug
endif
VERBOSE =
ifeq ($(verbose), true)
	VERBOSE = --verbose
endif


all: bundles

bundles: bundle-thememapperbundle

bundle-thememapperbundle:
	mkdir -p build
	NODE_PATH=$(NODE_PATH) $(GRUNT) bundle-thememapperbundle
	cp ./build/thememapperbundle.min.* ../src/plone/app/theming/browser/resources/

test:
	NODE_PATH=$(NODE_PATH) $(GRUNT) test $(DEBUG) $(VERBOSE) --pattern=$(pattern)

test-once:
	NODE_PATH=$(NODE_PATH) $(GRUNT) test_once $(DEBUG) $(VERBOSE) --pattern=$(pattern)

test-dev:
	NODE_PATH=$(NODE_PATH) $(GRUNT) test_dev $(DEBUG) $(VERBOSE) --pattern=$(pattern)

test-ci:
	NODE_PATH=$(NODE_PATH) $(GRUNT) test_ci $(DEBUG) $(VERBOSE)

.PHONY: bundles bundle-bundle-thememapperbundle test test-once test-dev test-ci
