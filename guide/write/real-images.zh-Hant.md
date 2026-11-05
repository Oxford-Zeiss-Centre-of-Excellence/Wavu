# 真實的影像

## 用白話說

*Blobs* 只是一張平面的圖。你的顯微鏡影像常常是**一疊圖**：好幾個色彩通道、
好幾個焦平面（z-stack），也許還有好幾個時間點。Wavu 把**整疊圖**當成一個
NumPy 陣列交給你的腳本，並告訴你它是怎麼疊的。就像收到一盒玻片，
外加一張標籤寫著它們是按什麼順序排的。

![一疊影像平面：時間、z、通道，然後是 y 和 x](../assets/img/axes.svg){ width="640" }

## 陣列的形狀

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

## 你還會拿到什麼：`ctx.meta`

`ctx.meta["image"]` 存著 Fiji 對 `"image"` 欄位所選影像知道的資訊：

- `"axes"`：軸的字母，如上；
- `"pixel_um"`：像素大小（微米），如果影像有校正的話；
- `"title"`：視窗標題。

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"]["axes"]
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel (Image › Duplicate…)")
    ...
```

先檢查形狀、丟出清楚的 `ValueError`，比讓程式碼之後才當掉更友善：
Fiji 會在錯誤視窗裡顯示這句話。

## 多大算太大？

Wavu 是為了**互動式處理一張能輕鬆放進記憶體的影像**而設計的，大約到
**1–2 GB**。小影像用一則訊息就送過去；比較大的會透過磁碟上的一個暫存
TIFF 檔傳遞。你什麼都不用做：無論哪種方式，`inputs["image"]` 都是 NumPy 陣列。

超過這個大小，或要處理上百個檔案時，Wavu 就不是合適的工具。請轉成
OME-Zarr，改用批次或 HPC 工作流程。

## 第一次執行很慢（以及如何讓使用者安心） { #slow-first-runs-and-how-to-keep-users-calm }

有兩件事會讓*第一次*執行變慢，而且都只會發生一次：

1. **建立環境。** pixi 會下載 `pixi.toml` 裡列出的套件。如果有 PyTorch
   （Cellpose 需要它），可能多達 **1–2 GB**、花上好幾分鐘。下載時 Fiji 的 Log 會說明。
2. **下載模型權重。** Cellpose 之類的工具第一次使用時，會從網路下載訓練好的模型。
   這發生在*你的腳本裡面*，所以 Fiji 完全不知道，看起來可能像是當掉了。

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

你的腳本會拿到整張影像，是一個依 **T Z C Y X** 順序排列的陣列（看
`ctx.meta` 確認），大小最好在 1–2 GB 以內，而且在任何耗時的步驟（例如第一次下載模型）
之前，都應該先 `ctx.log`。

[下一步：不用 Fiji 也能測試 :material-arrow-right:](test-without-fiji.md){ .md-button }
