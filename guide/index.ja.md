---
title: ホーム
hide:
  - navigation
  - toc
---

# Wavu: あなたの Python を、画像ビューアーの中で

*Wavu* はフィジー語で **橋** という意味です。画像を見る場所であるビューアー、
つまり **Fiji** や **napari** と、Cellpose や scikit-image などのツールが
ある Python をつなぎます。

レストランを思い浮かべてください。**ビューアーはウェイター**です。注文
（いくつかの入力欄があるダイアログ）を受け取り、あなたの画像を **食材** として
厨房に運び、料理（新しい画像、表、輪郭）をテーブルまで運んできます。
**ワーカーはドアの向こうの厨房**です。そしてレシピごとに **専用の調理器具**、
つまり専用の鍋や包丁やオーブン（Python パッケージ）があるので、Cellpose の
レシピがぼかしのレシピの道具を借りたり、壊したりすることはありません。同じレシピを、
どちらのウェイターでも出せます。

![ウェイター（フロントエンド）: wavu-fiji, wavu-napari → 厨房（バックエンド）: wavu ワーカー, あなたの script.py PARAMS + run(), 専用の pixi 環境 （調理器具） — 任意：厨房ごとコンテナーに入れる（Docker / Apptainer）](assets/img/home-model.svg){ width="1000" }

**スクリプトフォルダーは 1 つ、ビューアーは 2 つ。** `script.py` は一度
書くだけです。Fiji のユーザーも napari のユーザーもそれを実行でき、毎回
そのフォルダー専用の環境で動きます。

## なぜ Wavu があるのか { #why-this-exists }

- **何でも 1 つの環境に入れると壊れます。** napari の環境に Cellpose の
  プラグインを `pip install` すると、別のバージョンの PyTorch・NumPy・Qt が
  入ることがあります。次のプラグインはまた別のバージョンを固定し、napari や
  同僚のツールが起動しなくなります。1 つの環境で `conda` と `pip` を混ぜると、
  さらに悪化します。
- **Fiji の中の Python はもっと大変です。** Fiji 標準のスクリプト言語は
  Jython（Python 2.7、NumPy なし）です。PyImageJ のような橋渡しを使うと、
  Java・conda・パッケージのバージョンをマシンごとに手で合わせる必要があります。
- **Wavu の答え：** ビューアーは小さくきれいなまま。各スクリプトは自分の
  `pixi.lock` から作られた**専用の pixi 環境**で動きます。スクリプト同士は
  パッケージを共有しないので、互いにも napari にも Fiji にも影響せず、同じ
  フォルダーはどのコンピューターでも同じようにインストールされます。

## 橋だけではありません：解析全体をスクリプトで

Wavu は、あなた自身のスクリプトから呼べる **関数呼び出し** でもあります。
Groovy スクリプト、ImageJ マクロ、Python ノートブックがフォルダーを順に
処理し、ネイティブな手順（開く、前処理、測定、保存）は自分で行い、Cellpose の
ような重い手順だけを Wavu に渡します。Wavu はそれを専用の環境で動かし、結果を
スクリプトに返します。スクリプト 1 つでフォルダー全体を、毎回同じように。

[スクリプトによるワークフロー :material-arrow-right:](workflows/index.md){ .md-button .md-button--primary }

## どこから始めますか？

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **しくみを理解する**

    ---

    ウェイター、厨房、調理器具。何がどこで動くのか、なぜパッケージが
    ぶつからないのかを説明します。

    [:octicons-arrow-right-24: しくみ](model/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **スクリプトを書く**

    ---

    ノートブックをメニュー項目に変えます。テストから始めましょう。
    すぐに使えるひな形はワンクリックで手に入ります。

    [VS Code でテンプレートを開く](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: テンプレートを入手する](write/get-the-template.md)

-   :material-microscope:{ .lg .middle } **Fiji で使う**

    ---

    wavu-fiji をインストールし、サンプル画像で最初のスクリプトを実行して、
    ツールを zip ファイル 1 つで研究室と共有します。

    [:octicons-arrow-right-24: wavu-fiji](fiji/install.md)

-   :material-layers-outline:{ .lg .middle } **napari で使う**

    ---

    Wavu パネル付きで napari を起動します。結果は Image、Labels、Shapes
    レイヤーとして戻ってきます。

    [:octicons-arrow-right-24: wavu-napari](napari/install.md)

</div>

## 知っておくと良いこと

- **どのくらいのデータまで？** 対話的な利用は、メモリーに収まる 1 枚の
  画像（およそ 1〜2 GB）が目安です。チャンク単位のストリーム処理（OME-Zarr）
  なら、ローカルのコンピューターで約 50 GB まで扱えますが、**大きな注意点**
  があります。Fiji と napari はメモリー上のデータを前提にしたキャンバス型の
  ビューアーなので、ストリーム中は小さなプレビューか最終結果しか見えず、
  動作も遅く、ストリームを操作する場所としてはおすすめしません。約 50 GB を
  超える場合は、バッチ処理や HPC のパイプラインを使ってください。
- **スクリプトごとに専用の環境があります。** そのため、PyTorch を使う
  スクリプトと NumPy だけのスクリプトがぶつかることはありません。
- **どう作られているか気になりますか？** [アーキテクチャ](model/architecture.md)
  のページで、ワーカー、その HTTP プロトコル、ビューアーがワーカーを
  起動する方法を説明しています。

アイデアから Fiji プラグインの公開まで、すべての詳細を知りたい方は
[GitHub の完全ガイド](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md)（英語）をどうぞ。
