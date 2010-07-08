

// bootstrap dillemma, first argument is the absolute path to __nosejs__.js runtime, 
// so load it:
load(arguments[0]);
nosejs.resource_dir = new java.io.File(arguments[0]).getParent(); // the dir of __nosejs__.js

var remaining_scripts = arguments.slice(1);
nosejs.loadFiles(remaining_scripts)
var passed = nosejs.report(); // fixme, return non-zero?
print("");
print("Loaded " + remaining_scripts.length + " JavaScript file" + (remaining_scripts.length==1 ? '': 's'));
