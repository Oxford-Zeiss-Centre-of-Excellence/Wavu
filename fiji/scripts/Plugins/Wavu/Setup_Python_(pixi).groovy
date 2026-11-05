// Plugins > Wavu > Setup Python (pixi)
// Finds pixi, or downloads the official single-binary release for this OS/CPU
// from github.com/prefix-dev/pixi, verifies its sha256 and installs it into
// <Fiji>/wavu (or ~/.wavu/bin if Fiji's folder is read-only).
// SPDX-License-Identifier: GPL-3.0-or-later
import ij.IJ

// Load the shared Wavu library (lib/wavu_lib.groovy.txt; see docs/decisions.md D6).
// WAVU_LIB overrides the location (used by the tests, which run from a git checkout).
def wavuLibFile = System.getenv("WAVU_LIB") ? new File(System.getenv("WAVU_LIB")) :
        new File(ij.IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt")
def wavu = new GroovyShell(this.class.classLoader).evaluate(wavuLibFile)

try {
    File found = wavu.findPixi()
    if (found != null && !IJ.showMessageWithCancel("Wavu", "pixi is already available:\n" + found + "\n\nDownload the latest release anyway?")) return
    File pixi = wavu.setupPixi()
    def p = new ProcessBuilder(pixi.getAbsolutePath(), "--version").redirectErrorStream(true).start()
    String v = p.getInputStream().getText("UTF-8").trim()
    p.waitFor()
    IJ.showMessage("Wavu", "Ready: " + v + "\n" + pixi)
} catch (Exception e) {
    IJ.log("[Wavu] " + e)
    IJ.error("Wavu", "Could not set up pixi:\n" + e.getMessage() + "\n\nInstall it by hand from https://pixi.sh and try again.")
}
