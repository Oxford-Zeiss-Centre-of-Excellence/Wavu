# 從筆記本到 Wavu

## 用白話說

筆記本裡的一個儲存格和一個 Wavu 腳本做的是同樣的工作，只有**進出的門**換了。
在筆記本裡，是*你*自己輸入設定、載入檔案、看圖表。在 Wavu 裡，**Fiji**
用對話框填好設定、把已經開著的影像交給你，再把你回傳的東西顯示出來。
中間的分析完全不用改。

```mermaid
flowchart LR
    subgraph NB["筆記本"]
        A1["sigma = 2.0"]:::script
        A2["img = io.imread(...)"]:::script
        A3["你的分析"]:::worker
        A4["plt.imshow(labels)"]:::script
    end
    subgraph WV["Wavu 腳本"]
        B1["PARAMS → 對話框"]:::fiji
        B2["inputs['image']"]:::fiji
        B3["你的分析"]:::worker
        B4["return {'labels': labels}"]:::fiji
    end
    A1 -.-> B1
    A2 -.-> B2
    A3 -.-> B3
    A4 -.-> B4

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## 對照表

| 在筆記本裡 | 在 `script.py` 裡 | 在 Fiji 裡看到的 |
|---|---|---|
| `sigma = 2.0` | 在 `PARAMS` 裡寫 `"sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"}`，再用 `params["sigma"]` | 一個數字欄位 **Sigma (pixels)** |
| `img = io.imread("cells.tif")` | 在 `PARAMS` 裡寫 `"image": {"type": "image"}`，再用 `inputs["image"]` | 列出已開啟影像的下拉選單 |
| `print("found", n)` | `ctx.log(f"found {n}")`（`print` 也可以） | **Log** 視窗裡的一行 |
| `plt.imshow(labels)` | `return {"labels": labels}` | 一個名為 *…-labels* 的新影像視窗 |
| `df`（一個表格） | `return {"cells": df}` | 一個 Results 表格 |

## 實際範例

這是一個典型的筆記本儲存格，對細胞核做閾值分割並計數：

```python
from skimage import io, filters, measure

sigma = 2.0
img = io.imread("nuclei.tif")
smooth = filters.gaussian(img, sigma)
mask = smooth > filters.threshold_otsu(smooth)
labels = measure.label(mask)
print("found", labels.max(), "nuclei")
plt.imshow(labels)
```

同樣的事寫成 Wavu 腳本。把 `script.py` 的內容換成：

```python
"""Count nuclei -- Otsu threshold after a Gaussian blur."""

PARAMS = {
    "image": {"type": "image", "label": "Nuclei image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
}


def run(ctx, inputs, params):
    from skimage import filters, measure

    img = inputs["image"]                     # 對話框裡選的影像
    smooth = filters.gaussian(img, params["sigma"])
    mask = smooth > filters.threshold_otsu(smooth)
    labels = measure.label(mask)
    ctx.log(f"found {labels.max()} nuclei")   # 出現在 Fiji 的 Log
    return {"labels": labels}                 # 以新影像開啟
```

這裡用到 scikit-image，所以先在 `pixi.toml` 加上 `scikit-image = "*"`
（[做法](get-the-template.md#adding-a-package)）。兩個檔案都儲存，按
**Stop Worker**，然後在 *Blobs* 上執行。

## 三條規則

1. **最上方的 `PARAMS`** 就是對話框。每一項變成一個欄位。
2. **`def run(ctx, inputs, params):`** 是真正做事的地方。影像放在 `inputs`，
   其他設定放在 `params`，`ctx` 則是你通往 Fiji 的熱線（Log、進度條、取消）。
3. **回傳一個字典。** 每個鍵成為一個結果的名稱（Fiji 會在前面加上影像名稱，
   例如 *blobs-labels*），每個值會用合適的方式顯示。

!!! tip "兩個省時間的習慣"
    - **在 `run` 裡面才 import 大型套件**，如上例。這樣 Fiji 能立刻顯示對話框，
      不必等大型套件載入。
    - **遇到使用者操作錯誤時，丟出一句白話的錯誤**，例如
      `raise ValueError("Please pick a single-channel image")`。Fiji 會在錯誤視窗裡顯示這段訊息。

docstring（最上方三引號裡的文字）的第一行會顯示在對話框頂端，
所以寫一句簡短的說明就好。

## 一句話總結

分析保持原樣；只要從 `params` 取設定、從 `inputs` 取影像、用 `ctx.log`
寫訊息，再 `return` 你想看到的東西。

[下一步：PARAMS = 你的對話框 :material-arrow-right:](params.md){ .md-button }
