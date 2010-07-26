# NoseJS
> Version 0.9.5 (unreleased)

# What

NoseJS is a [Nose](http://www.somethingaboutorange.com/mrl/projects/nose/)
plugin for integrating JavaScript tests into a Python test suite.

This projected has been forked from
[NoseJS on BitBucket](http://bitbucket.org/kumar303/nosejs).

# Overview

NoseJS is designed for Python projects that require JavaScript code for some
Web functionality. It currently has two features:

- Discover and run JavaScript tests alongside Python tests
- Validate JavaScript syntax (check for lint).

# Install

There are some optional external dependencies in the sections below.

#Checking JavaScript Syntax

NoseJS will find JavaScript files (e.g. ``app.js``) along the Nose path and run them through the `jsl`_ command line tool to check for "lint."  In other words, show you syntax errors, warnings, etc.  You can install jsl on most systems using your package manager (i.e. ``port install javascript-lint`` on Mac OS X) otherwise it is available for download on the `jsl`_ site.  

.. _jsl: http://www.javascriptlint.com/

## Usage

To check for lint without running any JavaScript unit tests, type::
    
    $ nosetests --with-javascript --no-javascript-tests path/to/javascript

To disable lint checking, add ``--no-javascript-lint``

# Running JavaScript Tests

NoseJS will also find and run JavaScript test files, those that match Nose's test pattern and end in ``.js``.  Currently, NoseJS supports running executing tests in [Rhino](http://www.mozilla.org/rhino/), a Java implementation of the JavaScript language.

## Usage

Assuming you've downloaded [Rhino](http://www.mozilla.org/rhino/) into `~/src`, discover and run JavaScript tests with this command::
    
    $ nosetests --with-javascript --rhino-jar ~/src/rhino1_7R1/js.jar path/to/javascript/tests

This command would look for any files along Nose's path ending in .js that match Nose's current test pattern, collect them all, then execute them using Rhino in a single Java subprocess at the end of all other tests.  By default, files looking like ``test*.js`` will be collected and run.

The idea behind NoseJS is that you might have a Python web application that relies on JavaScript for some of its functionality and you want to run both Python and JavaScript tests with one command, [nosetests] (http://www.somethingaboutorange.com/mrl/projects/nose/).  You can put these JavaScript tests wherever you want in your project.

Here is a more realistic example that shows how the `Fudge <http://farmdev.com/projects/fudge/>`_ project is tested simultaneously for Python and JavaScript functionality.  Its project layout looks roughly like this::

    |-- fudge
    |   |-- __init__.py
    |   |-- patcher.py
    |   |-- tests
    |   |   |-- __init__.py
    |   |   |-- test_fudge.py
    |   |   |-- test_patcher.py
    |-- javascript
    |   |-- fudge
    |   |   |-- fudge.js
    |   |   |-- tests
    |   |   |   |-- test_fudge.html
    |   |   |   `-- test_fudge.js
    `-- setup.py

Both Python and JavaScript tests can be run with this command::
    
    $ nosetests  --with-javascript \
                 --rhino-jar ~/src/rhino1_7R1/js.jar \
                 --with-dom \
                 --javascript-dir javascript/fudge/tests/
    ......................................................
    ----------------------------------------------------------------------
    Test Fake
      can find objects
      can create objects
      expected call not called
      call intercepted
      returns value
      returns fake
    Test ExpectedCall
      ExpectedCall properties
      call is logged
    Test fudge.registry
      expected call not called
      start resets calls
      stop resets calls
      global stop
      global clear expectations

    Loaded 6 JavaScript files

    OK
    ----------------------------------------------------------------------
    Ran 54 tests in 0.392s

    OK
    
The dots are the Python tests that were run and the output below that is what Fudge's JavaScript test files printed out.  Be sure to read the Caveats section below ;)

## Specifying a path to JavaScript files

If JavaScript files are nested in a subdirectory, like the above example, specify that directory with::
    
    $ nosetests --with-javascript --javascript-dir javascript/fudge/tests/ --javascript-dir ./another/dir

## nosejs JavaScript namespace

All JavaScripts have the ``nosejs`` JavaScript namespace available for use.  The following methods are available:

- **nosejs.requireFile(path)**
  
  - Load a JavaScript file from your test script.  If you require the same file multiple times, it will only 
    be loaded once.  If the file does not start with a slash, then it should be a path relative to the directory 
    of the script where requireFile() was called from.  For example, here is how test_fudge.js requires the 
    fudge library before testing::
        
        if (typeof nosejs !== 'undefined') {
            nosejs.requireFile("../fudge.js");
        }

- **nosejs.requireResource(name)**
  
  - Require a JavaScript file that is bundled with NoseJS.  There are a few available resources:
    
    - jquery-1.4.2.js
      - Will load the [jQuery](http://jquery.com/) library before loading any other tests

    - jquery/qunit-testrunner.js
      - Will load a very minimal set of JavaScript functions for testing.  It is a partial implementation of the [QUnit test runner](http://docs.jquery.com/QUnit) interface.  
      - Supported methods: `module()`, `test()`, `equals()`, `ok()`, and `expect()`
    
    - For example, test_fudge.js uses jquery and the testrunner ::
    
            if (typeof nosejs !== 'undefined') {
                nosejs.requireResource("jquery-1.3.1.js");
                nosejs.requireResource("jquery/qunit-testrunner.js");
                nosejs.requireFile("../fudge.js");
            }

## Using the DOM

If your JavaScript under test relies on a browser-like DOM environment, it might still work!  Just run::
    
    $ nosetests --with-javascript --with-dom

This will load a copy of [env.js](http://github.com/thatcher/env-js) to simulate a DOM before loading any other JavaScript.

## Wait ... Python *and* Java?

[Rhino](http://www.mozilla.org/rhino/) is pretty much the only stable, command line oriented implementation of JavaScript I know of and it's well supported by Mozilla.  

# Changelog

## New changes

- 0.9.5

  - Upgraded [env.js](http://github.com/thatcher/env-js) to latest from @thatcher's fork
  - Nuked Spidermonkey implementation for now
  - Nose now sees each js test file as a python test case
  - Failures and errors are now detected and displayed in the summary report

## Prior changes

- 0.9.4
 
  - Multiple paths for the --javascript-dir option can now be specified on multiple lines in setup.cfg
  
- 0.9.3
  
  - Added --with-javascript-only option to stop execution of any other Nose tests when needed.
  
- 0.9.2
  
  - **CHANGED**: The --js-test-dir option is now known as --javascript-dir
  - Added experimental support for python-spidermonkey
  - Added JavaScript lint check using the jsl tool
  - Fixed bugs in how custom paths to JavaScript were expanded
  
- 0.9.1
  
  - Fixed distribution problem
  
- 0.9
  
  - Initial release

# To Do

- Add spidermonkey support
- Distribute a Rhino js.jar with NoseJS
- Simplify command line inputs
