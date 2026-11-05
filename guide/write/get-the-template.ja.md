# テンプレートを手に入れる

[VS Code でテンプレートを開く](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }
[ZIP をダウンロード](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu-Script-Template/archive/refs/heads/main.zip){ .md-button }
[GitHub でこのテンプレートを使う](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu-Script-Template/generate){ .md-button }

## やさしく言うと

白紙からレシピカードを書く人はいません。**テンプレート** は、完成して
ちゃんと動くレシピ（[最初の実行](../start/first-run.md) のぼかし）で、
これをコピーしてから書き換えます。編集するのは `script.py` という 1 つの
ファイルだけです。無料のコードエディター
[VS Code](https://code.visualstudio.com) で編集し、すぐに Fiji から試せます。

```mermaid
flowchart LR
    T["テンプレート<br/>（ワンクリック）"]:::env
    V["VS Code で script.py を<br/>編集して保存"]:::script
    S["Fiji: Stop Worker"]:::fiji
    R["Fiji: Run Python Script"]:::fiji
    T --> V --> S --> R
    R -- "どこかを変える" --> V

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef env    fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
```

## クリックした後に起きること

1. ブラウザーが **Visual Studio Code を開くか** を聞いてきます。許可します。
2. VS Code が新しいフォルダーを **どこに保存するか** を聞いてきます。
   *ドキュメント* などを選びます。
3. フォルダーが VS Code で開き、左のファイル一覧に `script.py` が
   見えます。VS Code が Python 拡張機能を勧めてきたら、**Install** を
   クリックします。

これには **VS Code** と **Git** のインストールが必要です。何も起きない
場合は **ZIP をダウンロード** を使って解凍し、VS Code で
**File › Open Folder…**（フォルダーを開く）を選んでください。

![Visual Studio Code を開くか聞いてくるブラウザー](../assets/shots/08-vscode-browser-prompt.png)

![VS Code で開いたテンプレートフォルダー、script.py が見えている](../assets/shots/09-vscode-template-open.png)

*GitHub でこのテンプレートを使う* は、代わりにあなた専用のオンラインの
コピーを作ります。あとで [世界と共有](../share/with-the-world.md) したく
なったときに便利です。

## フォルダーの中身

| ファイル | 何か |
|---|---|
| `script.py` | **あなたのレシピ。** `PARAMS`（ダイアログ）と `run`（処理）。 |
| `pixi.toml` | このスクリプトの食材庫の買い物リスト。 |
| `test_script.py` | Fiji なしで動くチェック（[任意](test-without-fiji.md)）。 |
| `.vscode/` | [VS Code でのデバッグ](../help/debug-in-vscode.md) をワンクリックにします。 |
| `README.md`, `.github/` | メモと、自動リリース（[上級](../share/with-the-world.md)）。 |

## いつもの流れ

1. VS Code で `script.py` を **編集** して **保存** します
   （++ctrl+s++、Mac なら ++cmd+s++）。
2. Fiji で **Plugins › Wavu › Stop Worker** を選びます。
3. **Plugins › Wavu › Run Python Script** を選び、フォルダーを選びます。

!!! warning "なぜ Stop Worker？"
    厨房は開店するときにレシピを読みます。前回の実行から開いたままだと、
    *古い* レシピで料理を続けてしまいます。**Stop Worker** で厨房を閉めれば、
    次の実行で保存した変更が読み込まれます。かかるのは 1 秒ほどで、
    食材庫はそろったままです。

## パッケージを追加する { #adding-a-package }

scikit-image が必要ですか？ `pixi.toml` を開き、`[dependencies]` の下に
1 行足します。

```toml
[dependencies]
python = ">=3.10,<3.14"
numpy = ">=1.24"
scipy = ">=1.10"
scikit-image = "*"     # <- 新しい行："*" はどのバージョンでもよいという意味
```

保存して **Stop Worker** し、もう一度実行します。Wavu が新しい行に気づき、
pixi がパッケージを取ってきます（Log に表示されます）。PyPI（`pip` の世界）
にしかないパッケージは、代わりに `[pypi-dependencies]` の下に書きます。

??? note "ターミナルのほうが好きですか？"
    次のコマンドは、ボタンと同じことをターミナルで行います。

    ```sh
    git clone https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu-Script-Template.git my-analysis
    cd my-analysis
    pixi add scikit-image
    ```

    `pixi add` は `pixi.toml` を代わりに書き換えてくれます。ターミナルで
    `pixi` を使うには、[pixi.sh](https://pixi.sh) からインストールして
    ください。Fiji がダウンロードしたものは、ターミナルからは見えません。

## ひとことで言うと

ワンクリックで動くスクリプトフォルダーを手に入れ、VS Code で `script.py`
を編集し、変更を試すたびに Fiji で **Stop Worker** と
**Run Python Script** を実行します。

[次へ：ノートブックから Wavu へ :material-arrow-right:](from-notebook.md){ .md-button }
