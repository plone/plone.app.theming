export PATH := $(PATH):node_modules/.bin

all: clean watch

clean:
	rm -rf node_modules .plone

watch: node_modules
	npm run watch

###

node_modules: package.json
	yarn install
	touch node_modules

