/*
const fs = require('fs');
const config_type = process.argv.indexOf('start') !== -1 ? 'dev' : 'prod';
const config = require('mozilla-neo/config/webpack.' + config_type);
const webpack = require('mozilla-neo/node_modules/webpack');
const ExtractTextPlugin = require("extract-text-webpack-plugin");

// remove common chunk plugin since we serve all the code as one file
config.plugins = config.plugins.filter(function(plugin) {
  return !(plugin instanceof webpack.optimize.CommonsChunkPlugin);
});


// extract css into separate file (due to CSP)
const extractor = new ExtractTextPlugin({
  filename: "[name].css"
});
config.plugins.push(extractor);
config.module.loaders = config.module.loaders.map(function(loader) {
  if ("something.scss".match(loader.test)) {
    delete loader.loaders;
    loader.loaders = extractor.extract({
      fallback: "style-loader",
      use: ["css-loader", "sass-loader"],
    });
  }
  return loader;
});


// remove react-hot from loaders
config.module.loaders = config.module.loaders.filter(function(loader) {
  return !(loader['loaders'] && loader['loaders'].indexOf('react-hot') > -1);
});


// add elm loader
config.module.loaders.push({
  test: /\.elm$/,
  exclude: /(node_modules|elm-stuff)/,
  loader: 'elm-webpack'
});
config.module.noParse = /\.elm$/;


// in development environment use ssl
if (config_type === 'dev') {
  config.devServer.https = true;
  config.devServer.cacert = fs.readFileSync(process.env.SSL_CACERT);
  config.devServer.cert = fs.readFileSync(process.env.SSL_CERT);
  config.devServer.key= fs.readFileSync(process.env.SSL_KEY);
}

module.exports = config;
*/
