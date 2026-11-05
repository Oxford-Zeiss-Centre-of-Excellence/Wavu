# What is Wavu?

## The idea in plain words

You already know two worlds. In **Fiji** you open images, draw regions and
measure. In a **Jupyter notebook** you run Python tools such as Cellpose or
scikit-image. Moving between them usually means saving files, switching
programs and loading them again.

Wavu is a **bridge** between the two. You keep working in Fiji; when you need
Python, you pick a menu item, fill in a small dialog and press OK. The Python
code runs, and the results land back in Fiji as new images, tables or
outlines.

![The restaurant analogy: Fiji is the waiter, the worker is the kitchen, every recipe has its own pantry](../assets/img/restaurant.svg){ width="720" }

The restaurant picture helps:

| In the restaurant | In Wavu | What it really is |
|---|---|---|
| The waiter takes your order | **Fiji** shows a dialog | the Wavu menu items in Fiji |
| The menu card | **PARAMS** | a short list at the top of the Python script |
| The kitchen | **the worker** | a small Python program running on *your* computer |
| A recipe | **your script** | a `.py` file with a `run` function |
| Each recipe's own pantry | **the environment** | a folder with exactly the packages that script needs |

Because every recipe has its own pantry, installing PyTorch for one script can
never break another script. Nobody shares a pantry, so nothing gets spoiled.

## Who it is for

- You write notebooks and have run Cellpose or scikit-image before.
- You know Fiji, and you would like your Python step to be *one click* there.
- You do **not** want to learn Java, conda tricks or Docker.

## What it is not

!!! warning "Not for big data"
    Wavu sends one image at a time, and it must fit in your computer's memory
    (roughly up to 1–2 GB). For huge volumes, many files or whole-slide
    images, use a batch or HPC workflow instead.

!!! warning "Not a security sandbox"
    The separate environments keep *packages* apart. They do not lock a script
    in. A script can do anything your user account can do, so run only scripts
    you trust, exactly as you would with a notebook.

Wavu also does not replace your notebook. Notebooks are great for exploring;
Wavu is for the moment when the recipe works and you want to use it, or let
colleagues use it, from Fiji.

## How a run feels

1. In Fiji, open an image.
2. Choose **Plugins › Wavu › Run Python Script** and pick a script folder.
3. A dialog appears. Fill it in and press **OK**.
4. Messages scroll in Fiji's **Log** window and the progress bar moves.
5. The results open in Fiji.

The very first run of a script is slow, because its pantry (environment) is
being stocked: the packages download once. After that, it starts quickly.

## In one sentence

Wavu lets Fiji send an image and a few settings to your Python script, which
runs in its own tidy environment and sends the results straight back.

[Next: install Wavu in Fiji :material-arrow-right:](install.md){ .md-button }
