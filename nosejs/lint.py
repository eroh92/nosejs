
import sys
import unittest
import subprocess
import logging

log = logging.getLogger('nose.plugins.nosejs')

class JsLintError(Exception):
    """JavaScript Lint Error"""
    
class JsLintWarning(Exception):
    """JavaScript Lint Warning"""

class JsLintTestCase(unittest.TestCase):
    """A test case that runs a file through the jsl lint executable."""
    __test__ = False # do not collect
    
    def __init__(self, filename, jsl_bin, jsl_options=None, stop_on_error=False):
        self.jsl_bin = jsl_bin
        self.jsl_options = jsl_options or []
        self.filename = filename
        self.stop_on_error = stop_on_error
        super(JsLintTestCase, self).__init__()
    
    def runTest(self):
        pass
    
    def run(self, result):
        cmd = [self.jsl_bin]
        cmd.extend(self.jsl_options)
        
        start = '=NJS=ST='
        sep = '=NJS=SEP='
        
        cmd.extend([
            '-output-format', (start + '__FILE__' + sep + '__LINE__' + sep + '__ERROR__'), 
            '-nologo', '-nosummary', '-nofilelisting',
            '-process', self.filename])
        log.debug("jsl command: %s" % " ".join(cmd))
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        output = p.stdout.read()        
        returncode = p.wait()
        try:
            if returncode != 0:
                # or use result.stream ?
                # sys.stdout.write(output)
                
                msgs = output.split(start)
                for msg in msgs:
                    if msg.strip() == '':
                        continue
                    try:
                        file, line, error = msg.split(sep)
                    except:
                        log.debug("Could not split %s using markers" % msg)
                        raise
                
                    # log.debug("Extracted file %s, line %s, error %s" % (file, line, error))
                    error = error.strip()
                    if error.startswith('lint warning:'):
                        etype = JsLintWarning
                    else:
                        etype = JsLintError
                    result.addError(self, (etype, "%s:%s %s" % (file, line, error), None))
                
                    if self.stop_on_error:
                        break
            else:
                result.addSuccess(self)
        finally:
            result.stopTest(self)
            
    def address(self):
        return (self.id(), None, None)
    
    def id(self):
        return repr(self)
    
    def shortDescription(self):
        return repr(self)
    
    def __repr__(self):
        return "javascript-lint: %s" % self.filename
        
    __str__ = __repr__
        