---
title: Home
hide:
  - navigation
  - toc
---

# Wavu: your Python, inside your image viewer

*Wavu* is Fijian for **bridge**. It connects the viewer where you look at
your images, **Fiji** or **napari**, to Python, where tools like Cellpose and
scikit-image live.

Think of a restaurant. **The viewer is the waiter**: it takes your order (a
dialog with a few fields), carries your images in as the **ingredients**, and
brings the plate back to your table (new images, tables, outlines). **The
worker is the kitchen** behind the door, and every recipe has **its own
kitchenware**, its own pots, knives and ovens (the Python packages), so the
Cellpose recipe never borrows (or breaks) the tools of the blur recipe. The
same recipe can be served by either waiter.

![The waiters (frontends): wavu-fiji, wavu-napari → The kitchen (backend): wavu worker, your script.py PARAMS + run(), its own pixi env (the kitchenware) — optional: the whole kitchen in a container (Docker / Apptainer)](assets/img/home-model.svg){ width="1000" }

**One script folder, two viewers.** You write `script.py` once; Fiji users
and napari users both run it, each time in the folder's own environment.

## Why this exists { #why-this-exists }

- **One environment for everything breaks.** `pip install` a Cellpose plugin
  into napari's environment and it can pull in a different PyTorch, NumPy or
  Qt; the next plugin pins other versions, and napari or a colleague's tool
  stops starting. Mixing `conda` and `pip` in one environment makes it worse.
- **Python inside Fiji is harder still.** Fiji's own scripting is Jython
  (Python 2.7, no NumPy). Bridges such as PyImageJ mean matching Java,
  conda and package versions by hand on every machine.
- **Wavu's answer:** the viewer stays small and clean, and every script runs
  in **its own pixi environment**, built from its own `pixi.lock`. Scripts
  never share packages, so they cannot break each other, napari or Fiji, and
  the same folder installs identically on every computer.

## Not just a bridge: whole analyses, scripted

Wavu is also a **function call** your own scripts can make. A Groovy script,
an ImageJ macro or a Python notebook loops over a folder, does the native
steps itself (open, preprocess, measure, save) and hands only the heavy step,
such as Cellpose, to Wavu, which runs it in its own environment and returns
the result to the script. One script, the whole folder, every time the same.

[Scripted workflows :material-arrow-right:](workflows/index.md){ .md-button .md-button--primary }

## Where do you want to start?

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **Understand the model**

    ---

    Waiter, kitchen, kitchenware: what runs where, and why your packages
    never clash.

    [:octicons-arrow-right-24: How it works](model/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **Write a script**

    ---

    Turn your notebook into a menu item, tests first. Get the ready-made
    boilerplate with one click:

    [Open the template in VS Code](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: Get the template](write/get-the-template.md)

-   :material-microscope:{ .lg .middle } **Use it in Fiji**

    ---

    Install wavu-fiji, run your first script on a sample image, and share
    tools with your lab as one zip file.

    [:octicons-arrow-right-24: wavu-fiji](fiji/install.md)

-   :material-layers-outline:{ .lg .middle } **Use it in napari**

    ---

    Start napari with the Wavu panel; results come back as Image, Labels and
    Shapes layers.

    [:octicons-arrow-right-24: wavu-napari](napari/install.md)

</div>

## Good to know

- **How much data?** Interactive use means one image that fits in memory,
  roughly 1–2 GB. With chunked, streamed processing (OME-Zarr), Wavu can
  handle data up to about 50 GB on a local computer, **with a major caveat**:
  Fiji and napari are canvas-based viewers built around data held in memory,
  so during a stream they see only a small preview or the final result, stay
  slow while it runs, and are not the recommended place to drive it. Beyond
  about 50 GB, use a batch or HPC pipeline instead.
- **Every script has its own environment**, so a PyTorch script and a
  NumPy-only script never fight.
- **Curious how it is built?** The [architecture](model/architecture.md) page
  explains the worker, its HTTP protocol and how a viewer starts it.

Want every detail, from idea to a released Fiji plugin? Read the
[full guide on GitHub](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md).
