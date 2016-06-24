===============
ShipIt Frontend
===============

This is the new frontend for the ShipIt project, created and used by the Release Management team at Mozilla.


Commands
========

- ``npm run dev``

    Run development instance of application, on http://localhost:8080,
    via `webpack-dev-server`_, with hot reloading of code via
    `webpack hot module reload`_.

- ``npm run build``

    Build production ready static files into ``./build`` folder.

- ``npm run test``

    Run all the tests for the project one time.

    Coverage can be found in ``./coverage`` folder.

- ``npm run test:dev``

    Open browser, then run all tests, keep browser open and listen for code
    changes, then rerun the tests.

    Coverage can be found in ``./coverage`` folder.


Configuration
=============

This project does not use any of the *traditional* javascript building tools
(eg. `Gulp`_, `Grunt`_). It connects all with `webpack`_ and different webpack
loaders. Webpack is used here because it also provides nice development
environment (hot reload of code). Configuration for development, testing and
production can be found in ``./webpack.config.js``.

Webpack hooks and applies this `babel`_ transforms:
- `babel-preset-es2015`_
- `babel-preset-react`_
- `babel-preset-stage-0`_

Configuration for `eslint`_ configuration, which is used in webpack's build
chain is configured in ``./packages.json``, since this is the location eslint
linter looks.

For testing, test runner `karma`_ is used. It used webpack's configuration to
apply all babel transforms and runs tests in for different browsers.
Configuration for karma can be found in ``./karma.conf.js``

