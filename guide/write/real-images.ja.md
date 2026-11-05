# 実際の画像

## やさしく言うと

*Blobs* は平らな画像 1 枚です。でも顕微鏡の画像は、たいてい **画像の束** です。
いくつかの色チャンネル、いくつかの焦点面（z スタック）、もしかすると
いくつかの時点もあります。Wavu はその **束全体** を 1 つの NumPy 配列として
スクリプトに渡し、どう積み重なっているかを教えてくれます。スライドの箱を、
並び順を書いたラベルと一緒に受け取るようなものです。

![画像の面の束：時間、z、チャンネル、そして y と x](../assets/img/axes.svg){ width="640" }

## 配列の形

軸はいつもこの順番で並び、長さ 1 の軸は省かれます。

**T**（時間）· **Z**（面）· **C**（チャンネル）· **Y** · **X**、さらに RGB の
カラー画像では最後に長さ 3 の軸 **S** が付きます。

| Fiji の画像 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
|---|---|---|
| 2 次元のグレー画像 1 枚、512 × 512 | `(512, 512)` | `"YX"` |
| 3 チャンネル | `(3, 512, 512)` | `"CYX"` |
| 20 面の z スタック、2 チャンネル | `(20, 2, 512, 512)` | `"ZCYX"` |
| RGB の写真 | `(512, 512, 3)` | `"YXS"` |

つまり、`ZCYX` の画像で「すべての面のチャンネル 2」は `img[:, 1]` です。
Fiji は 8-bit、16-bit、32-bit、RGB のピクセルをそのまま送ります。

## ほかに受け取れるもの：`ctx.meta`

`ctx.meta["image"]` には、`"image"` 欄で選ばれた画像について Fiji が
知っていることが入っています。

- `"axes"`：上で見た軸の文字。
- `"pixel_um"`：画像がキャリブレーションされていれば、ピクセルサイズ
  （マイクロメートル）。
- `"title"`：ウィンドウのタイトル。

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"]["axes"]
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel (Image › Duplicate…)")
    ...
```

形を確認して分かりやすい `ValueError` を出すほうが、あとでコードが
クラッシュするより親切です。Fiji はその文をエラーウィンドウに表示します。

## どれくらいから大きすぎる？

Wavu は、**メモリに余裕を持って収まる画像 1 枚での対話的な作業** のために
作られています。目安は **1〜2 GB** までです。小さい画像は 1 つの
メッセージで送られ、大きい画像はディスク上の一時的な TIFF ファイルを
経由します。あなたは何もしなくてかまいません。どちらの場合も
`inputs["image"]` は NumPy 配列です。

それより大きいとき、あるいは何百ものファイルを扱うときは、Wavu は向いて
いません。OME-Zarr に変換して、バッチ処理や HPC のワークフローを使って
ください。

## 最初の実行が遅い（ユーザーを安心させる方法） { #slow-first-runs-and-how-to-keep-users-calm }

*最初の* 実行が遅くなる理由は 2 つあり、どちらも一度だけです。

1. **環境が作られます。** pixi が `pixi.toml` に書かれたパッケージを
   ダウンロードします。PyTorch（Cellpose に必要）があると **1〜2 GB**、
   数分かかることもあります。その間、Fiji の Log がそう伝えます。
2. **モデルの重みがダウンロードされます。** Cellpose などのツールは、
   初めて使うときに学習済みモデルをインターネットから取ってきます。これは
   *スクリプトの中で* 起きるので、Fiji は何も知らず、固まったように
   見えることがあります。

**時間のかかる処理の前には必ずログを書き**、何が起きているかをユーザーに
伝えましょう。

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "動く Cellpose のセットアップ"
    Wavu リポジトリには、核のための完全な Cellpose スクリプトがあります。
    PyTorch、Cellpose、任意の NVIDIA GPU 設定を含む `pixi.toml` 付きです：
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei)。
    その `[dependencies]` と `[pypi-dependencies]` の行を、自分の
    `pixi.toml` にコピーしてください。Apple シリコンの Mac は、何もしなくても
    GPU を使います。

## ひとことで言うと

スクリプトは画像全体を **T Z C Y X** の順の配列 1 つで受け取ります（確かめる
には `ctx.meta` を読みます）。大きさは 1〜2 GB くらいまでにし、最初の
モデルのダウンロードのような時間のかかる処理の前には `ctx.log` を書きましょう。

[次へ：研究室で共有する :material-arrow-right:](../share/with-your-lab.md){ .md-button }
