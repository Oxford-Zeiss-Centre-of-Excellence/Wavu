# 名詞解釋

## 用白話說

每個領域都有自己的術語。這裡用一句白話解釋每個 Wavu 用語，適合的地方再搭配餐廳的比喻。

![餐廳比喻：Fiji 是服務生，worker 是廚房，每道食譜都有自己的食材櫃](../assets/img/restaurant.svg){ width="560" }

## 用語

**Fiji**
:   你已經在用的影像分析程式（加上外掛的 ImageJ）。在 Wavu 裡它是*服務生*：接收對話框的點單，送回結果。

**Wavu**
:   斐濟語的「橋」。指 Fiji 裡的選單項目，加上一個小小的 Python 輔助程式，把 Fiji 和你的 Python 腳本連起來。

**腳本（Script）**
:   一個含有 `PARAMS` 和 `run` 函式的 `.py` 檔。也就是*食譜*。

**腳本資料夾（Script folder）**
:   一個含有 `pixi.toml` 和一個或多個腳本的資料夾。就是你在 **Run Python Script** 裡挑選的東西。

**PARAMS**
:   腳本開頭那份描述對話框欄位的清單。也就是*菜單*。

**`run(ctx, inputs, params)`**
:   Wavu 呼叫的函式。`inputs` 裝著影像，`params` 裝著其他設定，`ctx` 則是通回 Fiji 的那條線。

**ctx**
:   「context」（情境）的縮寫：`ctx.log`、`ctx.progress`、`ctx.cancelled` 等等。

**Worker**
:   在*你自己*電腦上的一個小 Python 程式，當 Fiji 要求時就執行你的腳本。也就是*廚房*。它只在你自己的電腦上和 Fiji 溝通。

**環境（Environment）**
:   一個專屬資料夾，裡面放著一個確定版本的 Python，加上一個腳本需要的套件，存放在腳本資料夾裡的 `.pixi`。也就是*食材櫃*。

**pixi**
:   一個免費工具，負責建立環境和下載套件，是 conda 的現代替代品。Wavu 會替你把它抓下來。

**`pixi.toml`**
:   *購物清單*：腳本需要哪些套件。

**鎖定檔（Lock file，`pixi.lock`）**
:   *收據*：每個套件的精確版本。分享它，就代表每個人都會得到相同的環境。

**conda-forge / PyPI**
:   兩間放 Python 套件的大型線上「商店」。pixi 預設使用 conda-forge；PyPI 則是 `pip` 買東西的地方。

**NumPy 陣列（NumPy array）**
:   Python 的數字網格；你的腳本就是用它來接收和回傳影像。

**標籤影像（Labels，label image）**
:   一種影像，每個物件都有自己的整數編號（1、2、3 …），背景是 0。Fiji 會用隨機的鮮豔顏色來顯示它。

**ROI**
:   「Region of interest」（感興趣區域）：畫在影像上的一個輪廓。Fiji 把它們存在 **ROI Manager** 裡；*RoiSet* 則是一個裝滿 ROI 的 zip 檔。

**合作式取消（Cooperative cancel）**
:   按 Esc 會舉起一面旗子；你的腳本檢查到它，就自己停下來。

**中斷點（Breakpoint）**
:   VS Code 裡的一個紅點，執行中的腳本會在那裡暫停，讓你看看裡面。

**標籤／發布版本（Tag / release）**
:   貼在程式碼上的版本標記，例如 `v1.0.0`，以及 GitHub 為它產生的下載頁面。

**CI**
:   「Continuous integration」（持續整合）：當你推送標籤時，替你測試並打包程式碼的 GitHub 機器人。選用。

**更新站點（Update site）**
:   你在 **Help › Update…** 裡勾選的 Fiji 下載來源，用來安裝和更新外掛。

## 一句話總結

Fiji 是服務生，worker 是廚房，你的腳本是食譜，它的 pixi 環境是食材櫃，而 `pixi.lock` 是收據。
