#@ File (label = "Folder of time-lapses (.tif)", style = "directory") inDir
#@ File (label = "segment_frames folder", style = "directory") segmentDir
#@ File (label = "Output folder", style = "directory") outDir
// Batch: the pipeline of "Pipeline in Fiji" for every .tif in a folder,
// one row per file, one CSV and one plot for the folder.
import fiji.plugin.trackmate.Logger
import fiji.plugin.trackmate.Model
import fiji.plugin.trackmate.Settings
import fiji.plugin.trackmate.TrackMate
import fiji.plugin.trackmate.detection.LabelImageDetectorFactory
import fiji.plugin.trackmate.tracking.jaqaman.SparseLAPTrackerFactory
import ij.IJ
import ij.ImagePlus
import ij.gui.Line
import ij.gui.OvalRoi
import ij.gui.Overlay
import ij.gui.Plot
import ij.measure.ResultsTable
import java.awt.Color

def wavu = new GroovyShell(this.class.classLoader).evaluate(
        new File(IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt"))

// The pipeline for one file (steps 1-5 of the pipeline page). Returns one row.
def analyse = { File file ->
    // 1. Open the time-lapse (native Fiji).
    def imp = IJ.openImage(file.path)
    if (imp == null) throw new IOException("cannot open " + file.name)
    def cal = imp.getCalibration()
    double dt = cal.frameInterval > 0 ? cal.frameInterval : 1
    int nFrames = imp.getNFrames()

    // 2. Segment every frame (Wavu). The worker started for the first file is reused.
    Map seg = wavu.run(segmentDir, "script", [sigma: 2, threshold: "otsu", min_area: 30], [image: imp])
    def labels = seg.images.labels
    labels.setCalibration(cal.copy())

    // 3. Track (native Fiji: TrackMate).
    def model = new Model()
    model.setLogger(Logger.VOID_LOGGER)
    def settings = new Settings(labels)
    settings.detectorFactory = new LabelImageDetectorFactory()
    settings.detectorSettings = settings.detectorFactory.getDefaultSettings()
    settings.detectorSettings["TARGET_CHANNEL"] = 1
    settings.detectorSettings["SIMPLIFY_CONTOURS"] = false
    settings.trackerFactory = new SparseLAPTrackerFactory()
    settings.trackerSettings = settings.trackerFactory.getDefaultSettings()
    settings.trackerSettings["LINKING_MAX_DISTANCE"] = 10d
    settings.trackerSettings["ALLOW_GAP_CLOSING"] = true
    settings.trackerSettings["GAP_CLOSING_MAX_DISTANCE"] = 10d
    settings.trackerSettings["MAX_FRAME_GAP"] = 2
    settings.trackerSettings["ALLOW_TRACK_SPLITTING"] = true
    settings.trackerSettings["SPLITTING_MAX_DISTANCE"] = 10d
    def trackmate = new TrackMate(model, settings)
    if (!trackmate.checkInput() || !trackmate.process())
        throw new RuntimeException("TrackMate: " + trackmate.getErrorMessage())
    def tm = model.getTrackModel()
    def trackIds = tm.trackIDs(true)

    // 4. Tabulate: cells per frame, and one row per track.
    def counts = new ResultsTable()
    List<Integer> perFrame = []
    for (int t = 0; t < nFrames; t++) {
        int n = model.getSpots().getNSpots(t, true)
        perFrame << n
        counts.addRow()
        counts.addValue("frame", t)
        counts.addValue("time_min", t * dt)
        counts.addValue("cells", n)
    }
    def tracks = new ResultsTable()
    int divisions = 0
    trackIds.each { id ->
        def spots = tm.trackSpots(id)
        int splits = spots.count { s -> tm.edgesOf(s).count { e -> tm.getEdgeSource(e) == s } > 1 }
        divisions += splits
        def frames = spots.collect { it.getFeature("FRAME") as int }
        tracks.addRow()
        tracks.addValue("track", id)
        tracks.addValue("spots", spots.size())
        tracks.addValue("first_frame", frames.min())
        tracks.addValue("last_frame", frames.max())
        tracks.addValue("divisions", splits)
    }
    counts.save(new File(outDir, imp.getShortTitle() + "-counts.csv").path)
    tracks.save(new File(outDir, imp.getShortTitle() + "-tracks.csv").path)

    // 5a. Plot cells per frame (saved, not shown).
    def plot = new Plot("Cells per frame", "time (" + (cal.getTimeUnit() ?: "frame") + ")", "cells")
    plot.setColor(new Color(0x1565c0))
    plot.setLineWidth(2)
    double[] times = (0..<nFrames).collect { it * dt } as double[]
    plot.add("line", times, perFrame as double[])
    plot.add("circle", times, perFrame as double[])
    plot.setLimits(0, (nFrames - 1) * dt, 0, perFrame.max() + 5)
    IJ.saveAs(plot.getImagePlus(), "PNG", new File(outDir, imp.getShortTitle() + "-counts.png").path)

    // 5b. Tracks on the last frame (saved, not shown).
    double px = cal.pixelWidth
    def overlay = new Overlay()
    trackIds.each { id ->
        def colour = Color.getHSBColor((float) ((id * 0.618034) % 1), 0.9f, 1f)
        tm.trackEdges(id).each { e ->
            def a = tm.getEdgeSource(e), b = tm.getEdgeTarget(e)
            def line = new Line(a.getDoublePosition(0) / px, a.getDoublePosition(1) / px,
                                b.getDoublePosition(0) / px, b.getDoublePosition(1) / px)
            line.setStrokeColor(colour)
            overlay.add(line)
        }
        tm.trackSpots(id).each { s ->
            double r = s.getFeature("RADIUS") / px
            def ring = new OvalRoi(s.getDoublePosition(0) / px - r, s.getDoublePosition(1) / px - r, 2 * r, 2 * r)
            ring.setStrokeColor(colour)
            ring.setPosition(1, 1, (s.getFeature("FRAME") as int) + 1)
            overlay.add(ring)
        }
    }
    imp.setOverlay(overlay)
    IJ.run(imp, "Grays", "")
    imp.setT(nFrames)
    def last = new ImagePlus("last frame", imp.getProcessor().duplicate())
    last.setOverlay(new Overlay())
    overlay.each { roi -> if (roi.getTPosition() in [0, nFrames]) last.getOverlay().add(roi) }
    IJ.saveAs(last.flatten(), "PNG", new File(outDir, imp.getShortTitle() + "-tracks.png").path)
    imp.close()                                          // free the memory before the next file
    labels.close()

    return [frames: nFrames, times: times, perFrame: perFrame,
            tracks: trackIds.size(), divisions: divisions]
}

// The batch: loop, one row per file, one CSV and one plot for the folder.
def files = inDir.listFiles().findAll { it.name.toLowerCase().endsWith(".tif") }.sort { it.name }
def summary = new ResultsTable()
def all = new Plot("Cells per frame, all files", "time (min)", "cells")
try {
    files.eachWithIndex { File file, int i ->
        IJ.log("[${i + 1}/${files.size()}] ${file.name}")
        summary.addRow()
        summary.addValue("file", file.name)
        try {
            Map row = analyse(file)
            summary.addValue("frames", row.frames)
            summary.addValue("first_count", row.perFrame[0])
            summary.addValue("last_count", row.perFrame[-1])
            summary.addValue("mean_cells", (row.perFrame.sum() / row.frames) as double)
            summary.addValue("tracks", row.tracks)
            summary.addValue("divisions", row.divisions)
            summary.addValue("error", "")
            all.setColor(Color.getHSBColor((float) ((i * 0.618034) % 1), 0.8f, 0.8f))
            all.add("line", row.times, row.perFrame as double[])
        } catch (InterruptedException e) {
            throw e                                      // Esc: stop the whole batch
        } catch (Throwable e) {                          // also reader errors (Bio-Formats)
            IJ.log("  skipped ${file.name}: ${e}")          // one bad file: log it, go on
            summary.addValue("error", (e.message ?: e.toString()).readLines()[0])
        }
    }
} finally {
    wavu.stopAll()                                       // stop the worker once, at the end
}
summary.show("Batch summary")
summary.save(new File(outDir, "batch-summary.csv").path)
all.setLimitsToFit(false)
all.show()
IJ.saveAs(all.getImagePlus(), "PNG", new File(outDir, "batch-summary.png").path)
