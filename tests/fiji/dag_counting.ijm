// Minimal dynamic cell counting in Fiji, as an ImageJ macro (guide/workflows/pipeline-fiji.md):
// open -> segment (Wavu) -> track (Wavu: trackpy) -> tabulate -> plot + overlay.
// Run it from the script editor (it asks for the files), or from the command line:
//   ImageJ-win64.exe --console -batch dag_counting.ijm "<time-lapse>|<segment_frames>|<track_trackpy>|<output folder>"
// SPDX-License-Identifier: GPL-3.0-or-later
arg = getArgument();
if (arg == "") {
    timelapse = File.openDialog("Choose the time-lapse (T, Y, X)");
    segmentDir = getDirectory("Choose the segment_frames folder");
    trackDir = getDirectory("Choose the track_trackpy folder");
    outDir = getDirectory("Choose the output folder");
} else {
    a = split(arg, "|");
    timelapse = a[0]; segmentDir = a[1]; trackDir = a[2]; outDir = a[3] + "/";
}
setBatchMode(true);

// 1. Open the time-lapse (native Fiji).
open(timelapse);
movie = getImageID();
name = File.nameWithoutExtension;
dt = Stack.getFrameInterval();
if (dt == 0) dt = 1;
Stack.getUnits(xu, yu, zu, timeUnit, vu);
Stack.getDimensions(w, h, channels, slices, frames);

// 2. Segment every frame (Wavu: segment_frames). Opens <name>-labels,
//    <name>-detections and <name>-count_per_frame.
run("Run Script (Macro)", "folder=[" + segmentDir + "] script=script params=[sigma=2 threshold=otsu min_area=30]");

// 3. Track (Wavu: track_trackpy), given the detections table. Opens "tracks".
//    search_range is in pixels per frame: 15 px = about 10 microns here.
run("Run Script (Macro)", "folder=[" + trackDir + "] script=script params=[search_range=15 memory=2] tables=[detections=" + name + "-detections]");

// 4. Tabulate: cells per frame and number of tracks, from the tracks table.
n = Table.size("tracks");
cells = newArray(frames);
times = newArray(frames);
nTracks = 0;
for (i = 0; i < n; i++) {                          // rows are sorted by particle, then frame
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
Array.getStatistics(cells, cmin, cmax);
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
Stack.setFrame(frames);                            // last frame, with the tracks drawn in
run("Flatten");
saveAs("PNG", outDir + name + "-tracks.png");
close();
setBatchMode("exit and display");

counts = "" + cells[0];
for (t = 1; t < frames; t++) counts = counts + " " + cells[t];
print("Cells per frame: " + counts);
print(nTracks + " tracks");
run("Stop Worker");                                // stop both workers
print("WAVU_DAG_MACRO_OK frames=" + frames + " tracks=" + nTracks + " counts=" + replace(counts, " ", ","));  // test marker
