---
title: 首页
hide:
  - navigation
  - toc
---

# Wavu：在 Fiji/napari 里运行你的 Python

*Wavu* 是斐济语里的“**桥**”。它把你看图像用的 **Fiji** 或
**napari**，和 Cellpose、scikit-image 这些工具所在的 Python 连接起来。

想象一家餐厅。**Fiji/napari 是服务员**：它帮你点菜（一个只有几个输入框的对话框），
把你的图像作为**食材**送进厨房，再把菜端回你的桌上（新的图像、表格、轮廓）。
**worker 是门后的厨房**，而每道食谱都有**自己的厨具**，也就是它自己的锅、
刀和烤箱（Python 软件包），所以 Cellpose 的食谱绝不会借用（或弄坏）
模糊处理食谱的工具。同一道食谱，哪位服务员都能端上桌。

![服务员（前端）: wavu-fiji, wavu-napari → 厨房（后端）: wavu worker, 你的 script.py PARAMS + run(), 它自己的 pixi 环境 （厨具） — 可选：把整个厨房放进容器（Docker / Apptainer）](assets/img/home-model.svg){ width="1000" }

**一个脚本文件夹，Fiji 和 napari 都能用。**`script.py` 你只需写一次；Fiji 用户和
napari 用户都能运行它，每次都在该文件夹自己的环境中运行。

## 为什么需要 Wavu { #why-this-exists }

- **所有东西装在同一个环境里，迟早会出问题。** 用 `pip` 把一个 Cellpose 插件
  装进 napari 的环境，它可能会带进另一个版本的 PyTorch、NumPy 或 Qt；下一个
  插件又锁定别的版本，结果 napari 或同事的工具就启动不了。在同一个环境里混用
  `conda` 和 `pip`，只会更糟。
- **在 Fiji 里运行 Python 更麻烦。** Fiji 自带的脚本语言是 Jython（Python 2.7，
  没有 NumPy）。改用 PyImageJ 这类桥接工具，就得在每台电脑上手动对齐 Java、
  conda 和软件包的版本。
- **Wavu 的做法：**Fiji/napari 本身保持小巧干净，每个脚本都在**它自己的
  pixi 环境**里运行，由它自己的 `pixi.lock` 创建。脚本之间不共享软件包，所以
  不会互相破坏，也不会破坏 napari 或 Fiji；同一个文件夹在每台电脑上都会装出
  完全相同的环境。

## 不只是桥：用脚本跑完整个分析

Wavu 也是你自己的脚本可以调用的一个**函数**。Groovy 脚本、ImageJ 宏或
Python 笔记本可以逐个处理整个文件夹，自己完成原生步骤（打开、预处理、测量、
保存），只把最繁重的步骤（例如 Cellpose）交给 Wavu；Wavu 在它自己的环境里
运行这一步，再把结果交回给脚本。一个脚本、整个文件夹，每次都一样。

[脚本化工作流 :material-arrow-right:](workflows/index.md){ .md-button .md-button--primary }

## 你想从哪里开始？

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **理解工作模式**

    ---

    服务员、厨房、厨具：什么在哪里运行，以及为什么你的包永远不会互相
    冲突。

    [:octicons-arrow-right-24: 工作原理](model/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **编写脚本**

    ---

    把你的笔记本变成一个菜单项，先写测试。点一下就能拿到现成的模板：

    [在 VS Code 中打开模板](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: 获取模板](write/get-the-template.md)

-   :material-microscope:{ .lg .middle } **在 Fiji 中使用**

    ---

    安装 wavu-fiji，用示例图像运行你的第一个脚本，再用一个 zip 文件把工具
    分享给实验室。

    [:octicons-arrow-right-24: wavu-fiji](fiji/install.md)

-   :material-layers-outline:{ .lg .middle } **在 napari 中使用**

    ---

    带着 Wavu 面板启动 napari；结果会以 Image、Labels 和 Shapes 图层返回。

    [:octicons-arrow-right-24: wavu-napari](napari/install.md)

</div>

## 须知

- **数据量多大？** 交互使用指的是一张放得进内存的图像，大约 1–2 GB。
  改用分块、流式的处理（OME-Zarr），Wavu 可以在本机处理约 50 GB 以内的数据，
  但有**一个重大限制**：Fiji 和 napari 是以画布为核心、假设数据都在内存里的
  软件，流式处理进行时它们只看得到小小的预览或最后的结果，运行也慢，并不是
  推荐用来驱动流式分析的地方。超过约 50 GB，请改用批处理或 HPC 流程。
- **每个脚本都有自己的环境**，所以用 PyTorch 的脚本和只用 NumPy 的脚本
  永远不会互相冲突。
- **好奇它是怎么实现的？**[架构](model/architecture.md)页面介绍了
  worker、它的 HTTP 协议，以及 Fiji/napari 如何启动它。

想了解从想法到发布 Fiji 插件的每个细节？请阅读
[GitHub 上的完整指南](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md)（英文）。
