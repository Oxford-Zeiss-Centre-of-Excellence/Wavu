# 実際の画像

## やさしく言うと

*Blobs* は平らな画像 1 枚です。でも顕微鏡の画像は、たいてい **画像の束** です。
いくつかの色チャンネル、いくつかの焦点面（z スタック）、もしかすると
いくつかの時点もあります。Wavu はその **束全体** を 1 つの NumPy 配列として
スクリプトに渡し、ビューアーが知っていれば、どう積み重なっているかも教えて
くれます。スライドの箱を、並び順を書いたラベルと一緒に受け取るようなものです。

![画像の面の束：時間、z、チャンネル、そして y と x](../assets/img/axes.svg){ width="640" }

## 配列の形

=== "Fiji"

    軸はいつもこの順番で並び、長さ 1 の軸は省かれます。

    **T**（時間）· **Z**（面）· **C**（チャンネル）· **Y** · **X**、さらに
    RGB のカラー画像では最後に長さ 3 の軸 **S** が付きます。

    | Fiji の画像 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 2 次元のグレー画像 1 枚、512 × 512 | `(512, 512)` | `"YX"` |
    | 3 チャンネル | `(3, 512, 512)` | `"CYX"` |
    | 20 面の z スタック、2 チャンネル | `(20, 2, 512, 512)` | `"ZCYX"` |
    | RGB の写真 | `(512, 512, 3)` | `"YXS"` |

    つまり、`ZCYX` の画像で「すべての面のチャンネル 2」は `img[:, 1]` です。
    Fiji は 8-bit、16-bit、32-bit、RGB のピクセルをそのまま送ります。

=== "napari"

    選んだレイヤーのデータが、レイヤー自身の軸の順番のまま届きます。
    z スタックのレイヤーなら `(20, 512, 512)` です。napari はたいてい
    チャンネルごとに別のレイヤーとして開くので、ほしいチャンネルを選びます。

    | napari のレイヤー | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 2 次元のグレー画像 1 枚 | `(512, 512)` | `"YX"` |
    | 20 面の z スタック | `(20, 512, 512)` | レイヤーの軸ラベルが z, y, x なら `"ZYX"`、そうでなければなし |
    | RGB の写真 | `(512, 512, 3)` | `"YXS"` |

    **マルチスケール** のレイヤー（画像ピラミッド）は、最高解像度のレベルを
    送ります。2 次元と RGB のレイヤーには必ず軸の文字が付きます。それより
    大きいレイヤーに付くのは、OME-Zarr の読み込み機能が設定するように、
    napari の軸ラベルが単純な文字（t, z, c, y, x）のときだけです。なので、
    軸は `.get("axes")` で読み、`img.ndim` と `img.shape` も確認しましょう。

## ほかに受け取れるもの：`ctx.meta`

`ctx.meta["image"]` には、`"image"` 欄で選ばれた画像についてビューアーが
知っていることが入っています。

- `"axes"`：上で見た軸の文字（Fiji では常に。napari では 2 次元と RGB の
  レイヤー、そして軸ラベルが t/z/c/y/x の大きいレイヤーで）。
- `"pixel_um"`：わかっていれば、ピクセルサイズ（マイクロメートル）。Fiji では
  画像のキャリブレーションから、napari ではレイヤーの **scale** から
  （最後の 2 つの値が等しく、1 でないとき）。
- `"title"`：ウィンドウのタイトル（Fiji）またはレイヤー名（napari）。

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # ビューアーが教えなければ None
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

形を確認して分かりやすい `ValueError` を出すほうが、あとでコードが
クラッシュするより親切です。Fiji はその文をエラーウィンドウに、napari は
パネルのログと通知に表示します。

??? tip "軸の順：T C Z Y X がおすすめ（保存・受け渡し・計算）"

    Wavu は何も並べ替えません。Fiji は **T Z C Y X**（ImageJ のハイパースタックの順）で
    送り、napari はレイヤー自身の順で送り、Fiji は結果を自分の順で受け取ることを
    期待します。スクリプトの中では自由に選べます。おすすめは **T C Z Y X** です。
    層ごとの選択肢は次のとおりです。

    | 層 | おすすめ | 代わりの選択肢 | 代わりを選ぶのはこんなとき |
    |---|---|---|---|
    | **保存**（ディスク上のファイル） | **T C Z Y X**（または C Z Y X、Z Y X）の OME-Zarr | **T Z C Y X** の ImageJ TIFF | 主に Fiji で開く小さなデータ（ImageJ TIFF は自分の順でしか保存できません） |
    | **受け渡し**（Wavu ↔ スクリプト） | `run()` の最初で C 連続の **T C Z Y X** に変換し、返す前に元に戻す | Wavu が渡す順のまま（Fiji からは **T Z C Y X**） | 順が関係ない、面ごとの処理（フィルター、しきい値） |
    | **計算**（NumPy、PyTorch、GPU） | **T C Z Y X**：1 つの時点は `(C, Z, Y, X)`、バッチ軸を足すと PyTorch の `(N, C, D, H, W)` | GPU メモリの中だけで **channels last**（B Z Y X C）：`tensor.to(memory_format=torch.channels_last_3d)`。TensorFlow/Keras の既定 | 新しい NVIDIA GPU での混合精度の 3-D 畳み込み、Keras のモデル |

    なぜ T C Z Y X なのか。軸の順を左右するものは 4 つあり、この順はそのすべてに
    合っています。

    1. **顕微鏡。** カメラは一度に **Y × X** のフレームを 1 枚読み出し（いちばん
       速い）、ピエゾステージが **Z** を動き、フィルターやレーザーが **C** を
       切り替え、時間間隔 **T** がいちばん遅くなります。Y、X をいちばん内側に、
       その隣に Z を置くと、データを取得する順に沿い、3-D の体積がひとまとまりの
       ままになります（Z と C のループの順は装置によって違います）。
    2. **保存とチャンク。** NumPy と Zarr の配列は *C 連続* で、最後の軸が
       いちばん速く変わります。T C Z Y X なら、`(1, 1, 64, 512, 512)` のような
       チャンクは **1 つのチャンネル** のコンパクトな 3-D ブロックになるので、
       チャンネル 0（たとえば DAPI）だけを読むときはそのファイルだけを読みます。
       チャンネルが交互に並んでいると、読むたびに全チャンネルを取ってきます。そのため
       [OME-NGFF の仕様](https://ngff.openmicroscopy.org/0.4/#axes-md)
       は、時間、チャンネル、空間の順を求めています（バージョン 0.4 と 0.5。
       これをゆるめる提案 [RFC-3](https://ngff.openmicroscopy.org/rfc/3/index.html)
       はまだ審査中です）。Fiji、napari、Bio-Formats はどれもこれを読めます。
       ディスク上のデータは何十年も残りますが、GPU は数年ごとに変わります。
    3. **ディープラーニング。** `(C, Z, Y, X)` にバッチ軸を足すと、
       [PyTorch の `Conv3d`](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv3d.html)
       が期待する `(N, C, D, H, W)` そのものになります。C 連続の配列に
       `torch.from_numpy()` を使うとメモリを共有するので、何もコピーされません。
    4. **GPU。** NVIDIA の Tensor コアは、チャンネルがいちばん内側にあると
       （「channels last」）混合精度（FP16/BF16）の 3-D 畳み込みを速く実行
       できます。変換は **GPU メモリの中だけで**、重い層の直前に行います。形は
       `(N, C, D, H, W)` のままで、変わるのはストライドだけです。結果が GPU を
       出る前に、もう一度連続にしてください（`.contiguous()`）。チップの好みが
       ファイルに届くことはありません。

    スクリプトの中で、変換して元に戻す例です。

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
        axes = ctx.meta["image"].get("axes") or "YX"    # Fiji からは例えば "TZCYX" や "ZCYX"
        x, ours = to_tczyx(inputs["image"], axes)       # 例：(C, Z, Y, X)、"CZYX"
        # PyTorch：バッチ軸付きの 1 時点、コピーなし
        #   batch = torch.from_numpy(x)[None]           # "CZYX" なら (1, C, Z, Y, X)
        y = x * 2                                       # あなたの計算。出力も同じ並び
        return {"result": wavu.Image(back(y, ours, axes), axes=axes)}
    ```

    （軸が `S` で終わる RGB 画像はここでは扱いません。先にグレーに変換するか、
    色を分けてください。napari のレイヤーが `axes` なしで届いたら、その順を
    いちばん知っているのはあなたです。文字を自分で渡してください。）

## どれくらいから大きすぎる？

Wavu は、**メモリに余裕を持って収まる画像 1 枚での対話的な作業** のために
作られています。目安は **1〜2 GB** までです。小さい画像は 1 つの
メッセージで送られ、大きい画像はディスク上の一時的な TIFF ファイルを
経由します。あなたは何もしなくてかまいません。どちらの場合も
`inputs["image"]` は NumPy 配列です。この上限は Fiji でも napari でも
同じです。

!!! warning "napari：大きな遅延レイヤーはまるごと読み込まれます"
    napari は巨大な画像を遅延して（*dask* 配列として）表示し、画面に映る
    部分だけを読むことができます。Wavu にはそれができません。送る前に
    レイヤー全体をメモリに読み込むので、メモリに収まるレイヤー（切り抜き、
    1 チャンネル、解像度を下げたコピー）を選んでください。

それより大きいときは、OME-Zarr に変換して、スクリプトに少しずつ読ませて
ください。[ストリーム解析](../workflows/large-data.md) なら、ローカルの
コンピューターで約 50 GB まで扱えます。動きはしますが、Fiji や napari から
操作するのはおすすめしません。何百ものファイルを扱うときは
[バッチ処理](../workflows/batch.md) を見てください。約 50 GB を超えるときは、
バッチ処理や HPC のワークフローを使ってください。

## 最初の実行が遅い（ユーザーを安心させる方法） { #slow-first-runs-and-how-to-keep-users-calm }

*最初の* 実行が遅くなる理由は 2 つあり、どちらも一度だけです。

1. **環境が作られます。** pixi が `pixi.toml` に書かれたパッケージを
   ダウンロードします。PyTorch（Cellpose に必要）があると **1〜2 GB**、
   数分かかることもあります。その間、Fiji の Log または napari パネルの
   ログがそう伝えます。
2. **モデルの重みがダウンロードされます。** Cellpose などのツールは、
   初めて使うときに学習済みモデルをインターネットから取ってきます。これは
   *スクリプトの中で* 起きるので、ビューアーは何も知らず、固まったように
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

スクリプトは画像全体を配列 1 つで受け取ります（Fiji からは **T Z C Y X** の
順、napari からはレイヤー自身の順。確かめるには `ctx.meta` と形を見ます。OME-NGFF と PyTorch の
順である **T C Z Y X** に並べ替えることをおすすめします）。
どちらのビューアーでも大きさは 1〜2 GB くらいまでにし、最初の
モデルのダウンロードのような時間のかかる処理の前には `ctx.log` を書きましょう。

[次へ：コンテナとして共有する :material-arrow-right:](container.md){ .md-button }
