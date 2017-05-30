const HtmlWebpackPlugin = require('html-webpack-plugin');
const merge = require('webpack-merge');
const path = require('path');
const webpack = require('webpack');

const PlonePlugin = require('plonetheme-webpack-plugin');

const PATHS = {
  'patterns': path.join(
    __dirname, '..', 'extras', 'mockup', 'mockup', 'patterns')
};

const PLONE = new PlonePlugin({
  portalUrl: 'http://localhost:8080/Plone',
  publicPath: '',
  variables: {
    'mockup-patterns-thememapper': '\'' + path.relative(__dirname, path.join(
       PATHS.patterns, 'thememapper', 'pattern.thememapper.less')) + '\'',
    'mockup-patterns-filemanager': '\'' + path.relative(__dirname, path.join(
       PATHS.patterns, 'filemanager', 'pattern.filemanager.less')) + '\''
  }
});

const common = {
  entry: {
    thememapper: [
      path.join(__dirname, 'thememapper.js')
    ]
  },
  resolve: {
    alias: {
      'mockup-patterns-thememapper': path.join(
        PATHS.patterns, 'thememapper', 'pattern.js'),
      'mockup-patterns-thememapper-url': path.join(
        PATHS.patterns, 'thememapper')
    }
  }
};

switch(path.basename(process.argv[1])) {
  case 'webpack-dev-server':
    module.exports = merge(PLONE.development, common, {
      devServer: {
        proxy: {
          '/Plone': {
            target: 'http://localhost:8080/Plone',
            secure: false
          }
        }
      },
      plugins: [
        new HtmlWebpackPlugin({
          template: path.join(__dirname, 'thememapper.html')
        })
      ]
    });
    break;
}
