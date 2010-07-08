
// See http://www.mozilla.org/rhino/
// for info on builtin shell functions

nosejs = {};

(function(){
    
    var reporters = [];
    var scripts_loaded = {}; // key=<absolute script path>, val=<script that first loaded it>
    var current_script = null;
    
    var setHtmlLocation = function(html_file) {
        if (typeof window === 'undefined') {
            throw new Error(
                "Cannot load HTML file "+html_file+" because the DOM has not been initialized");
        }
        window.location = html_file;
        //print("set window.location="+html_file);
    };
    
    var patchDom = function() {
        // hmm, due to Java getters/setters the DOM is hard to patch :(
    }
    
    nosejs.resource_dir = null;
    
    nosejs.OSError = function(msg) {
        Error.call(this, msg);
        this.name = "OSError";
        this.message = msg;
    }
    
    nosejs.RuntimeError = function(msg) {
        Error.call(this, msg);
        this.name = "RuntimeError";
        this.message = msg;
    }
    
    nosejs.requireFile = function(path) {
        var filename;
        
        if (!path) {
            throw new nosejs.RuntimeError("path cannot be empty");
        }
        
        path = new java.io.File(path);
        
        if (path.toString().startsWith('/')) {
            filename = path;
        } else {            
            // assume it's relative to the script that's being executed.
            var root = new java.io.File(current_script).getParent();
            if (!root.endsWith('/')) {
                root = root + '/';
            }
            filename = new java.io.File(root + path);
        }        
        if (!filename.canRead()) {
            throw new nosejs.OSError("Could not read file: " + filename);
        }
        filename = new java.io.File(filename.getCanonicalPath()); // resolves `..' traversals
        filename = String(filename);
        
        if (scripts_loaded[filename]) {
            // already loaded it:
            return;
        }
        scripts_loaded[filename] = current_script;
        
        load(filename);
    };
    
    nosejs.requireResource = function(path) {
        nosejs.requireFile(new java.io.File(nosejs.resource_dir + '/' + path).getCanonicalPath());
    }
     
    nosejs.loadFiles = function(filelist) {
        var patched_dom = false;
        
        for (var i=0; i<filelist.length; i++) {
            var filename = filelist[i];
            if (filename.slice(-5).toLowerCase()==='.html') {
                // initialize DOM for the next JavaScript:
                setHtmlLocation(filename)
            } else {
                // load as JavaScript:
                // print("About to load "+filename);
                current_script = filename;
                load(filename);
            }
            
            if (!patched_dom) {
                // after env.js gets loaded, might need to make some adjustments
                if (typeof window !== 'undefined') {                    
                    patchDom();
                    patched_dom = true;
                }
            }
        }
    };
    
    nosejs.registerReporter = function(callback) {
        reporters.push(callback);
    }
    
    nosejs.report = function() {
        var passed = true;
        for (var i=0; i<reporters.length; i++) {
            report = reporters[i];
            var return_val = report();
            if (passed) {
                passed = return_val;
            }
        }
        return passed;
    }
})();
