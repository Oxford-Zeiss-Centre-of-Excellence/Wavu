// Headless Fiji smoke test (pytest -m fiji, tests/test_fiji_smoke.py).
// Loads the real client library, starts a worker for the template script
// through pixi, runs the Gaussian blur on a synthetic image -- once inline,
// once via a TIFF path -- and checks what comes back. With WAVU_SCRIPT_DIR2
// (tests/fiji/table_echo) it also passes a ResultsTable and a CSV path to wavu.run().
// Prints WAVU_SMOKE_OK on success; any failure prints WAVU_SMOKE_FAIL.
// SPDX-License-Identifier: GPL-3.0-or-later
import ij.IJ
import ij.ImagePlus
import ij.measure.ResultsTable
import ij.process.ShortProcessor

def fail = { String msg -> throw new AssertionError(msg) }
def wavu = new GroovyShell(this.class.classLoader).evaluate(new File(System.getenv("WAVU_LIB")))
println "java=" + System.getProperty("java.version") + " ij=" + IJ.getVersion()
try {
    File dir = new File(System.getenv("WAVU_SCRIPT_DIR"))
    println "installed scripts: " + wavu.installedScriptFolders()
    Map w = wavu.workerFor(dir)  // same path the menu stubs use (runScriptFolder)
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
    // Scripting API: one call, no dialogs, results returned (Workflows guide).
    Map r = wavu.run(dir, "script", [sigma: "2"], [image: imp])
    if (r.images.blurred == null) fail("run(): no 'blurred' in " + r)
    if (r.images.blurred.getBitDepth() != 16) fail("run(): wrong type " + r.images.blurred)
    if (wavu.parseParams("a=1 b=[two words] c=true") != [a: "1", b: "two words", c: "true"]) fail("parseParams")
    println "WAVU_SMOKE_RUN"

    // Chaining steps: a ResultsTable (and a CSV path) as inputs to wavu.run().
    String tableDir = System.getenv("WAVU_SCRIPT_DIR2")
    if (tableDir) {
        def rt = new ij.measure.ResultsTable()
        [[1, 10.5d, "a"], [2, 20d, "b,c"], [3, 7.25d, "d"]].each { lab, area, name ->
            rt.incrementCounter()
            rt.addValue("label", lab as double)
            rt.addValue("area", area as double)
            rt.addValue("name", name as String)
        }
        Map t = wavu.run(tableDir, "table_echo", [:], [table: rt])
        if (t.values.n_rows != 3) fail("table input: n_rows " + t.values)
        if (t.values.columns != "label,area,name") fail("table input: columns " + t.values.columns)
        ResultsTable back = t.tables.table
        if (back == null || back.size() != 3) fail("table input: no table back " + t)
        if (Math.abs(back.getValue("area_x2", 1) - 40d) > 1e-9 || Math.abs(back.getValue("area_x2", 2) - 14.5d) > 1e-9)
            fail("table input: wrong derived column")
        // The returned table's CSV, passed on as a path (File) to the next step.
        File csv = File.createTempFile("wavu-smoke-", ".csv")
        csv.text = "label,area\n1,2\n2,3\n"
        Map t2 = wavu.run(tableDir, "table_echo", [:], [table: csv])
        if (t2.values.n_rows != 2) fail("path input: n_rows " + t2.values)
        csv.delete()
        println "WAVU_SMOKE_TABLE rows=" + t.values.n_rows
    }

    // The recordable macro command, as a recorded ImageJ macro would call it.
    if (System.getenv("WAVU_SMOKE_MACRO")) {
        String folder = dir.getAbsolutePath().replace("\\", "/")
        IJ.runMacro("""
            setBatchMode(true);
            newImage("macro-input", "16-bit black", 64, 48, 1);
            makeRectangle(20, 20, 8, 8); run("Set...", "value=4000"); run("Select None");
            run("Run Script (Macro)", "folder=[${folder}] script=script params=[sigma=2]");
            print("WAVU_SMOKE_MACRO_DONE images=" + nImages);
        """)
    }
    wavu.stopAll()
    println "WAVU_SMOKE_OK"
} catch (Throwable t) {
    t.printStackTrace()
    println "WAVU_SMOKE_FAIL " + t
    try { wavu.stopAll() } catch (Throwable ignored) {}
}
