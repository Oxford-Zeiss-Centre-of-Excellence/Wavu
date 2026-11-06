# 从笔记本到 Wavu

## 用大白话说

笔记本里的一个单元格和一个 Wavu 脚本干的是同一件事，只是**进出的门**变了。
在笔记本里，是*你*自己输入参数、读取文件、看图。在 Wavu 里，由 **Fiji** 或
**napari** 通过对话框或表单填好参数，把已经打开的图像交给你，再把你返回的东西
显示出来。中间的分析部分一点都不用改，脚本也一样，不管由 Fiji 还是 napari 来运行。

```mermaid
flowchart LR
    subgraph NB["笔记本"]
        A1["sigma = 2.0"]:::script
        A2["img = io.imread(...)"]:::script
        A3["你的分析"]:::worker
        A4["plt.imshow(labels)"]:::script
    end
    subgraph WV["Wavu 脚本"]
        B1["PARAMS → 对话框 / 表单"]:::fiji
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

## 对照表

| 在笔记本里 | 在 `script.py` 里 | 在 Fiji 或 napari 里看到的 |
|---|---|---|
| `sigma = 2.0` | 在 `PARAMS` 里写 `"sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"}`，再用 `params["sigma"]` | Fiji 对话框或 napari 面板表单里的一个数字输入框 **Sigma (pixels)** |
| `img = io.imread("cells.tif")` | 在 `PARAMS` 里写 `"image": {"type": "image"}`，再用 `inputs["image"]` | 一个下拉菜单：列出已打开的图像（Fiji）或 Image 和 Labels 图层（napari）；输入就是你选中的那个 |
| `print("found", n)` | `ctx.log(f"found {n}")`（`print` 也行） | Fiji 的 **Log** 窗口或 napari 面板日志里的一行 |
| `plt.imshow(labels)` | `return {"labels": labels}` | 一个名为 *…-labels* 的新图像窗口（Fiji）或一个 Labels 图层（napari） |
| `df`（一张表） | `return {"cells": df}` | 一张 Results 表（Fiji）或一个表格面板（napari） |

## 一个完整的例子

下面是一个典型的笔记本单元格：对细胞核做阈值分割并计数：

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

同样的事写成 Wavu 脚本。把 `script.py` 的内容替换成：

```python
"""Count nuclei -- Otsu threshold after a Gaussian blur."""

PARAMS = {
    "image": {"type": "image", "label": "Nuclei image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
}


def run(ctx, inputs, params):
    from skimage import filters, measure

    img = inputs["image"]                     # 对话框/表单里选中的图像
    smooth = filters.gaussian(img, params["sigma"])
    mask = smooth > filters.threshold_otsu(smooth)
    labels = measure.label(mask)
    ctx.log(f"found {labels.max()} nuclei")   # 显示在日志里
    return {"labels": labels}                 # 新图像窗口 / Labels 图层
```

这里用到了 scikit-image，所以先在 `pixi.toml` 里加上 `scikit-image = "*"`
（[怎么加](get-the-template.md#adding-a-package)）。两个文件都保存，停止 worker
（[怎么做](get-the-template.md#the-everyday-loop)），然后在一张 2-D 图像上运行：
Fiji 里用 *Blobs*，napari 里用 *Coins*
（**File › Open Sample › napari builtins › Coins**）。

## 三条规则

1. **顶部的 `PARAMS`** 就是对话框（Fiji）或表单（napari）。每一项变成一个
   输入框。
2. **`def run(ctx, inputs, params):`** 是干活的地方。图像在 `inputs` 里，
   其他参数在 `params` 里，`ctx` 是你和 Fiji 或 napari 之间的联络线（日志、进度条、取消）。
3. **返回一个字典。** 每个键是一个结果的名字（Fiji 会在前面加上图像名，
   比如 *blobs-labels*；napari 用这个键给图层命名），每个值会以合适的方式显示。

!!! tip "两个省时间的习惯"
    - **在 `run` 里面再 import 大的包**，就像上面那样。这样对话框或表单能马上出现，
      不用等大包加载。
    - **用户操作出错时，抛出一句说人话的错误**，比如
      `raise ValueError("Please pick a single-channel image")`。Fiji 会在错误窗口里显示这句话；
      napari 会在面板日志里写 `Error: …` 并弹出一条通知。

docstring（最顶上三引号里的文字）的第一行会显示在 Fiji 对话框和 napari 面板的顶部，
所以写一句简短的说明就好。

## 一句话总结

分析照旧；只要从 `params` 取参数、从 `inputs` 取图像、用 `ctx.log`
写消息，再 `return` 你想看到的东西。

[下一步：PARAMS = 你的对话框 :material-arrow-right:](params.md){ .md-button }
