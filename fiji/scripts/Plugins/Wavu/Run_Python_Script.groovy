// Plugins > Wavu > Run Python Script...
// Pick a running worker, an installed script (<Fiji>/wavu/scripts/*) or any
// script folder (one with a pixi.toml), fill in its parameters, run it in its
// own environment; logs stream to the Log window, Esc cancels.
// SPDX-License-Identifier: GPL-3.0-or-later
import ij.IJ
import ij.io.DirectoryChooser

// Load the shared Wavu library (lib/wavu_lib.groovy.txt; see docs/decisions.md D6).
// WAVU_LIB overrides the location (used by the tests, which run from a git checkout).
def wavuLibFile = System.getenv("WAVU_LIB") ? new File(System.getenv("WAVU_LIB")) :
        new File(ij.IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt")
def wavu = new GroovyShell(this.class.classLoader).evaluate(wavuLibFile)

try {
    // Choices: live workers (started here or connected), then installed scripts.
    Map choices = new LinkedHashMap()   // label -> [worker: Map] or [dir: File]
    new ArrayList(wavu.workers().values()).findAll { wavu.alive(it) }.each {
        choices["running: " + it.scriptDir] = [worker: it, dir: new File((String) it.scriptDir)]
    }
    wavu.installedScriptFolders().each { File d ->
        if (!choices.values().any { it.dir?.getCanonicalPath() == d.getCanonicalPath() })
            choices["installed: " + d.getName()] = [dir: d]
    }
    String other = "<choose a script folder...>"
    Map picked = null
    if (!choices.isEmpty()) {
        def pick = new ij.gui.GenericDialog("Wavu: run a Python script")
        List labels = new ArrayList(choices.keySet()) + [other]
        pick.addChoice("Script folder", labels as String[], (String) labels[0])
        pick.showDialog()
        if (pick.wasCanceled()) return
        picked = choices[pick.getNextChoice()]
    }
    if (picked == null) {
        DirectoryChooser.setDefaultDirectory(ij.Prefs.get("wavu.lastDir", System.getProperty("user.home")))
        String chosen = new DirectoryChooser("Wavu: choose a script folder (contains pixi.toml)").getDirectory()
        if (chosen == null) return
        File d = new File(chosen).getCanonicalFile()
        ij.Prefs.set("wavu.lastDir", d.getAbsolutePath())
        picked = [dir: d]
    }
    Map w = picked.worker ?: wavu.workerFor((File) picked.dir)
    if (w != null) wavu.runWithDialog(w, (File) picked.dir)
} catch (InterruptedException e) {
    wavu.log(e.getMessage())
} catch (Exception e) {
    IJ.log("[Wavu] " + e)
    IJ.error("Wavu", e.getMessage() ?: e.toString())
}
