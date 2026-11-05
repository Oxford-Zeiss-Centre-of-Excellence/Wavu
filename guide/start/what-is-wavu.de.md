# Was ist Wavu?

## Die Idee in einfachen Worten

Sie kennen schon zwei Welten. In **Fiji** öffnen Sie Bilder, zeichnen
Regionen ein und messen. In einem **Jupyter-Notebook** nutzen Sie
Python-Werkzeuge wie Cellpose oder scikit-image. Zwischen beiden zu wechseln
heißt meist: Dateien speichern, Programm wechseln, alles wieder laden.

Wavu ist eine **Brücke** zwischen beiden. Sie arbeiten weiter in Fiji; wenn
Sie Python brauchen, wählen Sie einen Menüeintrag, füllen einen kleinen
Dialog aus und klicken auf OK. Der Python-Code läuft, und die Ergebnisse
landen wieder in Fiji, als neue Bilder, Tabellen oder Umrisse.

![Das Restaurant-Bild: Fiji ist der Kellner, der Worker ist die Küche, jedes Rezept hat seine eigene Vorratskammer](../assets/img/restaurant.svg){ width="720" }

Das Bild vom Restaurant hilft:

| Im Restaurant | In Wavu | Was es wirklich ist |
|---|---|---|
| Der Kellner nimmt Ihre Bestellung auf | **Fiji** zeigt einen Dialog | die Wavu-Menüeinträge in Fiji |
| Die Speisekarte | **PARAMS** | eine kurze Liste oben im Python-Skript |
| Die Küche | **der Worker** | ein kleines Python-Programm, das auf *Ihrem* Computer läuft |
| Ein Rezept | **Ihr Skript** | eine `.py`-Datei mit einer Funktion `run` |
| Die eigene Vorratskammer jedes Rezepts | **die Umgebung** | ein Ordner mit genau den Paketen, die dieses Skript braucht |

Weil jedes Rezept seine eigene Vorratskammer hat, kann die Installation von
PyTorch für ein Skript niemals ein anderes Skript kaputt machen. Niemand
teilt sich eine Vorratskammer, also verdirbt auch nichts.

## Für wen ist es gedacht?

- Sie schreiben Notebooks und haben schon einmal Cellpose oder scikit-image
  benutzt.
- Sie kennen Fiji und hätten Ihren Python-Schritt dort gern mit *einem
  Klick*.
- Sie möchten **kein** Java, keine conda-Tricks und kein Docker lernen.

## Was Wavu nicht ist

!!! warning "Nicht für große Datenmengen"
    Wavu schickt jeweils ein Bild, und es muss in den Arbeitsspeicher Ihres
    Computers passen (etwa bis 1–2 GB). Für riesige Volumen, viele Dateien
    oder ganze Objektträger-Scans (Whole-Slide-Bilder) nehmen Sie besser einen
    Batch-Workflow oder einen Rechencluster (HPC).

!!! warning "Keine Sicherheits-Sandbox"
    Die getrennten Umgebungen halten *Pakete* auseinander. Sie sperren ein
    Skript nicht ein. Ein Skript kann alles, was Ihr Benutzerkonto kann:
    Führen Sie also nur Skripte aus, denen Sie vertrauen, genau wie bei einem
    Notebook.

Wavu ersetzt auch Ihr Notebook nicht. Notebooks sind ideal zum Ausprobieren;
Wavu ist für den Moment, in dem das Rezept funktioniert und Sie es aus Fiji
heraus benutzen möchten, oder Kolleginnen und Kollegen es benutzen lassen
möchten.

## Wie sich ein Durchlauf anfühlt

1. Öffnen Sie in Fiji ein Bild.
2. Wählen Sie **Plugins › Wavu › Run Python Script** (Python-Skript
   ausführen) und dann einen Skriptordner.
3. Ein Dialog erscheint. Füllen Sie ihn aus und klicken Sie auf **OK**.
4. Im **Log**-Fenster von Fiji laufen Meldungen durch, und der
   Fortschrittsbalken bewegt sich.
5. Die Ergebnisse öffnen sich in Fiji.

Der allererste Durchlauf eines Skripts ist langsam, weil seine
Vorratskammer (die Umgebung) gefüllt wird: Die Pakete werden einmal
heruntergeladen. Danach startet es schnell.

## In einem Satz

Mit Wavu schickt Fiji ein Bild und ein paar Einstellungen an Ihr
Python-Skript, das in seiner eigenen, aufgeräumten Umgebung läuft und die
Ergebnisse direkt zurückschickt.

[Weiter: Wavu in Fiji installieren :material-arrow-right:](install.md){ .md-button }
