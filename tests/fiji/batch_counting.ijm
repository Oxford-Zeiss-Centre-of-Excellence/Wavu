// Batch: the pipeline of "Pipeline in Fiji" (macro) for every .tif in a folder.
// From the command line:
//   ImageJ-win64.exe --console -batch batch_counting.ijm "<input folder>|<segment_frames>|<track_trackpy>|<output folder>"
arg = getArgument();
if (arg == "") {
    inDir = getDirectory("Choose the folder of time-lapses");
    segmentDir = getDirectory("Choose the segment_frames folder");
    trackDir = getDirectory("Choose the track_trackpy folder");
    outDir = getDirectory("Choose the output folder");
} else {
    a = split(arg, "|");
    inDir = a[0] + "/"; segmentDir = a[1]; trackDir = a[2]; outDir = a[3] + "/";
}
setBatchMode(true);
list = getFileList(inDir);
Table.create("Batch summary");

for (f = 0; f < list.length; f++) {
    if (!endsWith(toLowerCase(list[f]), ".tif")) continue;
    print("[" + (f + 1) + "/" + list.length + "] " + list[f]);
    timelapse = inDir + list[f];

    // 1. Open the time-lapse (native Fiji).
    open(timelapse);
    movie = getImageID();
    name = File.nameWithoutExtension;
    dt = Stack.getFrameInterval();
    if (dt == 0) dt = 1;
    Stack.getUnits(xu, yu, zu, timeUnit, vu);
    Stack.getDimensions(w, h, channels, slices, frames);

    // 2. Segment every frame (Wavu). The worker started for the first file is reused.
    run("Run Script (Macro)", "folder=[" + segmentDir + "] script=script params=[sigma=2 threshold=otsu min_area=30]");

    // 3. Track (Wavu: trackpy), given the detections table. Opens "tracks".
    run("Run Script (Macro)", "folder=[" + trackDir + "] script=script params=[search_range=15 memory=2] tables=[detections=" + name + "-detections]");

    // 4. Tabulate: cells per frame and number of tracks.
    n = Table.size("tracks");
    cells = newArray(frames);
    times = newArray(frames);
    nTracks = 0;
    for (i = 0; i < n; i++) {
        t = Table.get("frame", i, "tracks");
        cells[t] = cells[t] + 1;
        if (i == 0 || Table.get("particle", i, "tracks") != Table.get("particle", i - 1, "tracks"))
            nTracks++;
    }
    Table.create("Cells per frame");
    for (t = 0; t < frames; t++) {
        times[t] = t * dt;
        Table.set("frame", t, t);
        Table.set("time_" + timeUnit, t, times[t]);
        Table.set("cells", t, cells[t]);
    }
    Table.update;
    Table.save(outDir + name + "-counts.csv");

    // 5a. Plot cells per frame against time.
    Plot.create("Cells per frame", "time (" + timeUnit + ")", "cells");
    Plot.setColor("#1565c0");
    Plot.setLineWidth(2);
    Plot.add("line", times, cells);
    Plot.add("circle", times, cells);
    Array.getStatistics(cells, cmin, cmax, cmean);
    Plot.setLimits(0, (frames - 1) * dt, 0, cmax + 5);
    Plot.show();
    saveAs("PNG", outDir + name + "-counts.png");

    // 5b. Draw each track's path on the original, one colour per track.
    selectImage(movie);
    run("Grays");
    palette = newArray("#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4",
                       "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080", "#e6beff");
    Overlay.remove;
    for (i = 1; i < n; i++) {
        p = Table.get("particle", i, "tracks");
        if (Table.get("particle", i - 1, "tracks") != p) continue;
        setColor(palette[p % palette.length]);
        Overlay.drawLine(Table.get("x", i - 1, "tracks"), Table.get("y", i - 1, "tracks"),
                         Table.get("x", i, "tracks"), Table.get("y", i, "tracks"));
    }
    Overlay.show;
    Stack.setFrame(frames);
    run("Flatten", "slice");
    saveAs("PNG", outDir + name + "-tracks.png");

    // Batch: one row for this file, then close everything it opened.
    r = Table.size("Batch summary");
    Table.set("file", r, list[f], "Batch summary");
    Table.set("frames", r, frames, "Batch summary");
    Table.set("first_count", r, cells[0], "Batch summary");
    Table.set("last_count", r, cells[frames - 1], "Batch summary");
    Table.set("mean_cells", r, cmean, "Batch summary");
    Table.set("tracks", r, nTracks, "Batch summary");
    close("*");                                    // all images: movie, labels, plot, snapshot
    close(name + "-detections");
    close(name + "-count_per_frame");
    close("tracks");
    close("Cells per frame");
}

// The folder: one CSV and one summary plot.
Table.save(outDir + "batch-summary.csv", "Batch summary");
last = Table.getColumn("last_count", "Batch summary");
mean = Table.getColumn("mean_cells", "Batch summary");
x = Array.getSequence(last.length);
Plot.create("Batch summary", "file (0 = first)", "cells");
Plot.setColor("#1565c0");
Plot.add("circle", x, last);
Plot.setColor("#ef6c00");
Plot.add("circle", x, mean);
Plot.setLegend("final count\tmean per frame");
Plot.show();
saveAs("PNG", outDir + "batch-summary.png");
setBatchMode("exit and display");
run("Stop Worker");                                // stop both workers, once
