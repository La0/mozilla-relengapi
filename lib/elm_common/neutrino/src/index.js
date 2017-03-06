'use strict';

const path = require('path');
const fs = require('fs');
const webpack = require('webpack');
const HtmlPlugin = require('html-webpack-plugin');
const htmlTemplate = require('html-webpack-template');
const merge = require('deepmerge');

const CWD = process.cwd();
const SRC = path.join(CWD, 'src');
const BUILD = path.join(CWD, 'build');
const TEST = path.join(CWD, 'test');
const PKG = require(path.join(CWD, 'package.json'));
const FILE_LOADER = require.resolve('file-loader');
const CSS_LOADER = require.resolve('css-loader');
const STYLE_LOADER = require.resolve('style-loader');
const URL_LOADER = require.resolve('url-loader');
const PROJECT_MODULES = path.join(CWD, 'node_modules');

module.exports = ({ config }) => {
  config
    .target('web')
    .context(CWD)
    .entry('index')
      .add(path.join(SRC, 'index.js'))
      .end()
    .output
      .path(BUILD)
      .publicPath('./')
      .filename('[name].bundle.js')
      .chunkFilename('[id].[chunkhash].js')
      .end()
    .resolve
      .modules
        .add(PROJECT_MODULES)
        .end()
      .extensions
        .add('.js')
        .add('json')
        .add('elm')
        .end()
      .end()
    .resolveLoader
      .modules
        .add(PROJECT_MODULES)
        .end();
  config.node
    .set('console', false)
    .set('global', true)
    .set('process', true)
    .set('Buffer', true)
    .set('__filename', 'mock')
    .set('__dirname', 'mock')
    .set('setImmediate', true)
    .set('fs', 'empty')
    .set('tls', 'empty');

  config.module
    .rule('html')
    .test(/\.html$/)
    .loader('file', FILE_LOADER, {
      name: '[name].[ext]'
    });

  config.module
    .rule('css')
    .test(/\.css$/)
    .loader('style', STYLE_LOADER)
    .loader('css', CSS_LOADER);
// TODO: extract web plugin !!

  config.module
    .rule('woff')
    .test(/\.(woff|woff2)(\?v=\d+\.\d+\.\d+)?$/)
    .loader('url', URL_LOADER, {
      limit: '10000',
      mimetype: 'application/font-woff'
    });

  config.module
    .rule('ttf')
    .test(/\.ttf(\?v=\d+\.\d+\.\d+)?$/)
    .loader('url', URL_LOADER, {
      limit: '10000',
      mimetype: 'application/octet-stream'
    });

  config.module
    .rule('eot')
    .test(/\.eot(\?v=\d+\.\d+\.\d+)?$/)
    .loader('file', FILE_LOADER);

  config.module
    .rule('svg')
    .test(/\.svg(\?v=\d+\.\d+\.\d+)?$/)
    .loader('url', URL_LOADER, {
      limit: '10000',
      mimetype: 'application/svg+xml'
    });

  config.module
    .rule('img')
    .test(/\.(png|jpg)$/)
    .loader('url', URL_LOADER, {
      limit: 8192
    });

  config.module
    .rule('ico')
    .test(/\.ico(\?v=\d+\.\d+\.\d+)?$/)
    .loader('url', URL_LOADER);

//TODO: elm compilation
/*
  config.module
    .rule('compile')
      .test(/\.elm$/)
      .include(SRC, TEST)
      .loader('elm-webpack', require.resolve('elm-webpack') );
*/

  config
    .plugin('html')
    .use(HtmlPlugin, merge({
      inject: false,
      template: htmlTemplate,
      appMountId: 'root',
      xhtml: true,
      mobile: true,
      minify: {
        useShortDoctype: true,
        keepClosingSlash: true,
        collapseWhitespace: true,
        preserveLineBreaks: true,
      }
    }, PKG.config && PKG.config.html ? PKG.config.html : {}));

  if (process.env.NODE_ENV === 'development') {
    const host = 'localhost';
    const port = parseInt(process.env.PORT) ||
      PKG.config && PKG.config.neutrino && PKG.config.neutrino.devServer && parseInt(PKG.config.neutrino.devServer.port) ||
      5000;

    config.devtool('eval');
    config.devServer
      .host(host)
      .port(port)
      .https(true)
      .cacert(fs.readFileSync(process.env.SSL_CACERT))
      .cert(fs.readFileSync(process.env.SSL_CERT))
      .key(fs.readFileSync(process.env.SSL_KEY))
      .contentBase(SRC)
      .historyApiFallback(true)
      .hot(true)
      .stats({
        assets: false,
        children: false,
        chunks: false,
        colors: true,
        errors: true,
        errorDetails: true,
        hash: false,
        modules: false,
        publicPath: false,
        timings: false,
        version: false,
        warnings: true
      });

    config
      .entry('index')
        .add(`webpack-dev-server/client?https://${host}:${port}/`)
        .add('webpack/hot/dev-server');

    config
      .plugin('hot')
      .use(webpack.HotModuleReplacementPlugin);
  } else {
    config.output.filename('[name].[chunkhash].bundle.js');

  }

};
