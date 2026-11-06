# 安装 wavu-napari

## 为什么需要 Wavu { #why-this-exists }

- **所有东西装在同一个环境里，迟早会出问题。** 用 `pip` 把一个 Cellpose 插件
  装进 napari 的环境，它可能会带进另一个版本的 PyTorch、NumPy 或 Qt；下一个
  插件又锁定别的版本，结果 napari 或同事的工具就启动不了。在同一个环境里混用
  `conda` 和 `pip`，只会更糟。
- **在 Fiji 里运行 Python 更麻烦。** Fiji 自带的脚本语言是 Jython（Python 2.7，
  没有 NumPy）。改用 PyImageJ 这类桥接工具，就得在每台电脑上手动对齐 Java、
  conda 和软件包的版本。
- **Wavu 的做法：** Fiji/napari 本身保持小巧干净，每个脚本都在**它自己的
  pixi 环境**里运行，由它自己的 `pixi.lock` 创建。脚本之间不共享软件包，所以
  不会互相破坏，也不会破坏 napari 或 Fiji；同一个文件夹在每台电脑上都会装出
  完全相同的环境。

## 用大白话说

在 napari 里，Wavu 是同一个厨房的**第二位服务员**。它是一个停靠在 napari
窗口侧边的面板：你选一个脚本文件夹、填好表单、按下 **Run**（运行），结果就会
以图层的形式出现。

这里有**两个食材柜**，把它们分开，就是全部的诀窍：

- **napari 的食材柜**里装的是 napari 本身、Qt 和 Wavu 面板。它很小，而且
  不会因为你添加脚本而改变。
- **每个脚本的食材柜**里装的是*那个*脚本需要的东西（Cellpose、PyTorch、
  scikit-image……），按照它文件夹里的 `pixi.toml` 建立。

所以给某个脚本安装 PyTorch，绝不会弄坏 napari；napari 升级，也绝不会弄坏
你的脚本。

```mermaid
flowchart LR
    subgraph NP["napari 的环境（轻量）"]
        N["napari<br/>+ Wavu 面板"]:::fiji
    end
    W["wavu-worker"]:::worker
    subgraph SE["脚本文件夹的环境"]
        S["script.py<br/>cellpose、torch…"]:::script
    end
    N -- "127.0.0.1 上的 HTTP" --> W --> S

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
    style NP fill:#f3e5f5,stroke:#6a1b9a
    style SE fill:#f3e5f5,stroke:#6a1b9a
```

## 你需要准备

- **pixi**，从 [pixi.sh](https://pixi.sh) 安装（一条命令；网页会显示适合
  你系统的那一条）。在新的终端里用 `pixi --version` 检查。
- **Git**，从 [git-scm.com](https://git-scm.com) 获取，用来下载 Wavu。

Python 和 napari 都不用你自己安装：pixi 会把两者都装好。

## 第 1 步：下载 Wavu

在你存放项目的文件夹里打开终端，运行：

```sh
git clone https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu.git
cd Wavu
```

## 第 2 步：启动 napari

```sh
pixi run -e napari napari
```

`-e napari` 会选用 Wavu 的 **napari 环境**：napari 加上 Wavu 面板。第一次
运行时，pixi 会下载它，需要几分钟，仅此一次。下次 napari 几秒内就能打开。
请始终在 `Wavu` 文件夹里用这条命令启动 napari；面板就是这样被找到的。

## 第 3 步：打开 Wavu 面板

在 napari 中选择 **Plugins › Run Python Script (Wavu)**（运行 Python 脚本）。
窗口侧边会停靠一个面板，里面有：

- 一个 **Script folder**（脚本文件夹）输入框，以及 **Start worker**（启动
  worker）和 **Connect to running worker**（连接到正在运行的 worker）两个按钮；
- 一个 **Remote / container**（远程／容器）复选框，用于在别处运行的
  worker（现在可以先不管它）；
- 一个 **Script** 列表和一张空白表单（worker 运行后才会填上）；
- **Run** 和 **Cancel**（取消）、一个进度条、一个 log 框，以及
  **Stop worker**（停止 worker）。

安装就这样完成了。

## 更新

在 `Wavu` 文件夹里运行 `git pull`，再用同一条命令重新启动 napari。如有需要，
pixi 会更新 napari 的环境。

## 也用 Fiji 吗？

同样的脚本文件夹在 Fiji 和 napari 里都能用。Fiji 这位服务员的安装方式不同
（一个 zip 文件，不用终端）：请看
[在 Fiji 中安装 Wavu](../fiji/install.md)。

## 一句话总结

clone Wavu、运行 `pixi run -e napari napari`，再打开
**Plugins › Run Python Script (Wavu)**：napari 有自己的小食材柜，每个脚本
也各自带着自己的。

[下一步：在 napari 中第一次运行 :material-arrow-right:](first-run.md){ .md-button }
