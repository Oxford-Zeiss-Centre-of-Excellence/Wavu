#@ File (label = "Time-lapse (T, Y, X)", style = "file") timelapse
#@ File (label = "segment_frames folder", style = "directory") segmentDir
#@ File (label = "Output folder", style = "directory") outDir
// Minimal dynamic cell counting in Fiji (guide/workflows/pipeline-fiji.md):
// open -> segment (Wavu) -> track (TrackMate) -> tabulate -> plot + overlay.
// SPDX-License-Identifier: GPL-3.0-or-later
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

// Wavu's scripting library (installed with wavu-fiji).
def wavu = new GroovyShell(this.class.classLoader).evaluate(
        new File(IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt"))

try {
    // 1. Open the time-lapse (native Fiji).
    def imp = IJ.openImage(timelapse.path)
    def cal = imp.getCalibration()
    double dt = cal.frameInterval > 0 ? cal.frameInterval : 1   // minutes per frame
    int nFrames = imp.getNFrames()

    // 2. Segment every frame (Wavu: examples/segment_frames in its own environment).
    Map seg = wavu.run(segmentDir, "script", [sigma: 2, threshold: "otsu", min_area: 30], [image: imp])
    def labels = seg.images.labels                    // uint16 label stack, one frame per time point
    labels.setCalibration(cal.copy())                 // same pixel size and frame interval

    // 3. Track the labelled nuclei (native Fiji: TrackMate).
    def model = new Model()
    model.setLogger(Logger.VOID_LOGGER)
    def settings = new Settings(labels)
    settings.detectorFactory = new LabelImageDetectorFactory()
    settings.detectorSettings = settings.detectorFactory.getDefaultSettings()
    settings.detectorSettings["TARGET_CHANNEL"] = 1
    settings.detectorSettings["SIMPLIFY_CONTOURS"] = false
    settings.trackerFactory = new SparseLAPTrackerFactory()
    settings.trackerSettings = settings.trackerFactory.getDefaultSettings()
    settings.trackerSettings["LINKING_MAX_DISTANCE"] = 10d     // microns
    settings.trackerSettings["ALLOW_GAP_CLOSING"] = true
    settings.trackerSettings["GAP_CLOSING_MAX_DISTANCE"] = 10d
    settings.trackerSettings["MAX_FRAME_GAP"] = 2              // frames
    settings.trackerSettings["ALLOW_TRACK_SPLITTING"] = true   // divisions
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
        // A division: a spot linked to two spots in a later frame.
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
    counts.show("Cells per frame")
    tracks.show("Tracks")
    counts.save(new File(outDir, imp.getShortTitle() + "-counts.csv").path)
    tracks.save(new File(outDir, imp.getShortTitle() + "-tracks.csv").path)

    // 5a. Plot cells per frame against time.
    def plot = new Plot("Cells per frame", "time (" + (cal.getTimeUnit() ?: "frame") + ")", "cells")
    plot.setColor(new Color(0x1565c0))
    plot.setLineWidth(2)
    double[] times = (0..<nFrames).collect { it * dt } as double[]
    plot.add("line", times, perFrame as double[])
    plot.add("circle", times, perFrame as double[])
    plot.setLimits(0, (nFrames - 1) * dt, 0, perFrame.max() + 5)
    plot.show()
    IJ.saveAs(plot.getImagePlus(), "PNG", new File(outDir, imp.getShortTitle() + "-counts.png").path)

    // 5b. Draw each track's path on the original, one colour per track,
    //     and a circle around each nucleus in the frame where it is.
    double px = cal.pixelWidth
    def overlay = new Overlay()
    trackIds.each { id ->
        def colour = Color.getHSBColor((float) ((id * 0.618034) % 1), 0.9f, 1f)
        tm.trackEdges(id).each { e ->
            def a = tm.getEdgeSource(e), b = tm.getEdgeTarget(e)
            def line = new Line(a.getDoublePosition(0) / px, a.getDoublePosition(1) / px,
                                b.getDoublePosition(0) / px, b.getDoublePosition(1) / px)
            line.setStrokeColor(colour)
            overlay.add(line)                                   // on every frame: the whole path
        }
        tm.trackSpots(id).each { s ->
            double r = s.getFeature("RADIUS") / px
            def ring = new OvalRoi(s.getDoublePosition(0) / px - r, s.getDoublePosition(1) / px - r, 2 * r, 2 * r)
            ring.setStrokeColor(colour)
            ring.setPosition(1, 1, (s.getFeature("FRAME") as int) + 1)   // only in its own frame
            overlay.add(ring)
        }
    }
    imp.setOverlay(overlay)
    IJ.run(imp, "Grays", "")
    // A snapshot of the last frame with what is drawn on it.
    imp.setT(nFrames)
    def last = new ImagePlus("last frame", imp.getProcessor().duplicate())
    last.setOverlay(new Overlay())
    overlay.each { roi -> if (roi.getTPosition() in [0, nFrames]) last.getOverlay().add(roi) }
    IJ.saveAs(last.flatten(), "PNG", new File(outDir, imp.getShortTitle() + "-tracks.png").path)
    imp.show()
    labels.close()

    IJ.log("Cells per frame: " + perFrame.join(" "))
    IJ.log(trackIds.size() + " tracks, " + divisions + " divisions")
    println "WAVU_DAG_OK frames=${nFrames} tracks=${trackIds.size()} divisions=${divisions} counts=${perFrame.join(',')}"  // test marker
} finally {
    wavu.stopAll()                                               // stop the worker
}
