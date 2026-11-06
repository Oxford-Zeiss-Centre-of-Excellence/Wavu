// Plugins > Wavu > Run Script (Macro)
// The recordable, no-dialog way to run a Wavu script -- for ImageJ macros and
// batch workflows. Plugins > Macros > Record... captures it as, for example:
//
//   run("Run Script (Macro)", "folder=[D:/scripts/cellpose] script=script params=[diameter=30 use_gpu=false]");
//
// Every `image` parameter of the script gets the current image. Results open as
// windows named <image title>-<output name> (tables too), so the macro can
// selectWindow() them. The folder's worker starts once and is reused by later
// calls; Plugins > Wavu > Stop Worker ends it. Parameter values: name=value,
// separated by spaces (no spaces inside a value).
//
// Optional `tables` passes open tables as table inputs, input name = table title:
//
//   run("Run Script (Macro)", "folder=[D:/scripts/track] script=script tables=[detections=movie-detections]");
//
// (Results from a call without an image input are named just <output name>.)
// SPDX-License-Identifier: GPL-3.0-or-later
#@ File (label = "Script folder", style = "directory") folder
#@ String (label = "Script", value = "script") script
#@ String (label = "Parameters (name=value ...)", value = "", required = false, persist = false) params
#@ String (label = "Tables (input=table title ...)", value = "", required = false, persist = false) tables
import ij.IJ
import ij.measure.ResultsTable

// Load the shared Wavu library (lib/wavu_lib.groovy.txt; see docs/decisions.md D6).
// WAVU_LIB overrides the location (used by the tests, which run from a git checkout).
def wavuLibFile = System.getenv("WAVU_LIB") ? new File(System.getenv("WAVU_LIB")) :
        new File(ij.IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt")
def wavu = new GroovyShell(this.class.classLoader).evaluate(wavuLibFile)

try {
    File dir = folder.getCanonicalFile()
    Map w = wavu.workerFor(dir)
    if (w == null) throw new IOException("could not start a worker for " + dir)
    Map listing = wavu.getOk(w, "/scripts")
    Map schema = (Map) listing.scripts[script]
    if (schema == null)
        throw new IOException("no script '" + script + "' in " + dir + "; available: " + listing.scripts.keySet().join(", "))
    Map inputs = [:]
    // The current image: a visible window, or the macro's image in setBatchMode(true).
    ij.ImagePlus current = ij.WindowManager.getCurrentImage() ?: ij.macro.Interpreter.getLastBatchModeImage()
    ((Map) schema.params).each { String name, Map p ->
        if (p.type == "image") {
            if (current == null) throw new IOException(script + " needs an image: open one first")
            inputs[name] = current
        }
    }
    // Table inputs: input name -> the title of an open table (Results, Table.create, Wavu output).
    wavu.parseParams(tables).each { String name, String title ->
        ResultsTable rt = findTable(title)
        if (rt == null) throw new IOException("no open table named '" + title + "' (for input '" + name + "')")
        inputs[name] = rt
    }
    Map values = wavu.parseParams(params)
    wavu.log("Running " + script + " " + values)
    wavu.run(dir, script, values, inputs, true)
    wavu.log(script + " finished")
} catch (Exception e) {
    IJ.log("[Wavu] " + e)
    ij.macro.Interpreter.abort()  // stop the calling macro
    throw e
}

/** An open table by title: a table window, or a hidden table of a batch-mode macro. */
ResultsTable findTable(String title) {
    ResultsTable rt = ResultsTable.getResultsTable(title)
    if (rt == null) {
        def win = ij.WindowManager.getWindow(title)
        if (win instanceof ij.text.TextWindow) rt = ((ij.text.TextWindow) win).getResultsTable()
    }
    if (rt == null && title == "Results") rt = ResultsTable.getResultsTable()
    return rt
}
