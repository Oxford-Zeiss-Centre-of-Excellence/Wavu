// Headless Fiji smoke test (pytest -m fiji, tests/test_fiji_smoke.py).
// Loads the real client library, starts a worker for the template script
// through pixi, runs the Gaussian blur on a synthetic image -- once inline,
// once via a TIFF path -- and checks what comes back.
// Prints WAVU_SMOKE_OK on success; any failure prints WAVU_SMOKE_FAIL.
// SPDX-License-Identifier: GPL-3.0-or-later
import ij.IJ
import ij.ImagePlus
import ij.process.ShortProcessor

def fail = { String msg -> throw new AssertionError(msg) }
def wavu = new GroovyShell(this.class.classLoader).evaluate(new File(System.getenv("WAVU_LIB")))
println "java=" + System.getProperty("java.version") + " ij=" + IJ.getVersion()
try {
    File dir = new File(System.getenv("WAVU_SCRIPT_DIR"))
    Map w = wavu.startWorker(dir, false)
    if (w == null) fail("no pixi")
    Map listing = wavu.getOk(w, "/scripts")
    if (!listing.scripts.containsKey("script")) fail("template script not listed: " + listing)

    def ip = new ShortProcessor(64, 48)
    ip.setValue(4000); ip.fill(new ij.gui.Roi(20, 20, 8, 8))
    def imp = new ImagePlus("synthetic", ip)
    imp.getCalibration().pixelWidth = 0.65
    imp.getCalibration().pixelHeight = 0.65
    imp.getCalibration().setUnit("micron")

    [["inline", wavu.INLINE_LIMIT], ["file", 0]].each { mode, limit ->
        Map inputs = [image: wavu.encodeImage(imp, w, limit)]
        if (mode == "inline" && inputs.image.data == null) fail("expected an inline input")
        if (mode == "file" && inputs.image.path == null) fail("expected a file-path input")
        Map result = wavu.runJob(w, "script", [sigma: 2.0d], inputs, mode == "inline" ? wavu.INLINE_LIMIT : 0)
        if (result.status != "done") fail(mode + ": job ended " + result)
        Map images = wavu.openOutputs(w, result.outputs, imp, "", false)
        ImagePlus out = images.blurred
        if (out == null) fail(mode + ": no 'blurred' output in " + result.outputs.keySet())
        if (out.getWidth() != 64 || out.getHeight() != 48 || out.getBitDepth() != 16) fail(mode + ": wrong output " + out)
        double peak = out.getProcessor().getStatistics().max
        double edge = out.getProcessor().getPixelValue(19, 24)
        if (!(peak < 4000 && peak > 100 && edge > 0)) fail(mode + ": not blurred (peak " + peak + ", edge " + edge + ")")
        if (Math.abs(out.getCalibration().pixelWidth - 0.65) > 1e-6) fail(mode + ": calibration lost")
        println "WAVU_SMOKE_" + mode.toUpperCase() + " peak=" + peak + " edge=" + edge
    }
    wavu.stopAll()
    println "WAVU_SMOKE_OK"
} catch (Throwable t) {
    t.printStackTrace()
    println "WAVU_SMOKE_FAIL " + t
    try { wavu.stopAll() } catch (Throwable ignored) {}
}
