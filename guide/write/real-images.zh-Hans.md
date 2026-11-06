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

??? tip "轴的顺序：推荐 T C Z Y X（存储、传递、计算）"

    Wavu 不会重新排列任何东西：Fiji 发来 **T Z C Y X**（ImageJ hyperstack 的顺序），
    napari 发来图层自己的顺序，而 Fiji 期望结果按它的顺序传回。在脚本里你可以
    自由选择。我们推荐 **T C Z Y X**；以下是每一层的选择：

    | 层 | 推荐 | 替代方案 | 何时选替代方案 |
    |---|---|---|---|
    | **存储**（磁盘上的文件） | **T C Z Y X**（或 C Z Y X、Z Y X）的 OME-Zarr | **T Z C Y X** 的 ImageJ TIFF | 主要在 Fiji 里打开的小数据（ImageJ TIFF 只能存它自己的顺序） |
    | **传递**（Wavu ↔ 你的脚本） | 在 `run()` 开头转成 C 连续的 **T C Z Y X**；返回前再转回去 | 保留 Wavu 给的顺序（来自 Fiji 时是 **T Z C Y X**） | 逐平面处理（滤波、阈值），顺序无关紧要时 |
    | **计算**（NumPy、PyTorch、GPU） | **T C Z Y X**：一个时间点是 `(C, Z, Y, X)`，加上 batch 轴就是 PyTorch 的 `(N, C, D, H, W)` | 只在 GPU 显存里用 **channels last**（B Z Y X C）：`tensor.to(memory_format=torch.channels_last_3d)`；TensorFlow/Keras 默认就是它 | 在较新的 NVIDIA GPU 上做混合精度 3-D 卷积；Keras 模型 |

    为什么是 T C Z Y X？有四件事会影响轴的顺序，而它对四者都合适：

    1. **显微镜。** 相机一次读出一帧 **Y × X**（最快），压电载物台沿 **Z** 移动，
       滤光片或激光切换 **C**，时间间隔 **T** 最慢。把 Y、X 放在最内层、Z 紧挨着，
       就和数据采集的方式一致，也让 3-D 体积保持在一起。（Z/C 循环的确切顺序
       因设备而异。）
    2. **存储与分块。** NumPy 和 Zarr 数组都是 *C 连续*：最后一个轴变化最快。
       用 T C Z Y X 时，像 `(1, 1, 64, 512, 512)` 这样的分块（chunk）就是
       **单个通道** 的一块紧凑 3-D 块，所以只读通道 0（比如 DAPI）时只会读到
       那些文件；如果通道交错排列，每次读取都会取回所有通道。
       因此 [OME-NGFF 规范](https://ngff.openmicroscopy.org/0.4/#axes-md)
       要求先时间、再通道、再空间（0.4 和 0.5 版；放宽这条规定的提案
       [RFC-3](https://ngff.openmicroscopy.org/rfc/3/index.html) 仍在评审中）。
       Fiji、napari 和 Bio-Formats 都能读。磁盘上的数据要保存几十年，GPU
       却每隔几年就换代。
    3. **深度学习。** `(C, Z, Y, X)` 加上 batch 轴，就正好是
       [PyTorch 的 `Conv3d`](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv3d.html)
       要的 `(N, C, D, H, W)`。对 C 连续的数组用 `torch.from_numpy()` 会共享
       内存：什么都不用复制。
    4. **GPU。** 当通道在最内层（“channels last”）时，NVIDIA 的 Tensor Core
       能更快地执行混合精度（FP16/BF16）3-D 卷积。**只在 GPU 显存里** 转换，
       就在耗时的层之前；形状仍是 `(N, C, D, H, W)`，只有 stride 改变。结果离开
       GPU 之前，要先让它重新连续（`.contiguous()`）。芯片的偏好绝不会进到文件里。

    在脚本里转过去再转回来：

    ```python
    import numpy as np
    import wavu

    def to_tczyx(img, axes):
        """Reorder to T, C, Z, Y, X (only the axes present). Returns (array, new axes)."""
        new = "".join(a for a in "TCZYX" if a in axes)
        return np.ascontiguousarray(np.transpose(img, [axes.index(a) for a in new])), new

    def back(arr, axes_now, axes_wanted):
        """Reorder a result back, e.g. to the input's own order before returning it."""
        return np.ascontiguousarray(np.transpose(arr, [axes_now.index(a) for a in axes_wanted]))

    def run(ctx, inputs, params):
        axes = ctx.meta["image"].get("axes") or "YX"    # 来自 Fiji 时，例如 "TZCYX" 或 "ZCYX"
        x, ours = to_tczyx(inputs["image"], axes)       # 例如 (C, Z, Y, X)、"CZYX"
        # PyTorch：一个时间点加上 batch 轴，不复制
        #   batch = torch.from_numpy(x)[None]           # "CZYX" 时为 (1, C, Z, Y, X)
        y = x * 2                                       # 你的计算，输出排列不变
        return {"result": wavu.Image(back(y, ours, axes), axes=axes)}
    ```

    （轴以 `S` 结尾的 RGB 图像不在此列：请先转成灰度或拆开颜色。如果 napari
    图层发来时没有 `axes`，你最清楚它的顺序：自己传入这些字母。）

## 多大算太大？

Wavu 是为**交互式处理一张能轻松放进内存的图像**设计的，大约到
**1–2 GB**。小图像用一条消息就能传过去；大一些的会通过磁盘上的临时
TIFF 文件传递。你什么都不用做：不管哪种方式，`inputs["image"]` 都是 NumPy 数组。
这个上限在 Fiji 和 napari 里都一样。

!!! warning "napari：大的惰性图层会被完整加载"
    napari 可以惰性地显示巨大的图像（一个 *dask* 数组），只读取屏幕上的那部分。
    Wavu 做不到：它在发送前会把整个图层读进内存，所以请选一个放得进内存的图层
    （裁剪过的、单个通道，或者低分辨率的副本）。

超过这个大小，请转成 OME-Zarr，让脚本一块一块读取：
[流式分析](../workflows/large-data.md)在本机上可以处理约 50 GB 以内的数据。
能用，但不建议由 Fiji 或 napari 来驱动。要处理成百上千个文件时，请看
[批处理](../workflows/batch.md)；超过约 50 GB，请改用批处理或 HPC 工作流。

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
napari 时按图层自己的顺序；看 `ctx.meta` 和形状来确认；
我们建议重新排成 **T C Z Y X**，也就是 OME-NGFF 和 PyTorch 的顺序），不管在 Fiji 还是
napari 里，大小最好都在 1–2 GB 以内，并且在任何慢步骤（比如首次下载模型）
之前都要先 `ctx.log`。

[下一步：以容器形式分享 :material-arrow-right:](container.md){ .md-button }
