// Regenerate documentation screenshots with java.awt.Robot (screenshots.yml, under Xvfb).
//
// STATUS: first implementation, NOT yet run anywhere. TODO:
//   - verify window placement/timing under Xvfb on GitHub runners;
//   - capture the Run dialog via a non-modal path (today a timer thread grabs
//     the screen while the modal GenericDialog is up, then disposes it);
//   - commit the PNGs back (screenshots.yml only uploads an artifact).
//
// Env: WAVU_LIB (client library), WAVU_SCRIPT_DIR (template), WAVU_SHOTS (output folder).
// SPDX-License-Identifier: GPL-3.0-or-later
import ij.IJ
import ij.ImagePlus
import ij.gui.GenericDialog
import java.awt.Rectangle
import java.awt.Robot
import java.awt.Toolkit
import java.awt.Window
import javax.imageio.ImageIO

File out = new File(System.getenv("WAVU_SHOTS") ?: "docs/screenshots")
out.mkdirs()
Robot robot = new Robot()

def shoot = { String name, Window win = null ->
    Thread.sleep(800)
    Rectangle r = win != null && win.isShowing() ? win.getBounds() : new Rectangle(Toolkit.getDefaultToolkit().getScreenSize())
    ImageIO.write(robot.createScreenCapture(r), "png", new File(out, name + ".png"))
    println "captured " + name
}

def wavu = new GroovyShell(this.class.classLoader).evaluate(new File(System.getenv("WAVU_LIB")))

// 1. An image to work on.
ImagePlus imp = IJ.openImage("https://imagej.net/images/blobs.gif") ?: IJ.createImage("blobs", "8-bit ramp", 256, 254, 1)
imp.show()
IJ.log("Wavu screenshot run")

// 2. The parameter dialog built from the template's PARAMS.
Map w = wavu.startWorker(new File(System.getenv("WAVU_SCRIPT_DIR")), false)
Map schema = wavu.getOk(w, "/scripts").scripts.script
Thread.start {
    Thread.sleep(2500)
    Window dlg = Window.getWindows().find { it.isShowing() && it instanceof java.awt.Dialog && it.title.startsWith("Wavu") }
    shoot("run-dialog", dlg)
    dlg?.dispose()
}
wavu.askParams("script", schema, false)

// 3. The result next to the input, with the Log showing streamed messages.
Map result = wavu.runJob(w, "script", [sigma: 3.0d], [image: wavu.encodeImage(imp, w)])
wavu.openOutputs(w, result.outputs, imp, "blobs-", true)
shoot("result")

wavu.stopAll()
System.exit(0)
