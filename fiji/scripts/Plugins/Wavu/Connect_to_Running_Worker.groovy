// Plugins > Wavu > Connect to Running Worker
// Launch modes 2 and 3: attach to a worker you started yourself
// (`pixi run worker` in a terminal, or the container) via its handshake file.
// SPDX-License-Identifier: GPL-3.0-or-later
import ij.IJ
import ij.Prefs

// Load the shared Wavu library (lib/wavu_lib.groovy.txt; see docs/decisions.md D6).
// WAVU_LIB overrides the location (used by the tests, which run from a git checkout).
def wavuLibFile = System.getenv("WAVU_LIB") ? new File(System.getenv("WAVU_LIB")) :
        new File(ij.IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt")
def wavu = new GroovyShell(this.class.classLoader).evaluate(wavuLibFile)

def gd = new ij.gui.GenericDialog("Wavu: connect to a running worker")
gd.addFileField("Handshake file", Prefs.get("wavu.handshake", new File(System.getProperty("user.home"), ".wavu/worker.json").getPath()))
gd.addMessage("Container only -- how the worker sees your data folder:")
gd.addStringField("Host data folder", Prefs.get("wavu.hostPrefix", ""), 30)
gd.addStringField("Same folder inside the container", Prefs.get("wavu.workerPrefix", ""), 30)
gd.showDialog()
if (gd.wasCanceled()) return
String hs = gd.getNextString(), hp = gd.getNextString().trim(), wp = gd.getNextString().trim()
Prefs.set("wavu.handshake", hs); Prefs.set("wavu.hostPrefix", hp); Prefs.set("wavu.workerPrefix", wp)
try {
    Map w = wavu.connect(new File(hs), hp ?: null, wp ?: null)
    IJ.showMessage("Wavu", "Connected to the worker serving\n" + w.scriptDir +
            "\n\nNow use Plugins > Wavu > Run Python Script... and pick it from the list.")
} catch (Exception e) {
    IJ.error("Wavu", e.getMessage())
}
