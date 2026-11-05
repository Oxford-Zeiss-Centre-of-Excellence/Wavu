# Sharing your script with other Fiji users

```mermaid
flowchart LR
    S["your script folder<br/>script.py + pixi.toml"]:::you
    L["pixi.lock<br/>committed"]:::you
    P["wavu package"]:::tool
    Z["my-tool-fiji.zip"]:::out
    U["Fiji user<br/>Plugins › My Lab › My Tool"]:::fiji
    S --> L --> P --> Z -- "unzip into Fiji.app" --> U

    classDef you  fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef tool fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef out  fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef fiji fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
```

1. Commit `pixi.lock`. Run `pixi install` once in the script folder to create
   it.
2. Run `pixi run wavu package . --name my-tool --menu "My Lab>My Tool"`. This
   writes `dist/fiji/` and `dist/my-tool-fiji.zip`.
3. Users unzip that file into `Fiji.app` (Wavu must already be installed) and
   get **Plugins › My Lab › My Tool**. The first start downloads the packages
   pinned in your lock.

## Automated releases

Folders created with `wavu new-script` include
`.github/workflows/release.yml`. Push a tag such as `v1.0.0` and GitHub tests
the script, packages it and attaches the zip to a GitHub Release. You can
switch on PyPI or your own Fiji update site with repository variables. See the
comments in that file and [script-contract.md](script-contract.md).

For a full walk-through, see the
[Cellpose plugin tutorial](tutorial-cellpose-plugin.md).
