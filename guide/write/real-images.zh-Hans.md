# 真实图像

## 用大白话说

*Blobs* 只是一张平面图片。你的显微镜图像往往是**一摞图片**：好几个颜色通道、
好几个焦平面（z-stack），可能还有好几个时间点。Wavu 把**整摞图片**作为一个
NumPy 数组交给你的脚本，并且在 Fiji 或 napari 知道的情况下，告诉你它是怎么摞起来的。
就像收到一盒载玻片，外加一张标签，写明它们按什么顺序排列。

![一摞图像平面：时间、z、通道，然后是 y 和 x](../assets/img/axes.svg){ width="640" }

## 数组的形状

=== "Fiji"

    轴总是按这个顺序排列，长度为 1 的轴会被去掉：

    **T**（时间）· **Z**（平面）· **C**（通道）· **Y** · **X**，RGB 彩色图像
    最后还多一个长度为 3 的轴 **S**。

    | Fiji 里的图像 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 一张二维灰度图，512 × 512 | `(512, 512)` | `"YX"` |
    | 3 个通道 | `(3, 512, 512)` | `"CYX"` |
    | 20 个平面、2 个通道的 z-stack | `(20, 2, 512, 512)` | `"ZCYX"` |
    | 一张 RGB 照片 | `(512, 512, 3)` | `"YXS"` |

    所以对 `ZCYX` 图像来说，“每个平面的第 2 个通道”就是 `img[:, 1]`。Fiji 会把
    8 位、16 位、32 位或 RGB 像素原样发过来。

=== "napari"

    你拿到的是所选图层的原始数据，按图层自己的轴顺序排列：一个 z-stack 图层
    会以 `(20, 512, 512)` 传过来。napari 通常把每个通道打开成单独的图层，
    所以选你要的那个通道即可。

    | napari 里的图层 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 一张二维灰度图 | `(512, 512)` | `"YX"` |
    | 20 个平面的 z-stack | `(20, 512, 512)` | 如果图层的轴标签是 z、y、x，就是 `"ZYX"`；否则不设置 |
    | 一张 RGB 照片 | `(512, 512, 3)` | `"YXS"` |

    **多尺度**（multiscale）图层（图像金字塔）会发送最高分辨率的那一层。
    二维和 RGB 图层总是带有轴字母；更大的图层只有在 napari 的轴标签是简单字母
    （t、z、c、y、x，OME-Zarr 读取器就是这样设置的）时才有。所以请用
    `.get("axes")` 读取轴，并查看 `img.ndim` 和 `img.shape`。

## 你还能拿到什么：`ctx.meta`

`ctx.meta["image"]` 里存着 Fiji 或 napari 对 `"image"` 字段所选图像了解的信息：

- `"axes"`：轴的字母，同上（Fiji 总是有；napari 里二维和 RGB 图层有，
  轴标签为 t/z/c/y/x 的更大图层也有）；
- `"pixel_um"`：像素尺寸（微米），如果知道的话：Fiji 里来自图像的标定，
  napari 里来自图层的 **scale**（最后两个值相等且不为 1 时）；
- `"title"`：窗口标题（Fiji）或图层名（napari）。

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # 如果 Fiji 或 napari 没提供，就是 None
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

先检查形状、抛出清楚的 `ValueError`，比让代码在后面崩掉更友好：
Fiji 会在错误窗口里显示这句话，napari 则显示在面板日志里并弹出一条通知。

## 多大算太大？

Wavu 是为**交互式处理一张能轻松放进内存的图像**设计的，大约到
**1–2 GB**。小图像用一条消息就能传过去；大一些的会通过磁盘上的临时
TIFF 文件传递。你什么都不用做：不管哪种方式，`inputs["image"]` 都是 NumPy 数组。
这个上限在 Fiji 和 napari 里都一样。

!!! warning "napari：大的惰性图层会被完整加载"
    napari 可以惰性地显示巨大的图像（一个 *dask* 数组），只读取屏幕上的那部分。
    Wavu 做不到：它在发送前会把整个图层读进内存，所以请选一个放得进内存的图层
    （裁剪过的、单个通道，或者低分辨率的副本）。

超过这个大小，或者要处理成百上千个文件时，Wavu 就不是合适的工具了。请转成
OME-Zarr，改用批处理或 HPC 工作流。

## 首次运行很慢（以及如何让用户安心） { #slow-first-runs-and-how-to-keep-users-calm }

有两件事会让*首次*运行变慢，而且都只发生一次：

1. **构建环境。** pixi 会下载 `pixi.toml` 里列出的包。如果带上 PyTorch
   （Cellpose 需要），可能有 **1–2 GB**、要好几分钟。下载期间 Fiji 的 Log 或
   napari 面板的日志会有提示。
2. **下载模型权重。** Cellpose 这类工具第一次使用时会从网上下载训练好的模型。
   这发生在*你的脚本内部*，Fiji 或 napari 对此一无所知，看上去可能像卡死了。

**在慢步骤之前一定要写日志**，让用户知道发生了什么：

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "一套能用的 Cellpose 配置"
    Wavu 仓库里有一个完整的 Cellpose 细胞核脚本，包括一份带 PyTorch、
    Cellpose 和可选 NVIDIA GPU 配置的 `pixi.toml`：
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei)。
    把其中的 `[dependencies]` 和 `[pypi-dependencies]` 几行复制到你自己的
    `pixi.toml` 里。Apple 芯片的 Mac 开箱即可用 GPU。

## 一句话总结

你的脚本拿到的是整张图像，一个数组（来自 Fiji 时按 **T Z C Y X** 顺序，来自
napari 时按图层自己的顺序；看 `ctx.meta` 和形状来确认），不管在 Fiji 还是
napari 里，大小最好都在 1–2 GB 以内，并且在任何慢步骤（比如首次下载模型）
之前都要先 `ctx.log`。

[下一步：以容器形式分享 :material-arrow-right:](container.md){ .md-button }
