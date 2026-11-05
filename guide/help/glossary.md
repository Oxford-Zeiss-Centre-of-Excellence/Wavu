# Glossary

## The idea in plain words

Every field has its jargon. Here is each Wavu word in one plain line, with
the restaurant picture where it helps.

![The restaurant analogy: Fiji is the waiter, the worker is the kitchen, every recipe has its own pantry](../assets/img/restaurant.svg){ width="560" }

## Words

**Fiji**
:   The image-analysis program you already use (ImageJ with plugins). In Wavu
    it is the *waiter*: dialog in, results out.

**Wavu**
:   Fijian for "bridge". The menu items in Fiji plus a small Python helper
    that connect Fiji to your Python script.

**Script**
:   A `.py` file with `PARAMS` and a `run` function. The *recipe*.

**Script folder**
:   A folder with a `pixi.toml` and one or more scripts. What you pick in
    **Run Python Script**.

**PARAMS**
:   The list at the top of a script that describes the dialog fields. The
    *menu card*.

**`run(ctx, inputs, params)`**
:   The function Wavu calls. `inputs` holds the images, `params` the other
    settings, `ctx` is the line back to Fiji.

**ctx**
:   Short for "context": `ctx.log`, `ctx.progress`, `ctx.cancelled` and
    friends.

**Worker**
:   A small Python program on *your* computer that runs your script when Fiji
    asks. The *kitchen*. It talks to Fiji only on your own machine.

**Environment**
:   A private folder holding one exact Python plus the packages one script
    needs, kept in `.pixi` inside the script folder. The *pantry*.

**pixi**
:   The free tool that builds environments and downloads packages, a modern
    alternative to conda. Wavu fetches it for you.

**`pixi.toml`**
:   The *shopping list*: which packages the script needs.

**Lock file (`pixi.lock`)**
:   The *receipt*: the exact version of every package. Sharing it means
    everyone gets the same environment.

**conda-forge / PyPI**
:   The two big online "shops" for Python packages. pixi uses conda-forge
    by default; PyPI is where `pip` shops.

**NumPy array**
:   Python's grid of numbers; how your script receives and returns images.

**Labels (label image)**
:   An image where each object has its own whole number (1, 2, 3 …) and the
    background is 0. Fiji shows it in random bright colours.

**ROI**
:   "Region of interest": an outline drawn on an image. Fiji keeps them in the
    **ROI Manager**; a *RoiSet* is a zip file full of them.

**Cooperative cancel**
:   Esc raises a flag; your script checks it and stops itself.

**Breakpoint**
:   A red dot in VS Code where a running script pauses so you can look inside.

**Tag / release**
:   A version label such as `v1.0.0` on your code, and the download page
    GitHub makes for it.

**CI**
:   "Continuous integration": GitHub's robot that tests and packages your
    code when you push a tag. Optional.

**Update site**
:   A Fiji download source you tick in **Help › Update…** to install and
    update plugins.

## In one sentence

Fiji is the waiter, the worker the kitchen, your script the recipe, its
pixi environment the pantry and `pixi.lock` the receipt.
