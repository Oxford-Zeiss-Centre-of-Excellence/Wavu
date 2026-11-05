// Plugins > Wavu > Stop Worker -- shut down every worker this Fiji started or connected to.
// SPDX-License-Identifier: GPL-3.0-or-later
// Load the shared Wavu library (lib/wavu_lib.groovy.txt; see docs/decisions.md D6).
// WAVU_LIB overrides the location (used by the tests, which run from a git checkout).
def wavuLibFile = System.getenv("WAVU_LIB") ? new File(System.getenv("WAVU_LIB")) :
        new File(ij.IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt")
def wavu = new GroovyShell(this.class.classLoader).evaluate(wavuLibFile)

int n = wavu.stopAll()
ij.IJ.showStatus("Wavu: stopped " + n + " worker(s)")
if (n == 0) wavu.log("No workers running.")
