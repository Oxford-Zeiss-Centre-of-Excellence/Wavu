# 术语表

## 用大白话说

每个领域都有自己的行话。这里用一句大白话解释每个 Wavu 术语，合适的地方再配上餐厅的比喻。

![餐厅比喻：Fiji 是服务员，worker 是厨房，每道食谱都有自己的厨具](../assets/img/restaurant.svg){ width="560" }

## 术语

**Fiji**
:   你已经在用的图像分析软件（带插件的 ImageJ）。在 Wavu 里它是*服务员*：从对话框接单，把结果端回来。

**Wavu**
:   斐济语里的“桥”。指 Fiji 里的菜单项，加上一个小小的 Python 辅助程序，把 Fiji 和你的 Python 脚本连起来。

**脚本（Script）**
:   一个包含 `PARAMS` 和 `run` 函数的 `.py` 文件。也就是*食谱*。

**脚本文件夹（Script folder）**
:   一个包含 `pixi.toml` 和一个或多个脚本的文件夹。就是你在 **Run Python Script** 里选的那个。

**PARAMS**
:   脚本开头那份描述对话框字段的列表。也就是*菜单*。

**`run(ctx, inputs, params)`**
:   Wavu 调用的函数。`inputs` 装着图像，`params` 装着其他设置，`ctx` 是通回 Fiji 的那条线。

**ctx**
:   “context”（上下文）的缩写：`ctx.log`、`ctx.progress`、`ctx.cancelled` 等等。

**Worker**
:   在*你自己*电脑上的一个小 Python 程序，Fiji 一发话它就运行你的脚本。也就是*厨房*。它只在你自己的电脑上和 Fiji 通信。

**环境（Environment）**
:   一个专用文件夹，里面有一个确定版本的 Python，加上某个脚本需要的软件包，存放在脚本文件夹里的 `.pixi` 中。也就是食谱的*厨具*：它自己的锅、刀和烤箱。

**pixi**
:   一个免费工具，负责搭建环境和下载软件包，是 conda 的现代替代品。Wavu 会帮你把它下载下来。

**`pixi.toml`**
:   *厨具清单*：脚本需要哪些包。

**锁文件（Lock file，`pixi.lock`）**
:   厨具的*收据*：每个包的精确版本。分享它，就意味着每个人都得到相同的环境。

**conda-forge / PyPI**
:   两家卖 Python 软件包的大型在线“商店”。pixi 默认用 conda-forge；PyPI 则是 `pip` 购物的地方。

**NumPy 数组（NumPy array）**
:   Python 的数字网格；你的脚本就是用它来接收和返回图像的。

**标签图像（Labels，label image）**
:   一种图像，每个对象都有自己的整数编号（1、2、3 …），背景是 0。Fiji 会用随机的鲜艳颜色显示它。

**ROI**
:   “Region of interest”（感兴趣区域）：画在图像上的一个轮廓。Fiji 把它们放在 **ROI Manager** 里；*RoiSet* 则是一个装满 ROI 的 zip 文件。

**协作式取消（Cooperative cancel）**
:   按 Esc 会竖起一面旗子；你的脚本检查到它，就自己停下来。

**断点（Breakpoint）**
:   VS Code 里的一个红点，运行中的脚本会在那里暂停，让你看看里面。

**标签／发布版本（Tag / release）**
:   贴在代码上的版本标记，比如 `v1.0.0`，以及 GitHub 为它生成的下载页面。

**CI**
:   “Continuous integration”（持续集成）：你推送标签时，帮你测试并打包代码的 GitHub 机器人。可选。

**更新站点（Update site）**
:   你在 **Help › Update…** 里勾选的 Fiji 下载源，用来安装和更新插件。

## 一句话总结

Fiji 是服务员，worker 是厨房，你的脚本是食谱，你的图像是食材，它的 pixi 环境是厨具，`pixi.lock` 是收据。
