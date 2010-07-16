
// QUnit compatible test library for running headless in Rhino.
// See http://docs.jquery.com/QUnit

if (typeof nosejs === 'undefined') {
    nosejs = {}
}
nosejs.AssertionError = function(msg) {
    Error.call(this, msg);
    this.name = "AssertionError";
    this.message = "TEST FAILED: " + msg;
}
nosejs.AssertionError.prototype.toString = function() { return this.message; }

// this doesn't work since throwing a custom JavaScript object as an exception
// does not expose traceback info (or maybe I don't know how to get it).
nosejs.registerReporter(function() {
    for (var i=0; i<nosejs.test_registry.queued_exceptions.length; i++) {
        var exc_info = nosejs.test_registry.queued_exceptions[i];
        print("----------------------------------------------------------------------");
        print(exc_info.name);
        print("----------------------------------------------------------------------");
        // http://groups.google.com/group/mozilla.dev.tech.js-engine.rhino/
        // browse_thread/thread/3545664b2d747ae9?pli=1
        exc_info.exception.rhinoException.printStackTrace();
        print("----------------------------------------------------------------------");
    }
})

nosejs.test_registry = {
    queued_exceptions: [], // this is global to the entire test run
    assertions: 0,
    expectations: 0,
    
    reset: function() {
        this.assertions = 0;
        this.expectations = 0;
    }
}

equals = function(actual, expected, message) {
    nosejs.test_registry.assertions += 1;
    if (actual != expected) {
        throw new nosejs.AssertionError(expected + " != " + actual + " " + String(message));
    }
}

expect = function(assertions) {
    nosejs.test_registry.expectations = assertions;
}

ok = function(should_be_truthy, message) {
    nosejs.test_registry.assertions += 1;
    if (should_be_truthy) {
        // pass
    } else {
        throw new nosejs.AssertionError("Not OK " + String(message));
    }
}

// call on start of module test to prepend name to all tests
module = function(name, lifecycle) {
    print(name);
}

test = function(name, callback) {
    // try {
    nosejs.test_registry.reset();
    print("  "+name);
	callback();
	if (    nosejs.test_registry.expectations > 0 && 
	        nosejs.test_registry.expectations != nosejs.test_registry.assertions) {
	    throw new nosejs.AssertionError(
	        nosejs.test_registry.expectations + " assertion(s) expected, " +
	        nosejs.test_registry.assertion + " ran"
	    );
    }
    // } catch (exc) {
    //     nosejs.test_registry.queued_exceptions.push({name:name, exception:exc});
    // }
}
