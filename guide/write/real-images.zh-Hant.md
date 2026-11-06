# 真實的影像

## 用白話說

*Blobs* 只是一張平面的圖。你的顯微鏡影像常常是**一疊圖**：好幾個色彩通道、
好幾個焦平面（z-stack），也許還有好幾個時間點。Wavu 把**整疊圖**當成一個
NumPy 陣列交給你的腳本，而且只要 Fiji 或 napari 知道，就會告訴你它是怎麼疊的。就像收到一盒玻片，
外加一張標籤寫著它們是按什麼順序排的。

![一疊影像平面：時間、z、通道，然後是 y 和 x](../assets/img/axes.svg){ width="640" }

## 陣列的形狀

=== "Fiji"

    軸永遠按照這個順序，長度為 1 的軸會被拿掉：

    **T**（時間）· **Z**（平面）· **C**（通道）· **Y** · **X**，RGB 彩色影像
    還會多一個長度為 3 的最後一軸 **S**。

    | Fiji 裡的影像 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 一張 2D 灰階影像，512 × 512 | `(512, 512)` | `"YX"` |
    | 3 個通道 | `(3, 512, 512)` | `"CYX"` |
    | 20 個平面、2 個通道的 z-stack | `(20, 2, 512, 512)` | `"ZCYX"` |
    | 一張 RGB 照片 | `(512, 512, 3)` | `"YXS"` |

    所以對 `ZCYX` 影像來說，「每個平面的第 2 個通道」就是 `img[:, 1]`。Fiji 會把
    8-bit、16-bit、32-bit 或 RGB 像素原封不動地送過來。

=== "napari"

    你會拿到所選圖層原本的資料，軸的順序也是圖層自己的：一個 z-stack 圖層
    送過來是 `(20, 512, 512)`。napari 通常會把每個通道各開成一個圖層，
    所以請挑你要的那個通道。

    | napari 裡的圖層 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 一張 2D 灰階影像 | `(512, 512)` | `"YX"` |
    | 20 個平面的 z-stack | `(20, 512, 512)` | 如果圖層的軸標籤是 z、y、x，就是 `"ZYX"`；否則不設定 |
    | 一張 RGB 照片 | `(512, 512, 3)` | `"YXS"` |

    **多尺度**（multiscale）圖層（影像金字塔）會送出它的全解析度層級。
    2D 和 RGB 圖層一定附有軸的字母；更大的圖層只有在 napari 的軸標籤是單純的字母
    （t、z、c、y、x，OME-Zarr 讀取器就是這樣設定的）時才會附上。所以請用
    `.get("axes")` 讀取軸，並看看 `img.ndim` 和 `img.shape`。

## 你還會拿到什麼：`ctx.meta`

`ctx.meta["image"]` 存著 Fiji 或 napari 對 `"image"` 欄位所選影像知道的資訊：

- `"axes"`：軸的字母，如上（Fiji 一定有；napari 裡 2D 和 RGB 圖層有，
  軸標籤是 t/z/c/y/x 的較大圖層也有）；
- `"pixel_um"`：像素大小（微米），如果知道的話：在 Fiji 來自影像的校正，
  在 napari 來自圖層的 **scale**（最後兩個值相等且不是 1 時）；
- `"title"`：視窗標題（Fiji）或圖層名稱（napari）。

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # 如果 Fiji/napari 沒提供，就是 None
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

先檢查形狀、丟出清楚的 `ValueError`，比讓程式碼之後才當掉更友善：
Fiji 會在錯誤視窗裡顯示這句話，napari 則顯示在面板的 log 和一則通知裡。

??? tip "軸的順序：建議用 T C Z Y X（儲存、傳遞、運算）"

    Wavu 不會重新排列任何東西：Fiji 送來 **T Z C Y X**（ImageJ hyperstack 的順序），
    napari 送來圖層自己的順序，而 Fiji 期待結果以它的順序傳回。在腳本裡你可以
    自由選擇。我們建議用 **T C Z Y X**；以下是每一層的選擇：

    | 層 | 建議 | 替代方案 | 何時選替代方案 |
    |---|---|---|---|
    | **儲存**（磁碟上的檔案） | **T C Z Y X**（或 C Z Y X、Z Y X）的 OME-Zarr | **T Z C Y X** 的 ImageJ TIFF | 主要在 Fiji 裡開啟的小資料（ImageJ TIFF 只能存它自己的順序） |
    | **傳遞**（Wavu ↔ 你的腳本） | 在 `run()` 開頭轉成 C 連續的 **T C Z Y X**；傳回前再轉回去 | 保留 Wavu 給的順序（從 Fiji 來是 **T Z C Y X**） | 逐平面處理（濾波、閾值），順序無關緊要時 |
    | **運算**（NumPy、PyTorch、GPU） | **T C Z Y X**：一個時間點是 `(C, Z, Y, X)`，加上 batch 軸就是 PyTorch 的 `(N, C, D, H, W)` | 只在 GPU 記憶體裡用 **channels last**（B Z Y X C）：`tensor.to(memory_format=torch.channels_last_3d)`；TensorFlow/Keras 預設就是它 | 在新的 NVIDIA GPU 上做混合精度 3-D 卷積；Keras 模型 |

    為什麼是 T C Z Y X？有四件事會影響軸的順序，而它對四者都合適：

    1. **顯微鏡。** 相機一次讀出一張 **Y × X** 影格（最快），壓電載台沿 **Z** 移動，
       濾鏡或雷射切換 **C**，時間間隔 **T** 最慢。把 Y、X 放在最內層、Z 緊挨著，
       就跟資料擷取的方式一致，也讓 3-D 體積保持在一起。（Z/C 迴圈的確切順序
       因設備而異。）
    2. **儲存與區塊。** NumPy 和 Zarr 陣列都是 *C 連續*：最後一個軸變化最快。
       用 T C Z Y X 時，像 `(1, 1, 64, 512, 512)` 這樣的區塊（chunk）就是
       **單一通道** 的一塊緊湊 3-D 區塊，所以只讀通道 0（例如 DAPI）時只會讀到
       那些檔案；如果通道交錯排列，每次讀取都會抓回所有通道。
       因此 [OME-NGFF 規範](https://ngff.openmicroscopy.org/0.4/#axes-md)
       要求先時間、再通道、再空間（0.4 和 0.5 版；放寬這條規定的提案
       [RFC-3](https://ngff.openmicroscopy.org/rfc/3/index.html) 仍在審查中）。
       Fiji、napari 和 Bio-Formats 都能讀。磁碟上的資料要保存數十年，GPU
       卻每隔幾年就換代。
    3. **深度學習。** `(C, Z, Y, X)` 加上 batch 軸，就正好是
       [PyTorch 的 `Conv3d`](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv3d.html)
       要的 `(N, C, D, H, W)`。對 C 連續的陣列用 `torch.from_numpy()` 會共用
       記憶體：什麼都不用複製。
    4. **GPU。** 當通道在最內層（「channels last」）時，NVIDIA 的 Tensor Core
       能更快地執行混合精度（FP16/BF16）3-D 卷積。**只在 GPU 記憶體裡** 轉換，
       就在耗時的層之前；形狀仍是 `(N, C, D, H, W)`，只有 stride 改變。結果離開
       GPU 之前，要先讓它重新連續（`.contiguous()`）。晶片的偏好絕不會進到檔案裡。

    在腳本裡轉過去再轉回來：

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
        axes = ctx.meta["image"].get("axes") or "YX"    # 從 Fiji 來，例如 "TZCYX" 或 "ZCYX"
        x, ours = to_tczyx(inputs["image"], axes)       # 例如 (C, Z, Y, X)、"CZYX"
        # PyTorch：一個時間點加上 batch 軸，不複製
        #   batch = torch.from_numpy(x)[None]           # "CZYX" 時為 (1, C, Z, Y, X)
        y = x * 2                                       # 你的運算，輸出排列不變
        return {"result": wavu.Image(back(y, ours, axes), axes=axes)}
    ```

    （軸以 `S` 結尾的 RGB 影像不在此列：請先轉成灰階或拆開顏色。如果 napari
    圖層送來時沒有 `axes`，你最清楚它的順序：自己傳入這些字母。）

## 多大算太大？

Wavu 是為了**互動式處理一張能輕鬆放進記憶體的影像**而設計的，大約到
**1–2 GB**。小影像用一則訊息就送過去；比較大的會透過磁碟上的一個暫存
TIFF 檔傳遞。你什麼都不用做：無論哪種方式，`inputs["image"]` 都是 NumPy 陣列。
這個上限在 Fiji 和 napari 裡都一樣。

!!! warning "napari：大型的延遲載入圖層會被完整載入"
    napari 可以延遲載入（lazily）顯示巨大的影像（一個 *dask* 陣列），只讀取畫面上的部分。
    Wavu 做不到：它會先把整個圖層載入記憶體再送出，所以請挑一個放得進記憶體的圖層
    （裁切過的一塊、一個通道，或解析度較低的副本）。

超過這個大小，請轉成 OME-Zarr，讓腳本一塊一塊讀取：
[流式分析](../workflows/large-data.md)在本機上可以處理約 50 GB 以內的資料。
行得通，但不建議由 Fiji 或 napari 來驅動。要處理上百個檔案時，請看
[批次處理](../workflows/batch.md)；超過約 50 GB，請改用批次或 HPC 工作流程。

## 第一次執行很慢（以及如何讓使用者安心） { #slow-first-runs-and-how-to-keep-users-calm }

有兩件事會讓*第一次*執行變慢，而且都只會發生一次：

1. **建立環境。** pixi 會下載 `pixi.toml` 裡列出的套件。如果有 PyTorch
   （Cellpose 需要它），可能多達 **1–2 GB**、花上好幾分鐘。下載時 Fiji 的 Log 或 napari 面板的 log
   會說明。
2. **下載模型權重。** Cellpose 之類的工具第一次使用時，會從網路下載訓練好的模型。
   這發生在*你的腳本裡面*，所以 Fiji 或 napari 完全不知道，看起來可能像是當掉了。

**在耗時的步驟之前一定要寫 Log**，讓使用者知道發生了什麼事：

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "一套能用的 Cellpose 設定"
    Wavu 儲存庫裡有一個完整的 Cellpose 細胞核腳本，包含一份含 PyTorch、
    Cellpose 和選用 NVIDIA GPU 設定的 `pixi.toml`：
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei)。
    把它的 `[dependencies]` 和 `[pypi-dependencies]` 那幾行複製到你自己的
    `pixi.toml`。Apple 晶片的 Mac 不用設定就能用 GPU。

## 一句話總結

你的腳本會拿到整張影像，是一個陣列（從 Fiji 來是 **T Z C Y X** 順序，
從 napari 來是圖層自己的順序；看 `ctx.meta` 和形狀確認；
我們建議重新排成 **T C Z Y X**，也就是 OME-NGFF 和 PyTorch 的順序），不管在 Fiji 還是 napari，
大小最好都在 1–2 GB 以內，而且在任何耗時的步驟（例如第一次下載模型）
之前，都應該先 `ctx.log`。

[下一步：以容器分享 :material-arrow-right:](container.md){ .md-button }
