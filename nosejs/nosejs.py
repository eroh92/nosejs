
import os
import sys
import subprocess
from nose.plugins.base import Plugin
from nose.config import ConfigError
import logging
import java
from lint import JsLintTestCase

log = logging.getLogger('nose.plugins.nosejs')

resource_dir = os.path.join(os.path.dirname(__file__), 'resources')

def get_resource(filename):
    return os.path.join(resource_dir, filename)

class JavaScriptTester(object):
    
    def __init__(self, stream, config):
        self.stream = stream
        self.config = config
    
    def load_files(self, files):
        raise NotImplementedError("runs each listed JavaScript file")

class RhinoJavaScriptTester(JavaScriptTester):
    
    def __init__(self, stream, config):
        super(RhinoJavaScriptTester, self).__init__(stream, config)
        
        cmd = [config.java_bin, '-jar', config.rhino_jar, '-opt', '-1']
        if config.rhino_jar_debug:
            cmd.append('-debug')
        
        self.base_cmd = cmd
    
    def load_files(self, files):
        cmd = [c for c in self.base_cmd]
        cmd.extend(files)

        log.debug("command to run is: \n  %s\n" % "\n    ".join(cmd))
        p = subprocess.Popen(
            cmd, env={'PATH':os.environ.get('PATH',None)},
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=self.config.nosejs_work_dir
        )
        self.stream.write(p.stdout.read())
        returncode = p.wait()
        print >> self.stream, ""
        if returncode != 0:
            # fixme: need to tell nose to exit non-zero
            print >> self.stream, "FAIL"
        else:
            print >> self.stream, "OK"

class RhinoContext(object):
    """creates top level methods in spidermonkey compatible with Rhino shell.
    
    See http://www.mozilla.org/rhino/
    """
    
    def __init__(self, stream=sys.stdout):
        from spidermonkey import Runtime
        rt = Runtime()
        self.ctx = rt.new_context()
        self.stream = stream
        self.ctx.bind_callable("help", self.help)
        self.ctx.bind_callable("defineClass", self.defineClass)
        self.ctx.bind_callable("deserialize", self.deserialize)
        self.ctx.bind_callable("load", self.load)
        self.ctx.bind_callable("loadClass", self.loadClass)
        self.ctx.bind_callable("load", self.load)
        self.ctx.bind_callable("print", self.print_)
        self.ctx.bind_callable("readFile", self.readFile)
        self.ctx.bind_callable("readUrl", self.readUrl)
        self.ctx.bind_callable("runCommand", self.runCommand)
        
        # this is for java.io.File() to work (see __nosejs__.js)
        self.ctx.bind_class(java._SM_JavaFile, bind_constructor=True)
    
    def help(self):
        raise NotImplementedError()
    
    def defineClass(self, class_name):
        raise NotImplementedError()
    
    def deserialize(self, filename):
        raise NotImplementedError()
    
    def load(self, *files):
        raise NotImplementedError()
        
    def loadClass(self, class_name):
        raise NotImplementedError()
        
    def load(self, *files):
        for file in files:
            log.debug("Spidermonkey is going to read and eval %s" % file)
            f = open(file,'r')
            # fixme: optimize with mmap and a regex for `;'
            self.ctx.eval_script(f.read())
            f.close()
    
    def print_(self, *messages):
        for msg in messages:
            # fixme: add spaces between multiple messages?
            if isinstance(msg, unicode):
                msg = msg.encode('utf-8')
            self.stream.write(msg)
        self.stream.write("\n")
        
    def readFile(self, file, encoding='utf-8'):
        raise NotImplementedError()
        
    def readUrl(self, url, encoding='utf-8'):
        raise NotImplementedError()
        
    def runCommand(self, cmd_name, *args_options):
        raise NotImplementedError()

class SpidermonkeyJavaScriptTester(JavaScriptTester):
    
    def __init__(self, stream, config):
        super(SpidermonkeyJavaScriptTester, self).__init__(stream, config)
        self.rhino = RhinoContext(stream=stream)
    
    def load_files(self, files):
        """run a command line JavaScript program.
        
        This should behave just like the Rhino counterpart, 
        which is pretty much:
        
        java -jar Rhino/js.jar main.js file1.js file2.js ...
        
        In other words, the first file we get is main.js and 
        each subsequent file will be loaded by main.js
        """
        if len(files) < 2:
            raise ValueError(
                "files %s should contain at least a main program (i.e. main.js) "
                "and one other JavaScript to execite")
        class main:
            arguments = files[1:]
        m = main()
        # set arguments like how Rhino does:
        self.rhino.ctx.bind_attribute("arguments", m, "arguments")
        # execute the first script as if it is a command line program:
        self.rhino.load(files[0])

class NoseJS(Plugin):
    """Finds JavaScript files to run tests and check for lint."""
    name = 'javascript'
    
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)
        parser.add_option('--with-javascript-only', dest="javascript_only", 
                            action="store_true", help=(
            "Activates the NoseJS plugin and prevents Nose from running any other tests.  "
            "Implies --with-javascript."
        ))
        parser.add_option('--no-javascript-tests', dest="run_javascript_tests", 
                            default=True, action="store_false", help=(
            "Disables default behavior of looking for JavaScript test files and "
            "loading them if they match nose's testMatch (i.e. [tT]est.*\.js)"
        ))
        parser.add_option('--no-javascript-lint', dest="run_javascript_lint", 
                            default=True, action="store_false", help=(
            "Disables default behavior of looking for JavaScript files and running them "
            "through the jsl command line tool to report lint errors and warnings."
        ))
        parser.add_option('--jsl-bin', default="jsl", help=(
            "Path to jsl executable.  Default: %default (using $PATH)"
        ))
        parser.add_option('--jsl-opt', default=[], action="append", help=(
            "Additional command line options to send to the jsl executable.  "
            "You can specify this multiple times."
        ))
        parser.add_option('--java-bin', default="java", help=(
            "Path to java executable.  Default: %default (using $PATH)"
        ))
        parser.add_option('--rhino-jar', help=(
            "Path to rhino1_7R1/js.jar (or later release). Download from http://www.mozilla.org/rhino/"
        ))
        parser.add_option('--rhino-jar-no-debug', dest='rhino_jar_debug', 
            action='store_false', default=True, help=(
            "Do not pass the -debug flag to js.jar.  By default -debug is passed because "
            "it shows tracebacks."
        ))
        parser.add_option('--spidermonkey', action='store_true', help=(
            "Run tests using the spidermonkey module from Python "
            "(this trumps --java-bin, --rhino-jar, and --rhino-no-debug) "
        ))
        parser.add_option('--with-dom', action="store_true", help=(
            "Simulate the DOM by loading John Resig's env.js "
            "before any other JavaScript files."
        ))
        parser.add_option('--load-js-lib', dest='javascript_libs_to_load', 
            action='append', metavar='JS_FILEPATH', default=[], help=(
            "Path to a JavaScript file that should be loaded before the tests. "
            "This option can be specified multiple times."
        ))
        parser.add_option('--javascript-dir', dest='javascript_dirs', 
            action='append', metavar='JS_DIRECTORY', default=[], help=(
            "Path to where JavaScript tests live.  Must be a subdirectory of where "
            "Nose is already looking for tests (i.e. os.getcwd()).  "
            "This option can be specified multiple times."
        ))
        possible_res = []
        os.walk(resource_dir)
        for root, dirs, files in os.walk(resource_dir):
            for name in files:
                if name[0] in ('.','_'):
                    continue
                if name.find('README') != -1:
                    continue
                abspath = os.path.join(root, name)
                possible_res.append(abspath.replace(resource_dir+"/", ""))
            
        parser.add_option('--load-js-resource', dest='resources_to_load', 
            action='append', metavar='RELATIVE_FILEPATH', help=(
            "Relative path to internal nosejs resource file that should be loaded before tests "
            "(but after DOM initialization).  This option can be specified multiple times.  "
            "Possible values: %s" % ", ".join(possible_res)
        ))
        runner = get_resource('rhino-testrunner.js')
        if not os.path.exists(runner):
            runner = None
        parser.add_option('--rhino-testrunner', metavar="RHINO_TESTRUNNER", default=runner, help=(
            "JavaScript that runs tests in Rhino.  When test files are discovered they will be "
            "executed as java -jar rhino1_7R1/js.jar RHINO_TESTRUNNER <discovered_test_file>.  "
            "Default: %default"
        ))
        parser.add_option('--nosejs-work-dir', help=(
            "A path to change into before running any commands"
        ))

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        if options.javascript_only:
            # --with-javascript-only implies --with-javascript
            self.enabled = True
        if not self.enabled:
            return
            
        self.files = [] # used by self.wantFile()
        
        if options.run_javascript_tests:
            self._configureJsTesters(options, config)
        if options.run_javascript_lint:
            self._configureJsLint(options, config)
            
        self.javascript_dirs = set([])
        
        root = os.getcwd()
        
        # convert a multiline value from setup.cfg:
        if len(options.javascript_dirs)==1 and "\n" in options.javascript_dirs[0]:
            # e.g. ['\napp/public/javascript/cmp/\napp/public/javascript/cmp/widgets']
            options.javascript_dirs = options.javascript_dirs[0].strip().split("\n")
            
        for dir in options.javascript_dirs:
            absdir = os.path.abspath(dir)
            # fixme: look for non working dir nose starting points?
            if not absdir.startswith(root):
                raise ValueError(
                    "Option --javascript-dir=%s must be somewhere along the working directory "
                    "path (currently %s)" % (absdir, root))
            absdir = absdir.replace(root, '')
            parts = absdir.split(os.sep)
            for i in range(len(parts)+1):
                incremental_part = os.sep.join(parts[0:i])
                if incremental_part:
                    if incremental_part.startswith(os.sep):
                        incremental_part = incremental_part[len(os.sep):]
                    self.javascript_dirs.add(os.path.join(root, incremental_part))
        log.debug("Exploded --javascript-dir(s): %s" % self.javascript_dirs)
        
        self.options = options
        self.config = config
    
    def _configureJsLint(self, options, config):
        found_jsl = False
        for prefix in os.environ.get('PATH','').split(':'):
            exe = os.path.join(prefix, options.jsl_bin)
            if os.path.exists(exe):
                found_jsl = True
                options.jsl_bin = exe
                break
        if not found_jsl:
            raise ConfigError(
                "Could not find jsl binary for JavaScript lint ($PATH=%r).  "
                "Try setting an explicit path with --jsl-bin or else disable lint with "
                "--no-javascript-lint" % (os.environ.get('PATH','')))
    
    def _configureJsTesters(self, options, config):
        wd = options.nosejs_work_dir
        if not wd:
            wd = os.getcwd()
            
        if not options.spidermonkey: 
            if not options.rhino_jar:
                raise ConfigError("--rhino-jar (path to js.jar) must be specified")
            if not os.path.exists(os.path.join(wd, options.rhino_jar)):
                raise ConfigError("Rhino js.jar does not exist: %s" % options.rhino_jar)
        if not options.rhino_testrunner:
            raise ConfigError("--rhino-testrunner (JavaScript test runner) must be specified")
        if not os.path.exists(os.path.join(wd, options.rhino_testrunner)):
            raise ConfigError("%s: file does not exist" % options.rhino_testrunner)
        
        libs = [get_resource('__nosejs__.js')] # load the runtime first
        if options.with_dom:
            libs.append(get_resource('env.js'))
            # load this HTML file so that the DOM gets activated:
            libs.append(get_resource('__nosejs__.html'))
        if options.resources_to_load:
            for resource in options.resources_to_load:
                libs.append(get_resource(resource))
        libs.extend(options.javascript_libs_to_load)
        options.javascript_libs_to_load = libs
        
        # explode --javascript-dir values into incremental paths
        # that can be used by wantDirectory() to descend into the 
        # actual path.  
        #
        # I.E. --javascript-dir=/path/to/somewhere/else/ becomes:
        #   /path/
        #   /path/to/
        #   /path/to/somewhere/
        #   /path/to/somewhere/else/
        
    
    def loadTestsFromFile(self, filename):
        """yield all test cases in a file or if there are none, yield False."""
        log.debug("nosejs is loading tests from: %s" % filename)
        
        if not self.options.run_javascript_lint:
            yield False
            return
        else:
            yield JsLintTestCase(filename, self.options.jsl_bin, 
                                    jsl_options=self.options.jsl_opt,
                                    stop_on_error=self.config.stopOnError)
    
    def wantDirectory(self, dirpath):
        want_dir = dirpath in self.javascript_dirs
        log.debug("Want directory: %s ? %s" % (dirpath, want_dir))
        if want_dir:
            return True
        elif self.options.javascript_only:
            # prevent Nose from running any other tests
            return False
        else:
            # allow Nose to continue through plugin chain as normal    
            return None
    
    def wantFile(self, file):
        found_some = None
        # fixme: provide custom file extensions?
        if file.endswith('.js'):
            found_some = True
            # fixme: provide custom test matches?
            if self.conf.testMatch.search(os.path.basename(file)):
                # just store it, don't return True
                log.debug("Storing file: %s" % file)
                self.files.append(file)
        
        if self.options.javascript_only:
            # prevent any other tests in Nose from running.
            if found_some is None:
                return False
                
        return found_some
        
    def report(self, stream):
        
        if self.options.run_javascript_tests:
            print >> stream, "----------------------------------------------------------------------"
        
            if self.options.spidermonkey:
                js_test = SpidermonkeyJavaScriptTester(stream, self.options)
            else:
                js_test = RhinoJavaScriptTester(stream, self.options)
            
            files = [self.options.rhino_testrunner] # the main program
            for js_lib in self.options.javascript_libs_to_load:
                files.append(js_lib)
            files.extend(self.files)
            js_test.load_files(files)
            