
LOC-FLOW 是一个广泛使用的地震目录处理工具。但在实际使用中，它的一些操作流程确实不够方便，比如得手动去改各种配置文件，中间结果文件也散得到处都是。

**初衷与尝试：**
为了改善这个状况，我之前尝试着手，想给 LOC-FLOW 的一部分常用功能做一个图形界面 (GUI)，并且把生成的中间结果统一放到一个地方。

**问题与后续规划：**
但在开发做到处理 "REAL" 数据那部分时，我逐渐发现，单纯做成桌面 GUI 可能不是最优解。它在操作灵活性上会有一些限制，而且考虑到很多研究数据都是放在服务器上处理的，纯 GUI 在远程访问或数据可视化加载上可能会遇到问题。

基于这些考虑，我打算调整一下后续的开发思路：

1.  可能会转向做 **Web UI**，这样远程使用和共享会更方便。
2.  或者看看能不能在现在的 PyQt 框架里，加入直接连接服务器跑 **Jupyter 代码**处理数据的功能。
3.  另外，现在的 PyQt5 从性能和界面效果上看，确实有点落伍了，如果以后要继续做 UI，可能会考虑用 **PyQt6 加一些新的 UI 库**（比如 QtFluentWidgets）来重构。

**关于当前仓库内容：**
所以现在传上来的这个，就是当时**写到一半，但没有继续下去的 GUI 版本**。虽然没做完，但里面记录了我当时的实现思路和一些代码片段。上传主要是为了**保留这个过程**，以后新项目需要的时候，可以回来**参考一下**或者直接复用一些代码。

---

LOC-FLOW is a widely used tool for processing earthquake catalogs. However, its current usage can be inconvenient, often requiring manual modification of configuration files and resulting in scattered intermediate output files.

**Initial Approach & Goals:**
To improve usability, I started an attempt to build a Graphical User Interface (GUI) for some of LOC-FLOW's frequently used functions, aiming to also standardize the location of generated intermediate files.

**Challenges and Plans:**
However, while developing the "REAL" data processing module, I began to realize that a pure desktop GUI might not be the best solution. It can introduce limitations in operational flexibility, and considering that much of the relevant data is processed on servers, a pure GUI might face issues with remote access or data visualization loading.

Based on these considerations, I plan to adjust the future development approach:

1.  I might pivot towards building a **Web UI**, which would be more convenient for remote access and collaboration.
2.  Alternatively, I could explore adding functionality within the current PyQt framework to directly run **Jupyter code on a remote server** for data processing.
3.  Furthermore, given that PyQt5 is showing its age in terms of performance and modern aesthetics, any future UI development might consider a refactor using **PyQt6 along with newer UI libraries** (like QtFluentWidgets).

**About This Repository:**
Therefore, the code uploaded here is the **GUI version that was started but not completed**. Although unfinished, it captures the implementation ideas and code snippets from that development phase. The main purpose of uploading it is to **preserve this development process** and serve as a **reference for future projects**, allowing for potential code reuse.

---
文件
main_window.py
: 主窗口，包含多个标签页，用于不同功能的GUI。

catalog_download.py
: 用于下载地震目录，并通过多线程避免阻塞主线程。

config_gui.py
: 配置页面，允许用户设置LOC-Flow路径和工作路径。

config.ini
: 存储配置文件，包括LOC-Flow路径和工作路径。

phasenet_pick_gui.py
: PhaseNet检测页面，用于生成picks.csv文件并分离P和S波。

waveform_download_mseed_gui.py
: 用于下载地震波形数据并生成PhaseNet输入文件。 这个文件用到了pyqtfluentwidget,所以看起来会不一样

README.MD
: 介绍项目的初衷、问题和后续规划。


