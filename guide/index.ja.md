---
title: Wavu
hide:
  - navigation
  - toc
---

# Wavu: あなたの Python を Fiji の中で

*Wavu* はフィジー語で **橋** という意味です。画像を見る場所である Fiji と、
Cellpose や scikit-image などのツールがある Python をつなぎます。

レストランを思い浮かべてください。**Fiji はウェイター**です。注文
（いくつかの入力欄があるダイアログ）を受け取り、料理（新しい画像、表、
輪郭）をテーブルまで運んできます。**ワーカーはドアの向こうの厨房**です。
そしてレシピごとに **専用の食材庫** があるので、Cellpose のレシピがぼかしの
レシピの材料を借りたり、壊したりすることはありません。

```mermaid
flowchart LR
    subgraph FIJI["Fiji（ウェイター）"]
        D["ダイアログ<br/>PARAMS から作られる"]:::fiji
        R["結果<br/>画像 · 表 · ROI"]:::fiji
    end
    subgraph PY["ワーカー（厨房）"]
        S["あなたの script.py"]:::script
    end
    E[("専用の pixi 環境<br/>（食材庫）")]:::env

    D -- "あなたの注文" --> S
    S -.- E
    S -- "料理 + リアルタイムの Log" --> R

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef env    fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    style FIJI fill:#f5f9ff,stroke:#90caf9
    style PY   fill:#f6fbf6,stroke:#a5d6a7
```

## 何をしたいですか？

<div class="grid cards" markdown>

-   :material-play-circle-outline:{ .lg .middle } **スクリプトを使う**

    ---

    Fiji に Wavu をインストールして、サンプル画像で最初の Python
    スクリプトを実行します。ターミナルは不要です。

    [:octicons-arrow-right-24: ここから始める](start/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **スクリプトを書く**

    ---

    ノートブックを Fiji のメニュー項目に変えます。すぐに使えるひな形は
    ワンクリックで手に入ります。

    [VS Code でテンプレートを開く](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: しくみを見る](write/get-the-template.md)

-   :material-share-variant-outline:{ .lg .middle } **スクリプトを共有する**

    ---

    ツールを zip ファイル 1 つにして、研究室全体に配れます。世界への公開は
    任意です。

    [:octicons-arrow-right-24: 研究室で共有する](share/with-your-lab.md)

</div>

## 知っておくと良いこと

- **小さめのデータを対話的に。** メモリに収まる画像 1 枚、だいたい 1〜2 GB
  までが対象です。巨大なデータには、バッチ処理や HPC のワークフローを
  使ってください。
- **スクリプトごとに専用の環境があります。** そのため、PyTorch を使う
  スクリプトと NumPy だけのスクリプトがぶつかることはありません。

アイデアからプラグインの公開まで、すべての詳細を知りたい方は
[GitHub の完全ガイド](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md)（英語）をどうぞ。
