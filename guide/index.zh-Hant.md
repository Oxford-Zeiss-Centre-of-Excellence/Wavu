---
title: 首頁
hide:
  - navigation
  - toc
---

# Wavu：讓你的 Python 在 Fiji/napari 裡執行

*Wavu* 是斐濟語的「**橋**」。它把你看影像用的 **Fiji** 或
**napari**，和 Cellpose、scikit-image 這些工具所在的 Python 連在一起。

想像一間餐廳。**Fiji/napari 是服務生**：它幫你點餐（一個只有幾個欄位的對話框），
把你的影像當作**食材**送進廚房，再把餐點端回你的桌上（新的影像、表格、輪廓）。
**worker 是門後的廚房**，而每道食譜都有**自己的廚具**，也就是它自己的鍋子、
刀具和烤箱（Python 套件），所以 Cellpose 的食譜永遠不會借用（或弄壞）
模糊處理食譜的工具。同一道食譜，哪一位服務生都能端上桌。

![服務生（前端）: wavu-fiji, wavu-napari → 廚房（後端）: wavu worker, 你的 script.py PARAMS + run(), 它自己的 pixi 環境 （廚具） — 可選：把整個廚房放進容器（Docker / Apptainer）](assets/img/home-model.svg){ width="1000" }

**一個腳本資料夾，Fiji 和 napari 都能用。**`script.py` 你只要寫一次；Fiji 使用者和
napari 使用者都能執行它，每次都在該資料夾自己的環境中執行。

## 為什麼需要 Wavu { #why-this-exists }

- **所有東西裝在同一個環境，遲早會壞。** 用 `pip` 把一個 Cellpose 外掛裝進
  napari 的環境，它可能會帶進另一個版本的 PyTorch、NumPy 或 Qt；下一個外掛
  又鎖定別的版本，結果 napari 或同事的工具就打不開了。在同一個環境裡混用
  `conda` 和 `pip`，只會更糟。
- **在 Fiji 裡跑 Python 更麻煩。** Fiji 內建的腳本語言是 Jython（Python 2.7，
  沒有 NumPy）。改用 PyImageJ 這類橋接工具，就得在每台電腦上手動對齊 Java、
  conda 和套件的版本。
- **Wavu 的做法：**Fiji/napari 本身保持小而乾淨，每個腳本都在**它自己的
  pixi 環境**裡執行，由它自己的 `pixi.lock` 建立。腳本之間不共用套件，所以
  不會弄壞彼此，也不會弄壞 napari 或 Fiji；同一個資料夾在每台電腦上都會裝出
  一模一樣的環境。

## 不只是橋：用腳本跑完整個分析

Wavu 也是你自己的腳本可以呼叫的一個**函式**。Groovy 腳本、ImageJ 巨集或
Python 筆記本可以逐一處理整個資料夾，自己完成原生步驟（開啟、前處理、測量、
儲存），只把最吃重的步驟（例如 Cellpose）交給 Wavu；Wavu 在它自己的環境裡
執行這一步，再把結果交回給腳本。一個腳本、整個資料夾，每次都一樣。

[腳本化工作流程 :material-arrow-right:](workflows/index.md){ .md-button .md-button--primary }

## 你想從哪裡開始？

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **了解運作模式**

    ---

    服務生、廚房、廚具：什麼在哪裡執行，以及為什麼你的套件永遠不會互相
    衝突。

    [:octicons-arrow-right-24: 運作原理](model/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **撰寫腳本**

    ---

    把你的筆記本變成一個選單項目，先寫測試。按一下就能拿到現成的範本：

    [在 VS Code 中開啟範本](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: 取得範本](write/get-the-template.md)

-   :material-microscope:{ .lg .middle } **在 Fiji 中使用**

    ---

    安裝 wavu-fiji，用範例影像執行你的第一個腳本，再用一個 zip 檔把工具
    分享給實驗室。

    [:octicons-arrow-right-24: wavu-fiji](fiji/install.md)

-   :material-layers-outline:{ .lg .middle } **在 napari 中使用**

    ---

    帶著 Wavu 面板啟動 napari；結果會以 Image、Labels 和 Shapes 圖層回來。

    [:octicons-arrow-right-24: wavu-napari](napari/install.md)

</div>

## 先知道這些

- **資料量多大？** 互動使用指的是一張放得進記憶體的影像，大約 1–2 GB。
  改用分塊、串流的處理（OME-Zarr），Wavu 可以在本機處理約 50 GB 以內的資料，
  但有**一個重大限制**：Fiji 和 napari 是以畫布為核心、假設資料都在記憶體裡的
  軟體，串流進行時它們只看得到小小的預覽或最後的結果，運作也慢，並不是建議
  用來驅動串流分析的地方。超過約 50 GB，請改用批次或 HPC 流程。
- **每個腳本都有自己的環境**，所以用 PyTorch 的腳本和只用 NumPy 的腳本
  永遠不會打架。
- **好奇它是怎麼做出來的？**[架構](model/architecture.md)頁面說明了
  worker、它的 HTTP 協定，以及 Fiji/napari 如何啟動它。

想知道從構想到發布 Fiji 外掛的每個細節？請看
[GitHub 上的完整指南](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md)（英文）。
