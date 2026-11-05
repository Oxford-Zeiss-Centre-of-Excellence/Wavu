---
title: Wavu
hide:
  - navigation
  - toc
---

# Wavu: your Python, inside Fiji

*Wavu* is Fijian for **bridge**. It connects Fiji, where you look at your
images, to Python, where tools like Cellpose and scikit-image live.

Think of a restaurant. **Fiji is the waiter**: it takes your order (a dialog
with a few fields) and brings the plate back to your table (new images,
tables, outlines). **The worker is the kitchen** behind the door, and every
recipe has **its own pantry**, so the Cellpose recipe never borrows (or
breaks) the ingredients of the blur recipe.

```mermaid
flowchart LR
    subgraph FIJI["Fiji (the waiter)"]
        D["Dialog<br/>built from PARAMS"]:::fiji
        R["Results<br/>images · tables · ROIs"]:::fiji
    end
    subgraph PY["Worker (the kitchen)"]
        S["your script.py"]:::script
    end
    E[("its own pixi env<br/>(the pantry)")]:::env

    D -- "your order" --> S
    S -.- E
    S -- "the plate + live Log" --> R

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef env    fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    style FIJI fill:#f5f9ff,stroke:#90caf9
    style PY   fill:#f6fbf6,stroke:#a5d6a7
```

## What do you want to do?

<div class="grid cards" markdown>

-   :material-play-circle-outline:{ .lg .middle } **Use a script**

    ---

    Install Wavu in Fiji and run your first Python script on a sample
    image. No terminal needed.

    [:octicons-arrow-right-24: Start here](start/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **Write a script**

    ---

    Turn your notebook into a Fiji menu item. Get the ready-made
    boilerplate with one click:

    [Open the template in VS Code](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: How it works](write/get-the-template.md)

-   :material-share-variant-outline:{ .lg .middle } **Share a script**

    ---

    Give your tool to the whole lab as one zip file. Publishing to the
    world is optional.

    [:octicons-arrow-right-24: Share with your lab](share/with-your-lab.md)

</div>

## Good to know

- **Small, interactive data.** One image that fits in memory, up to roughly
  1–2 GB. For huge data, use a batch or HPC workflow instead.
- **Every script has its own environment**, so a PyTorch script and a
  NumPy-only script never fight.

Want every detail, from idea to a released plugin? Read the
[full guide on GitHub](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md).
