# Glossar

## Die Idee in einfachen Worten

Jedes Fach hat seinen Jargon. Hier steht jedes Wavu-Wort in einer einfachen
Zeile, mit dem Restaurant-Bild, wo es hilft.

![Das Restaurant-Bild: Fiji ist der Kellner, der Worker ist die Küche, jedes Rezept hat seine eigenen Küchengeräte](../assets/img/restaurant.svg){ width="560" }

## Die Wörter

**Fiji**
:   Das Bildanalyse-Programm, das Sie schon benutzen (ImageJ mit Plugins).
    In Wavu ist es der *Kellner*: Dialog rein, Ergebnisse raus.

**Wavu**
:   Fidschianisch für „Brücke“. Die Menüeinträge in Fiji plus ein kleiner
    Python-Helfer, die Fiji mit Ihrem Python-Skript verbinden.

**Skript**
:   Eine `.py`-Datei mit `PARAMS` und einer Funktion `run`. Das *Rezept*.

**Skriptordner**
:   Ein Ordner mit einer `pixi.toml` und einem oder mehreren Skripten. Das,
    was Sie in **Run Python Script** auswählen.

**PARAMS**
:   Die Liste oben in einem Skript, die die Felder des Dialogs beschreibt.
    Die *Speisekarte*.

**`run(ctx, inputs, params)`**
:   Die Funktion, die Wavu aufruft. `inputs` enthält die Bilder, `params`
    die übrigen Einstellungen, `ctx` ist der direkte Draht zu Fiji.

**ctx**
:   Kurz für „context“ (Kontext): `ctx.log`, `ctx.progress`,
    `ctx.cancelled` und Co.

**Worker**
:   Ein kleines Python-Programm auf *Ihrem* Computer, das Ihr Skript
    ausführt, wenn Fiji darum bittet. Die *Küche*. Es spricht mit Fiji nur
    auf Ihrem eigenen Rechner.

**Umgebung (Environment)**
:   Ein privater Ordner mit genau einem Python und den Paketen, die ein
    Skript braucht, abgelegt in `.pixi` im Skriptordner. Die
    *Küchengeräte* des Rezepts: eigene Töpfe, Messer und Öfen.

**pixi**
:   Das kostenlose Werkzeug, das Umgebungen baut und Pakete herunterlädt,
    eine moderne Alternative zu conda. Wavu holt es für Sie.

**`pixi.toml`**
:   Die *Liste der Küchengeräte*: welche Pakete das Skript braucht.

**Lock-Datei (`pixi.lock`)**
:   Der *Kassenbon* für die Küchengeräte: die genaue Version jedes Pakets. Wer sie weitergibt,
    sorgt dafür, dass alle dieselbe Umgebung bekommen.

**conda-forge / PyPI**
:   Die zwei großen Online-„Läden“ für Python-Pakete. pixi nutzt
    standardmäßig conda-forge; bei PyPI kauft `pip` ein.

**NumPy-Array**
:   Pythons Zahlengitter; so bekommt Ihr Skript Bilder und gibt sie zurück.

**Labels (Label-Bild)**
:   Ein Bild, in dem jedes Objekt seine eigene ganze Zahl hat (1, 2, 3 …)
    und der Hintergrund 0 ist. Fiji zeigt es in zufälligen, kräftigen
    Farben.

**ROI**
:   „Region of interest“ (interessierende Region): ein Umriss, der auf ein
    Bild gezeichnet ist. Fiji verwaltet sie im **ROI Manager**; ein
    *RoiSet* ist eine ZIP-Datei voller ROIs.

**Kooperatives Abbrechen**
:   Esc setzt eine Flagge; Ihr Skript prüft sie und hört von selbst auf.

**Haltepunkt (Breakpoint)**
:   Ein roter Punkt in VS Code, an dem ein laufendes Skript anhält, damit
    Sie hineinschauen können.

**Tag / Release**
:   Ein Versionsetikett wie `v1.0.0` an Ihrem Code, und die Download-Seite,
    die GitHub dafür anlegt.

**CI**
:   „Continuous Integration“: GitHubs Roboter, der Ihren Code testet und
    verpackt, wenn Sie einen Tag pushen. Optional.

**Update-Site**
:   Eine Download-Quelle für Fiji, die Sie in **Help › Update…** ankreuzen,
    um Plugins zu installieren und zu aktualisieren.

## In einem Satz

Fiji ist der Kellner, der Worker die Küche, Ihr Skript das Rezept, Ihre
Bilder die Zutaten, seine pixi-Umgebung die Küchengeräte und `pixi.lock`
der Kassenbon.
