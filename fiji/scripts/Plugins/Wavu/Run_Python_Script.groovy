// Plugins > Wavu > Run Python Script...
// Pick a script folder (one with a pixi.toml), fill in its parameters, run it
// in its own environment; logs stream to the Log window, Esc cancels.
// SPDX-License-Identifier: GPL-3.0-or-later
import ij.IJ
import ij.io.DirectoryChooser

// Load the shared Wavu library (lib/wavu_lib.groovy.txt; see docs/decisions.md D6).
// WAVU_LIB overrides the location (used by the tests, which run from a git checkout).
def wavuLibFile = System.getenv("WAVU_LIB") ? new File(System.getenv("WAVU_LIB")) :
        new File(ij.IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt")
def wavu = new GroovyShell(this.class.classLoader).evaluate(wavuLibFile)

try {
    // Offer the workers already running (started here, or connected to via
    // "Connect to Running Worker"), else ask for a script folder.
    List live = new ArrayList(wavu.workers().values()).findAll { wavu.alive(it) }
    Map w = null
    File dir = null
    if (!live.isEmpty()) {
        String other = "<choose another script folder...>"
        def pick = new ij.gui.GenericDialog("Wavu: run a Python script")
        pick.addChoice("Worker", ((live.collect { it.scriptDir }) + [other]) as String[], live[0].scriptDir as String)
        pick.showDialog()
        if (pick.wasCanceled()) return
        String c = pick.getNextChoice()
        if (c != other) { w = live.find { it.scriptDir == c }; dir = new File(c) }
    }
    if (w == null) {
        DirectoryChooser.setDefaultDirectory(ij.Prefs.get("wavu.lastDir", System.getProperty("user.home")))
        String chosen = new DirectoryChooser("Wavu: choose a script folder (contains pixi.toml)").getDirectory()
        if (chosen == null) return
        dir = new File(chosen).getCanonicalFile()
        ij.Prefs.set("wavu.lastDir", dir.getAbsolutePath())
        w = live.find { it.scriptDir == dir.getAbsolutePath() }
    }
    if (w == null) {
        if (!new File(dir, "pixi.toml").isFile()) {
            IJ.error("Wavu", dir.toString() + "\nhas no pixi.toml, so it is not a Wavu script folder.\n" +
                    "Start one from the template: pixi run new-script <name> (see the Wavu README).")
            return
        }
        w = wavu.startWorker(dir, false)
        if (w == null) return
    }

    Map listing = wavu.getOk(w, "/scripts")
    listing.errors.each { name, err -> wavu.log("could not load " + name + ".py: " + err) }
    List names = new ArrayList(listing.scripts.keySet())
    if (names.isEmpty()) { IJ.error("Wavu", "No runnable scripts in " + dir + " (see the Log for import errors)."); return }
    String script = names[0]
    if (names.size() > 1) {
        def gd = new ij.gui.GenericDialog("Wavu: choose a script")
        gd.addChoice("Script", names as String[], ij.Prefs.get("wavu.lastScript", names[0]))
        gd.showDialog()
        if (gd.wasCanceled()) return
        script = gd.getNextChoice()
        ij.Prefs.set("wavu.lastScript", script)
    }

    Map answers = wavu.askParams(script, listing.scripts[script], w.process != null && !w.debug)
    if (answers == null) return
    if (answers.debug) {
        wavu.stopWorker(w)
        wavu.log("Restarting the worker with debugpy. In VS Code: Run and Debug > 'Attach to Wavu worker'.")
        w = wavu.startWorker(dir, true)
        if (w == null) return
    }
    Map inputs = [:]
    ij.ImagePlus ref = null
    answers.images.each { name, imp ->
        inputs[name] = wavu.encodeImage(imp, w)
        if (ref == null) ref = imp
    }
    wavu.log("Running " + script + " " + answers.params)
    Map result = wavu.runJob(w, script, answers.params, inputs)
    if (result.status == "done") {
        wavu.openOutputs(w, result.outputs, ref, (ref != null ? ref.getShortTitle() + "-" : ""), true)
        wavu.log(script + " finished")
    } else if (result.status == "error") {
        IJ.error("Wavu", script + " failed:\n" + result.error.message + "\n\n(full traceback in the Log window)")
    }
} catch (InterruptedException e) {
    wavu.log(e.getMessage())
} catch (Exception e) {
    IJ.log("[Wavu] " + e)
    IJ.error("Wavu", e.getMessage() ?: e.toString())
}
