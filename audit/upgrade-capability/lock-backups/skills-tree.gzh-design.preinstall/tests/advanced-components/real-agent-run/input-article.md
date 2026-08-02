# 两三百块的旧 A 卡 RX 580，我把它折腾成了本地 AI 画图机（纯小白全程踩坑记）

> 普通人不可能为了体验一下 AI 画图,先去配一台几万块的电脑。但谁又不该体验一下呢?
我就是个小白,手里只有一张两三百块的二手 **AMD RX 580（8G）**。靠着网上无数前辈分享的零碎信息,我硬是把它跑通了——**完全本地、免费、断网也能画**。
这篇就是我从零开始、踩了一堆坑才跑通的全过程。我尽量讲人话、给链接、标清楚每个坑怎么填。你只要愿意照着一步步做,旧卡也能画出高清图。
> 

<aside>
👋

**这篇写给谁?**

- 想玩 AI 文生图,但**没有 N 卡、也不想花几万块**配新电脑的人
- 手里有张**老 AMD 显卡**(比如 RX 580 / 590 这种二手两三百块的卡)
- 自认是「小白」,但**愿意动手照着一步步做**

我自己就是这样的小白。这份记录把我折腾好几天、踩了一堆坑才跑通的全过程,尽量讲人话、给链接、标清楚每个坑怎么填。照着走,你也能让旧卡画出高清写实人像。

</aside>

## 🖼️ 先看成果

![成果：在 RX 580 8G 上用 Z-Image Turbo 跑出的高清写实人像](ComfyUI_00038_.png)

成果：在 RX 580 8G 上用 Z-Image Turbo 跑出的高清写实人像

这张图就是用下面整套方法,在一张 **8G 显存的旧 AMD 卡**上跑出来的,约 4 分钟一张。不是云端、不是付费 API,**完全本地、免费、断网也能跑**。

---

## 一、先搞清楚:为什么 A 卡跑 AI 这么折腾?

绝大多数 AI 生图工具都是为 **NVIDIA(N 卡)** 写的,因为它们依赖 N 卡专属的 **CUDA** 技术。AMD(A 卡)原生用不了 CUDA。

我们的解决办法是一个叫 **ZLUDA** 的「翻译层」:它能把 CUDA 的指令实时翻译成 A 卡能听懂的话。于是 A 卡就能「假装」成 N 卡来跑 ComfyUI。

<aside>
⚠️

**ZLUDA = 翻译。翻译就会有损耗。** 所以心理预期要摆正:

- **速度比同价位 N 卡慢不少**(我这张卡 512×768、8 步,约 4 分钟一张)
- **会折腾**,版本、补丁都很讲究,差一点就报错
- 但它**真的能跑、能出好图、而且免费**。值不值,你自己权衡 🙂
</aside>

---

## 二、我的电脑配置(门槛参考)

| 部件 | 我的配置 | 说明 |
| --- | --- | --- |
| 显卡 | AMD RX 580 2048SP **8G** | 架构代号 **gfx803**(Polaris),很老的卡 |
| 显存 | 8 GB | 8G 是比较紧张的下限,能跑但要用「省显存」技巧 |
| 内存 | 16 GB | 建议至少 16G |
| 系统 | Windows | 本教程基于 Windows |

<aside>
💡

你的卡型号不一样没关系,只要是 AMD 独显基本思路一致。但**老卡(gfx803,如 RX 480/580/590)**有额外的坑(见下文),新一点的 A 卡反而更省事。

</aside>

---

## 三、整体流程一张图

```
第1步 装环境(显卡驱动 + HIP SDK + ZLUDA + ComfyUI-Zluda)
   ↓
第2步 把版本「钉死」(关键!不然新版本跑不了老卡)
   ↓
第3步 打 ZLUDA 补丁 + 检查 cublas 文件
   ↓
第4步 装 GGUF 插件(让小显存能加载大模型)
   ↓
第5步 下载 3 个模型文件
   ↓
第6步 在界面里搭「工作流」(连节点)
   ↓
第7步 打 3 个救命补丁 → 出图!
```

---

## 四、第 1 步:安装环境

环境这块,我**强烈建议直接跟着 patientx 的官方仓库 README 走**(他维护的就是「A 卡 + ZLUDA 版 ComfyUI」),因为安装脚本会自动帮你建好大部分东西。我这里只把**关键版本**和**老卡专属的坑**列出来,其余照官方走。

> 📦 官方仓库:[github.com/patientx/ComfyUI-Zluda](http://github.com/patientx/ComfyUI-Zluda)
> 

### 4.1 要装的几样东西(版本很重要)

| 软件 | 我用的版本 | 下载 / 说明 |
| --- | --- | --- |
| AMD 显卡驱动 | 26.5.2 | AMD 官网下载对应你显卡的驱动 |
| **HIP SDK** | **5.7.1** | [AMD ROCm/HIP SDK for Windows](https://www.amd.com/en/developer/resources/rocm-hub/hip-sdk.html)。⚠️ 老卡(gfx803)**别装更高版本**,新版 HIP 不再支持老卡 |
| **ZLUDA** | 3.9.5 | 一般由 ComfyUI-Zluda 的安装脚本自动拉取/配置 |
| ComfyUI-Zluda | patientx 仓库 | `git clone -b pre24patched https://github.com/patientx/ComfyUI-Zluda` |

### 4.2 老卡(gfx803)的关键坑:rocBLAS 库

<aside>
🕳️

**RX 580 这类 gfx803 老卡**:HIP SDK 5.7.1 里**不自带**你这张卡的运算库(rocBLAS)。你需要额外下载一份**专门给 gfx803 编译的 rocBLAS 库**来覆盖。不做这一步,后面 100% 报错。

**我实际用的包(亲测可用):** `rocm.gfx800-gfx900-for.hip.sdk.5.7.1-and-6.2.4.7z` —— 顾名思义,它同时适配 HIP SDK **5.7.1 和 6.2.4**,覆盖 gfx800～gfx900 这一批老卡(RX 580 属于 gfx803)。

**下载地址(亲测来源):** 这个包托管在专门修 gfx803/gfx900 老卡的开源仓库里 —— [advanced-lvl-up/Rx470-Vega10-Rx580-gfx803-gfx900-fix-AMD-GPU](https://github.com/advanced-lvl-up/Rx470-Vega10-Rx580-gfx803-gfx900-fix-AMD-GPU)。在仓库首页文件列表里点 `rocm.gfx800-gfx900-for.hip.sdk.5.7.1-and-6.2.4.7z` 就能下载。直链:

`https://github.com/advanced-lvl-up/Rx470-Vega10-Rx580-gfx803-gfx900-fix-AMD-GPU/raw/main/rocm.gfx800-gfx900-for.hip.sdk.5.7.1-and-6.2.4.7z`

> 🇨🇳 国内打不开 GitHub：在上面直链最前面加代理 `https://gh-proxy.com/` 即可，例如 `https://gh-proxy.com/https://github.com/advanced-lvl-up/...`。
> 

**怎么用(解压后两步覆盖):**

1. 把包里的 `rocblas.dll` 复制到 HIP SDK 的 `bin` 目录,默认 `C:\Program Files\AMD\ROCm\5.7\bin`(覆盖原文件,建议先备份)。
2. 把包里的 `library` 文件夹整个覆盖到 `C:\Program Files\AMD\ROCm\5.7\bin\rocblas\library`。

覆盖完后,第一次用 ZLUDA 生图会重新编译(10～30 分钟,正常现象),之后就快了。

> 若你的卡不是 gfx803/gfx900,请去该仓库或 patientx 仓库找对应你架构的包。
> 
</aside>

### 4.3 安装与启动

按官方 README:进入 `ComfyUI-Zluda` 文件夹,运行**老卡专用**的安装脚本 `install-for-older-amd.bat`(**别用**普通的 `install.bat`——老卡一定要用带 `older-amd` 的这个)。它会自动:建好 Python 虚拟环境 `venv`、装好 **torch 2.2.1+cu118**、配置 **ZLUDA 3.9.5 / HIP 5.7.1**。

装好后,用启动脚本启动(我用的是 `comfyui-user.bat`)。第一次启动会很慢,耐心等。

<aside>
📌

**我的安装目录(你可不同):** `E:\ComfyUI-Zluda`,虚拟环境在 `E:\ComfyUI-Zluda\venv`。后文所有路径都基于这个,请换成你自己的。

</aside>

---

## 五、第 2 步【最关键】:把版本「钉死」

这是我踩得最惨、也最值得分享的坑。

<aside>
💣

**ComfyUI 的最新版,会用到一个叫 `comfy_kitchen` 的新东西,它要求 PyTorch ≥ 2.4。但老 A 卡的 ZLUDA 方案只能用到 PyTorch 2.2.1。**

结果就是:你一旦更新到太新的版本,启动直接崩,报错类似:

`AttributeError: module 'torch.library' has no attribute 'custom_op'`

所以**绝对不能无脑更新到最新**,必须停在一个「还支持老 torch」的旧版本上。

</aside>

### 我锁定的版本

- 分支:`pre24patched`(patientx 专门为「老卡 / 老 torch」维护的分支)
- 具体提交:**`532e2850`**(2025 年 12 月 24 日的版本,这是我实测能跑通的「甜点版本」)

### 怎么锁定(在 `ComfyUI-Zluda` 目录下开命令行)

```bash
git fetch --all
git checkout 532e2850
```

如果提示有本地文件冲突(比如 `comfy/zluda.py` 被改过挡路),先把改动暂存再切:

```bash
git stash
git checkout 532e2850
```

<aside>
💡

切完之后你会处于「分离头指针(detached HEAD)」状态——**这正是我们要的**,它能防止 ComfyUI 偷偷把你拉回最新版。启动时如果提示 "You are not currently on a branch / 无法自动更新",**忽略即可,这是正常的**。

</aside>

### 顺带固定两个依赖版本

- PyTorch:**2.2.1+cu118**
- numpy:**1.26.4**(必须 < 2,新版 numpy 会和老环境打架)

如果重装依赖,记得在命令里加 `"numpy<2"` 锁住。装完若报 `NumPy 1.x cannot be run in NumPy 2.x`,在 `E:\ComfyUI-Zluda` 目录下用这条修:

```bash
venv\Scripts\python.exe -m pip install --no-cache-dir "numpy<2"
```

> 🪧 **国内下载依赖报错(403)?** 清华源有时缺包。可以去掉 `-i` 用官方 PyPI(需要梯子),或换阿里源 `https://mirrors.aliyun.com/pypi/simple`。
> 

---

## 六、第 3 步:ZLUDA 补丁 + 检查 cublas

ZLUDA 需要用它自己的几个 `.dll` 去「冒充」CUDA 的库文件。安装脚本一般会自动做,但**重装过 PyTorch 后要重新打一遍**。

### 重新打补丁(在 `E:\ComfyUI-Zluda` 目录下)

```bash
copy /y zluda\cublas.dll "venv\Lib\site-packages\torch\lib\cublas64_11.dll"
copy /y zluda\cusparse.dll "venv\Lib\site-packages\torch\lib\cusparse64_11.dll"
copy /y zluda\nvrtc.dll "venv\Lib\site-packages\torch\lib\nvrtc64_112_0.dll"
copy /y zluda\cufft.dll "venv\Lib\site-packages\torch\lib\cufft64_10.dll"
copy /y zluda\cufftw.dll "venv\Lib\site-packages\torch\lib\cufftw64_10.dll"
```

### 怎么确认补丁打成功了?看 cublas 文件大小

打开 `venv\Lib\site-packages\torch\lib\cublas64_11.dll`,看它的大小:

| 文件大小 | 含义 |
| --- | --- |
| **约 246 KB**(≈246,784 字节) | ✅ 是 ZLUDA 的,补丁打对了 |
| 约 88 MB | ❌ 还是原版 CUDA 的,补丁没生效,重新 copy |

### 第 3.5 步:打完补丁先自检(强烈推荐)

在开 ComfyUI 之前,先用一行命令确认「显存分配」和「矩阵运算(rocBLAS)」都正常。在 `E:\ComfyUI-Zluda` 目录下运行:

```bash
zluda\zluda.exe -- venv\Scripts\python.exe -c "import torch; print('TORCH', torch.__version__); x=torch.zeros(8).cuda(); torch.cuda.synchronize(); print('ALLOC OK', float(x.sum())); a=torch.randn(512,512).cuda(); b=torch.randn(512,512).cuda(); c=a@b; torch.cuda.synchronize(); print('MATMUL OK', float(c.sum()))"
```

看到 `ALLOC OK` 和 `MATMUL OK` 就说明底层通了(首次会现场编译、卡几分钟正常,别关)。如果这一步就报错,先别急着搭工作流——那样后面也一定跑不出图。

<aside>
🧨

**最阴险的坑:装插件会偷偷弄坏 ZLUDA 补丁!** 后面装自定义节点时,pip 很可能**顺手重装一遍 torch**(哪怕版本号没变),把刚打好的 ZLUDA 翻译 DLL **覆盖回英伟达原版**。症状:文本编码那一步约 0.01 秒就报 `CUBLAS_STATUS_NOT_SUPPORTED`(或 `cublasSgemm` 失败)。

**判定:** 看 `cublas64_11.dll` 大小——**几百 KB = ZLUDA 版(正常);上百 MB = 被覆盖回原版(已坏)**。⚠️ 跟重启毫无关系,重启修不好。

**解法:** 把上面第 3 步那 5 条 `copy /y` 补丁命令**再跑一遍**。

**防复发:** ① 在 ComfyUI-Manager 里关掉 torch 自动更新;② 以后装任何节点,凡是要 `pip install torch / torchvision / torchaudio` 的一律跳过(它们要的新 torch 和老卡根本不兼容)。

</aside>

---

## 七、第 4 步:装 GGUF 插件(小显存救星)

完整模型对 8G 显存太大。**GGUF 是一种「压缩量化」格式**,能让大模型塞进小显存。我们用 `ComfyUI-GGUF` 这个插件来加载它。

### 安装(在 `ComfyUI-Zluda\custom_nodes` 目录下)

```bash
git clone https://github.com/city96/ComfyUI-GGUF
```

> 插件仓库:[github.com/city96/ComfyUI-GGUF](http://github.com/city96/ComfyUI-GGUF)
> 

装完重启 ComfyUI,就会多出 `Unet 加载器 (GGUF)`、`CLIP加载器 (GGUF)` 这些节点。

<aside>
⚠️

**装完插件后,务必回头再看一眼 `cublas64_11.dll` 的大小**(第 3 步那个判定法)。装插件经常会把 ZLUDA 补丁冲掉、文件变回上百 MB;一旦被冲掉,把第 3 步那 5 条 `copy /y` 命令重跑一遍再继续,否则一生图就报 `CUBLAS_STATUS_NOT_SUPPORTED`。

</aside>

---

## 八、第 5 步:下载 3 个模型文件

我们要画的模型是 **Z-Image Turbo**(出图快、质量高、对小显存友好)。它需要 3 个文件:

| 作用 | 文件 | 放到哪个文件夹 | 下载链接 |
| --- | --- | --- | --- |
| **主模型**(画图的) | `z_image_turbo-Q4_K_M.gguf`(约 5 GB) | `models\unet\` | [点此下载](https://huggingface.co/jayn7/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_K_M.gguf) |
| **文本编码器**(读懂你提示词的) | `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | `models\text_encoders\` | [点此下载](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf) |
| **VAE**(把数据还原成图片的) | `ae.safetensors`(约 335 MB) | `models\vae\` | [点此下载](https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors) |

<aside>
🇨🇳

**国内下不动 huggingface?** 把链接里的 `huggingface.co` 换成镜像站 `hf-mirror.com` 即可,例如:

`https://hf-mirror.com/jayn7/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_K_M.gguf`

建议用 IDM 之类的下载工具,大文件更稳。

</aside>

<aside>
🎚️

**显存更小 / 更大怎么选?** 文件名里的 `Q4_K_M` 是压缩档位。数字越大越清晰也越占显存:Q3 更省、Q5/Q6/Q8 更清晰。8G 显存用 **Q4_K_M** 比较平衡。

</aside>

---

## 九、第 6 步:在界面里搭「工作流」

打开浏览器进入 ComfyUI(默认 `http://127.0.0.1:8188`)。**在画布空白处双击**,会弹出搜索框,输入节点名就能添加。

### 要添加的 9 个节点

| # | 搜索这个名字 | 数量 | 作用 |
| --- | --- | --- | --- |
| 1 | `UnetLoaderGGUF` | 1 | 加载主模型 |
| 2 | `CLIPLoaderGGUF` | 1 | 加载文本编码器 |
| 3 | `VAELoader`(或老卡更稳的 `CFZ VAE Loader`) | 1 | 加载 VAE |
| 4 | `CLIPTextEncode` | **2** | 正面 + 负面提示词 |
| 5 | `EmptySD3LatentImage` | 1 | 定义画布尺寸 |
| 6 | `KSampler` | 1 | 采样(真正画图的核心) |
| 7 | `VAEDecodeTiled` | 1 | **分块**解码(小显存必须用这个,见第 7 步) |
| 8 | `SaveImage` | 1 | 保存图片 |

### 各节点参数

- **Unet 加载器 (GGUF)** → 选 `z_image_turbo-Q4_K_M.gguf`
- **CLIP加载器 (GGUF)** → 模型选 `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`;**类型(type)选 `qwen_image`** ⚠️(这个最容易选错,下文有说明)
- **加载VAE** → 选 `ae.safetensors`;如果用的是 CFZ VAE Loader,**精度选 `fp32`**
- **空Latent (EmptySD3LatentImage)** → 宽 `512`、高 `768`、批量 `1`
- **K采样器 (KSampler)** → 步数 `8`、cfg `1.0`、采样器 `euler`、调度器 `simple`、降噪 `1.0`
- **分块VAE解码 (VAEDecodeTiled)** → `tile_size` 设 `256`、`overlap` 设 `64`
- **正面 CLIP文本编码** → 填你想画的内容,如 `1girl, standing, detailed face, soft light`
- **负面 CLIP文本编码** → 填不想要的,如 `lowres, bad anatomy, blurry`

<aside>
🎯

**关于「类型」为什么选 `qwen_image`:** Z-Image 的文本编码器其实就是 Qwen3-4B。在 2025 年 12 月这个版本里,下拉框里**还没有独立的 `z_image` 选项**(那是后来才加的),所以选它对应的 `qwen_image` 就对了。如果你找不到 `z_image`,别慌,这是正常的。

</aside>

### 连线(从节点右边的「输出点」拖到另一个节点左边的「输入点」)

```
Unet加载器.MODEL        → K采样器.model
CLIP加载器.CLIP         → 正面文本编码.clip
CLIP加载器.CLIP         → 负面文本编码.clip   (同一个点能拖两条线)
正面文本编码.CONDITIONING → K采样器.positive
负面文本编码.CONDITIONING → K采样器.negative
空Latent.LATENT         → K采样器.latent_image
K采样器.LATENT          → 分块VAE解码.samples
加载VAE.VAE             → 分块VAE解码.vae
分块VAE解码.IMAGE        → 保存图像.images
```

连好后,每个节点左侧的输入点都应该有线接着(文本框是直接打字的,不用连)。

---

## 十、第 7 步【救命补丁】:让它真的能出图

搭好工作流直接跑,大概率会连报几个错。这是因为「**新 ComfyUI 代码 + 老 PyTorch 2.2.1**」之间有缝隙。下面 3 个补丁是我一个个踩出来的,打完就能出图。

### 补丁 ①②:改一个文件 `comfy/ops.py`

用记事本打开(先关掉 ComfyUI):

```bash
notepad E:\ComfyUI-Zluda\comfy\ops.py
```

在文件靠上、`import torch` 那一行的**下面**,粘贴这 3 行:

```python
if not hasattr(torch.compiler, "is_compiling"):
    torch.compiler.is_compiling = lambda *a, **k: False
torch.backends.cudnn.enabled = False
```

它们分别解决两个报错:

- **`module 'torch.compiler' has no attribute 'is_compiling'`** → 第 1~2 行补一个老 torch 缺失的函数
- **`cuDNN error: CUDNN_STATUS_INTERNAL_ERROR`**(VAE 解码时崩)→ 第 3 行关掉老 A 卡不稳的 cuDNN

> ⚠️ 注意第 2 行要有缩进(4 个空格),第 1、3 行顶格。保存时确认文件名还是 `ops.py`,别存成 `.txt`。
> 

<aside>
🔧

**为什么用改代码、而不是用界面里的 CFZ CUDNN Toggle 节点?** 两者效果一样(都是关 cuDNN),但改代码是**全局永久生效**,以后新建任何工作流都不用再操心;而节点法你每个工作流都得记得加,容易忘。对「显卡固定不变」的人,改代码更省心,且**零性能损耗**。

</aside>

### 补丁 ③:VAE 用「分块」解码

这个其实在第 6 步已经做了——**用 `VAEDecodeTiled`(分块VAE解码)而不是普通的 `VAEDecode`**。

原因:8G 显存一次性解码整张图,卷积运算太大,会让程序**直接闪退**(连报错都来不及)。分块解码把图切成小块逐块处理,就扛得住了。`tile_size` 设 256;如果还闪退,降到 128。

---

## 十一、出图!

<aside>
📏

**三条铁律(违反就翻车):**

1. **永远用 `comfyui-user.bat` 启动**(它内部已经用了 `zluda.exe` + 那串参数),别直接 `python main.py`。
2. **每次都新开一个干净的命令行窗口**,别在跑过别的脚本的旧窗口里启动。
3. **第一次出图会现场编译,10～30 分钟很正常**,别以为死机;结果会缓存,以后就快了。
</aside>

保存文件 → 重启 `comfyui-user.bat` → 回到界面点 **Queue / 运行**。

- 启动后先看日志里的设备那行,应是 `Device: cuda:0 AMD Radeon RX 580 ... [ZLUDA] : native`(**末尾是 `native`,不是 `cudaMallocAsync`**)。若不是 native,说明 `--disable-cuda-malloc` 没生效。
- 第一次跑会**很慢**(ZLUDA 要现场编译),可能卡住几分钟不动,**别以为死机,等着**。
- 跑完图片会出现在 `output` 文件夹里(要用 `保存图像 SaveImage` 节点才会存盘;若用 `预览图像 PreviewImage`,图只在临时目录、关掉就没了)。

🎉 看到图,你就成功了!

---

## 十二、踩坑速查表(报错 → 解法)

| 报错 / 现象 | 原因 | 解法 |
| --- | --- | --- |
| `torch.library has no attribute 'custom_op'` | 版本太新,要 torch 2.4 | 回退到旧版本(第 2 步,`git checkout 532e2850`) |
| `torch.compiler has no attribute 'is_compiling'` | 老 torch 缺函数 | 补丁 ①(第 7 步) |
| `cuDNN error: CUDNN_STATUS_INTERNAL_ERROR` | 老 A 卡 cuDNN 不稳 | 补丁 ②:关 cuDNN(第 7 步) |
| 跑到 VAE 解码**直接闪退**(无报错) | 卷积太大撑爆 | 补丁 ③:用分块VAE解码,tile_size 调小 |
| 下拉框里**没有 z_image** | 这版本还没这选项 | 选 `qwen_image`(正常现象) |
| 出图全是**黑图** | VAE 精度溢出 | VAE 精度用 `fp32`(别用 fp16) |
| 下依赖 **403 / SSL 错误** | 国内镜像缺包 | 换官方 PyPI(梯子)或阿里源 |
| 启动提示 "not on a branch / 无法更新" | 分离头指针 | **正常,忽略**,这正是我们要的 |
| `cublas64_11.dll` 有 88MB | ZLUDA 补丁没打上 | 重新 copy(第 3 步) |
| `CUBLAS_STATUS_NOT_SUPPORTED`(文本编码秒挂) | 装插件时 pip 重装 torch,把 ZLUDA 翻译 DLL 冲回原版 | 重跑第 3 步 5 条 `copy /y`;判定看 `cublas64_11.dll` 上百 MB=已坏(**重启无效**) |
| `CUDA error: operation not supported`(加载模型时) | ZLUDA 不支持 cudaMallocAsync | 启动参数里加 `--disable-cuda-malloc` |
| `CUDA out of memory`(升级 torch 后) | torch 2.3/2.4 在老卡必爆显存 | 降回 **torch 2.2.1**,这是 RX 580 的天花板 |
| 装节点报 `security level configuration` | ComfyUI-Manager 安全等级拦截(非节点问题) | 把 `user\__manager\config.ini` 的 `security_level` 改成 `weak`,装完改回 `normal`;或手动 `git clone` 到 `custom_nodes` |
| 放大时跑到 VAE 解码**闪退**(`请按任意键继续`) | 图变大后 fp32 VAE 解码撑爆显存 | 把 VAE 精度改 **bf16**(用 CFZ VAE Loader);或把「分块VAE解码」`tile_size` 降到 128 |

---

## 十三、常见问答

- <strong>Q：VAE 精度 fp32 / fp16 / bf16 怎么选?</strong>
    - **bf16(写实强烈推荐,实测可用!)**:我折腾后的最大发现——RX 580(gfx803)虽然没有原生 bf16,但 **ZLUDA 实测能跑、不黑图**,显存还只占 fp32 的一半左右。写实流首选 bf16(又省显存又不黑图)。
    - **fp32**:最稳、绝不黑图,但占用最高、最慢。base 出图能用;**一旦放大就容易爆显存闪退**,这时换 bf16。
    - **fp16**:最省最快,但 **Flux 系 VAE(写实)用它几乎必黑图,别用**;不过**二次元的 SD1.5 VAE 对 fp16 友好**,二次元可放心用 fp16(还更快)。
- <strong>Q：文本编码器要用 Instruct 版还是 base 版?</strong>
    
    我实测用的是 **`Qwen3-4B-Instruct` 版,完全能跑、出图质量很好**,所以本教程就用它。
    
    网上有说法称 Z-Image「理论上更适合用 base 版」,但我还没实测验证。如果你想追求理论最优可以自己试 base 版;就「能不能用、好不好用」而言,Instruct 版已经验证可行。
    
- <strong>Q：太慢了,能提速吗?</strong>
    
    老卡跑 ZLUDA 慢是正常的。可尝试:降低分辨率;保持 8 步不要加;别开 lowvram(反而更慢);VAE 试 bf16(见上)。但本质上受限于硬件,别期待 N 卡的速度。
    
- <strong>Q：怎么换内容画别的?怎么固定同一张脸?</strong>
    - 换内容:改「正面文本编码」里的提示词,点 Queue 重跑即可。
    - 固定脸:用**同一个种子(seed)+ 同样的提示词**,出来的就是同一张脸/构图。
- <strong>Q：我的启动参数是什么?</strong>
    
    我用的启动参数(写在启动 bat 里):
    
    `--auto-launch --use-quad-cross-attention --reserve-vram 0.9 --disable-async-offload --disable-pinned-memory --disable-cuda-malloc`
    
    ⚠️ **不要**加 `lowvram`,实测反而更慢更不稳。
    
- <strong>Q：出一张图就得重启一次吗?能连续「抽卡」吗?</strong>
    
    **能,不用每张都重启。** 出图后模型赖在显存里是**正常且有利的**——下一张直接复用、更快,这就是「抽卡」。想连出就一直点「生成」。
    
    ⚠️ 但**千万别点「释放模型 / Unload Models」按钮**:这张卡(ZLUDA)上一点它,进程就直接崩(命令行蹦 `请按任意键继续`),等于强制重启。真遇到自然崩溃(跑挂、或换大模型显存不够),才重启 `comfyui-user.bat`。换成 GAN 放大(轻)后,基本可以放心连抽。
    
- <strong>Q：生成的图在「资产 / Assets」面板里看不到,但 output 文件夹里明明有?</strong>
    
    这是新版 ComfyUI「资产」面板的**已知 bug**(它取代了老「队列」,经常不自动刷新、重启后空白),图没丢。
    
    - 先试:浏览器按 `Ctrl+R` / `F5` 刷新,或把「资产」标签关掉再打开。
    - 最稳:直接开 `output` 文件夹看(固定到「快速访问」)。每张 PNG 内嵌了工作流,**直接拖回 ComfyUI 就能还原全部参数**。
    
    ⚠️ **别为修这个去更新 ComfyUI**,会破坏你钉死的 ZLUDA 版本。
    

---

## 十四、进阶:把图片放大(用「放大模型」,又快又干净)

跑出图后,你大概会想要更大、更清晰的图。**我一开始走了大弯路,后来才发现:这张卡上最好用的放大方法,恰恰是「GAN 放大模型」——又快又干净,还不挑显存。**

<aside>
🔄

**重要更正(推翻我之前的结论):** 我一度以为「放大模型(ESRGAN / RealESRGAN 那类)在 RX 580 上跑不动」——**错了!** 实测它不但能跑,还是**最佳方案**:二次元出 4K 约 **90 秒**,写实出 2K 约 **200 秒**(都含出图)。因为 GAN 放大**不重绘**,只做一次「放大 + 锐化」,既不爆显存、也不会加脏东西。

</aside>

### 先搞懂:放大分两种

| 类型 | 原理 | 结果 |
| --- | --- | --- |
| **重绘式**(SD放大 / Latent 高清修复) | 加噪声 → 重新画一遍 | 会**加纹理**(毛孔、飞丝),还慢;对干净的脸反而越放越「脏」 |
| **GAN 模型放大**(RealESRGAN 等) | 只放大 + 锐化,**不重画** | **完整保留出图的干净**,而且飞快 ✅ |

追求「干净、清晰、还要快」,**直接用 GAN 模型放大**,别碰重绘式。

### 第 1 步:下载放大模型(放进 `models\upscale_models\`)

| 模型 | 倍数 | 用途 | 下载 |
| --- | --- | --- | --- |
| **RealESRGAN_x2plus** | 2x | 写实,温和干净、最省显存(**写实日常推荐**) | [点此下载](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth) |
| **4x-UltraSharp** | 4x | 写实,最锐(但 4x 在写实流里易爆显存,见下) | [点此下载](https://hf-mirror.com/lokCX/4x-Ultrasharp/resolve/main/4x-UltraSharp.pth) |
| **RealESRGAN_x4plus_anime_6B** | 4x | **二次元专用**,线条最干净(整合包常自带) | 整合包通常已自带;没有就去 [openmodeldb.info](http://openmodeldb.info) 搜 |

下完**重启 ComfyUI**(或点界面刷新),「放大模型加载器」下拉框里就能选到。

### 第 2 步:接 2 个节点(写实 / 二次元通用)

在原来「分块VAE解码 → 保存图像」中间,插入放大节点:

```
分块VAE解码 ──图像──→ 使用模型放大图像 ──图像──→ 保存图像
                          ↑ 放大模型
              放大模型加载器 ┘
```

- **放大模型加载器(UpscaleModelLoader)** → 选模型
- **使用模型放大图像(ImageUpscaleWithModel)** → 接上面的「放大模型」+「分块VAE解码」的图像输出;它的图像输出直接进「保存图像」

**没有 K采样器、没有降噪、没有 ControlNet**——纯放大,所以 100% 保持干净。

### 写实 / 二次元 各自怎么配

| 类型 | 放大模型 | 倍数 | 实测速度(含出图) |
| --- | --- | --- | --- |
| **写实**(Z-Image) | `RealESRGAN_x2plus` | 2x → ~2K | 约 200 秒 |
| **二次元**(MeinaMix) | `RealESRGAN_x4plus_anime_6B` | 4x → ~4K | 约 90 秒 |

<aside>
🧠

**为什么写实只用 2x、二次元能上 4x?** Z-Image 模型重,出图模型 + 4x 放大(中间图要到 3072×4608)挤在 8G 里会爆;而 SD1.5(二次元)很轻,留得出显存,4x 在同一个工作流里也跑得动。**写实若想要 4x,就把放大单独做成一个小工作流**(只有「加载图像 → 使用模型放大图像 → 保存图像」、不加载任何出图模型),8G 全空给它,就不爆了。

</aside>

<aside>
⚠️

**别在 ZLUDA 上点「释放模型 / Unload Models」按钮!** 这张卡上一点它,进程会直接崩(命令行蹦 `请按任意键继续`),等于强制重启。好在你**根本不需要它**:正常抽卡就一直点「生成」,模型常驻显存反而更快;真崩了再重启 `comfyui-user.bat`。

</aside>

### (可选)想要「重绘增强」细节?

GAN 放大只放大、不重画。如果你**就是想让画面被重新精修一遍**(比如二次元把眼睛、阴影画得更精致),可以用重绘式的「Latent 高清修复 / Ultimate SD Upscale」——但它**更慢、且对写实干净脸会加脏东西**,追求干净就别用。需要时去社区找 Ultimate SD Upscale 教程即可。

---

## 十五、附:另一条更省力的路线(SD1.5 + MeinaMix,二次元)

<aside>
🧭

上面整篇讲的是 **Z-Image Turbo**(较新、写实强)。其实在老卡上,**SD1.5 系模型**更轻、社区资源最多、跑二次元/动漫风格特别顺手——这也是我最早跑通的路线。**环境部分(驱动 / HIP / ZLUDA / 版本钉死 / ZLUDA 补丁 / 自检)完全沿用上面第 1～3 步**,只是换模型、换工作流。下面给一套实测好用的二次元配方(MeinaMix V12)。

</aside>

### 要下载的文件(国内 hf-mirror 镜像,免梯子)

| 文件 | 放到哪 | 下载链接 |
| --- | --- | --- |
| **MeinaMix V12**(2.13G 单文件) | `models\checkpoints` | [点此下载](https://hf-mirror.com/ElectricGoal/models-moved/resolve/main/meinamix_v12Final.safetensors)(备用:[源2](https://hf-mirror.com/realding/tem/resolve/main/meinamix_v12Final.safetensors)) |
| **VAE** kl-f8-anime2(405MB) | `models\vae` | [点此下载](https://hf-mirror.com/Lucetepolis/FuzzyHazel/resolve/main/kl-f8-anime2.vae.safetensors) |
| 负面嵌入 EasyNegative | `models\embeddings` | [点此下载](https://hf-mirror.com/datasets/gsdf/EasyNegative/resolve/main/EasyNegative.safetensors) |
| 负面嵌入 ng_deepnegative | `models\embeddings` | [点此下载](https://hf-mirror.com/tera0711/embeddings/resolve/main/ng_deepnegative_v1_75t.safetensors) |
| 治手嵌入 badhandv4(可选) | `models\embeddings` | [点此下载](https://hf-mirror.com/ffxvs/negative-prompts-pack/resolve/main/badhandv4.pt) |

<aside>
⚠️

huggingface 上的 `Meina/MeinaMix_V11` 是 **Diffusers 多文件夹格式**,ComfyUI 用不了,**必须用上面的单文件 `.safetensors`**。下完素材记得**重启 ComfyUI** 让它扫描到。

</aside>

### 节点与参数(数据流从前到后)

- **Checkpoint加载器** → `meinamix_v12Final.safetensors`
- **设置CLIP最后一层(CLIPSetLastLayer)** → `-2`(即 Clip Skip 2,二次元关键)
- **加载VAE** → `kl-f8-anime2.vae.safetensors`
- **空Latent图像** → 宽 512 × 高 768,批量 1
- **基础 K采样器** → `dpmpp_2m` / `karras` / 步数 28 / cfg 6～7 / 降噪 **1.0**
- **缩放Latent(比例 LatentUpscaleBy)** → `nearest-exact` / 缩放 1.5 倍(这就是 Hires Fix 高清修复)
- **高清 K采样器** → `dpmpp_2m` / `karras` / 步数 20 / cfg 7 / 降噪 **0.45**(灵魂参数,绝不能设 1.0)
- 最后 **VAE解码 → 保存图像**

**数据流:** 空Latent → 基础采样器(降噪1.0) → 缩放Latent(1.5) → 高清采样器(降噪0.45) → VAE解码 → 保存图像

**正面提示词模板:**

```
masterpiece, best quality, very aesthetic, 1girl, solo, detailed face, detailed eyes, beautiful detailed hair, soft lighting, depth of field
```

**负面提示词模板:**

```
EasyNegative, ng_deepnegative_v1_75t, worst quality, low quality, blurry, bad anatomy, bad hands, extra fingers, missing fingers, watermark, signature, text
```

<aside>
🖐️

**老画崩手怎么办?** 把治手嵌入 `badhandv4` 放进 `models\embeddings`,在负面词里写它的文件名(不带扩展名)即可;太抢画风就降权写成 `(badhandv4:0.8)`。想更彻底就装 `ComfyUI-Impact-Pack`,用 Detailer + `hand_yolov8` 把手部单独检测放大重绘。

</aside>

<aside>
⏱️

**速度参考:** 512×512 / 20 步约 **22 秒/张**(首次现场编译会久,缓存后就是这速度)。≈1 s/it 基本就是 RX 580 跑 SD1.5 的算力天花板,后端开关基本撒不动;真要提速靠**减步数 / 用 `dpmpp_2m`+`karras`**(12～15 步出同等质量)。

</aside>

---

<aside>
❤️

**写在最后:** 我也只是个普通人,能跑通全靠网上无数前辈分享的零碎信息拼起来的。所以我把它整理成这份记录,希望你也能少踩点坑。普通人不用花几万块,也能体验一把本地 AI 生图的乐趣。玩得开心 🎨

</aside>

---

## 📝 个人记录区(不传飞书)

<aside>
🗂️

这一部分是我自己后续折腾的记录,属于「跑通之后」的个人玩法——换模型、换风格、图生图等,丰俭由人。**飞书上传的是上面的正文(到「写在最后」为止);这一节及以下只留在这里做记录,不传飞书。**

</aside>

### 记录一:图生图(img2img)——在现有工作流上改 3 处

不用下任何东西,就在二次元(MeinaMix)工作流上改:把「空Latent图像」换成「真实图片编码出来的 Latent」,再把降噪调到 1.0 以下。

1. 加 `加载图像(LoadImage)` 节点,选要改的图。
2. 加 `VAE编码(VAEEncode)`:`pixels` 接 LoadImage 的 IMAGE;`vae` 接和解码端同一个 VAE 加载器(图小用普通编码即可,不用分块)。
3. 把 `VAE编码` 输出的 LATENT 接到 `K采样器` 的 `latent_image` 口,取代原来的「空Latent图像」。
4. 把 K采样器「降噪」从 1.0 调低。

| 降噪 | 效果 |
| --- | --- |
| 0.3~0.4 | 几乎只换质感/修细节,构图不动 |
| 0.5 左右 | 同构图重画,换风格最常用,先从这试 |
| 0.6~0.75 | 大改,适合线稿/草稿上色 |
| 0.8+ | 基本无视原图,接近文生图 |

<aside>
⚠️

**输入图尺寸要压到 SD1.5 舒适区(约 512×768)。** 输出尺寸就等于输入图尺寸,喂大图会变形/变慢/爆显存。可在 LoadImage 后、VAE编码 前加 `缩放图像(按最长边)` 先缩到 512~768。VAE 的输入口接「VAE加载器」的输出,一个 VAE 同时喂编码和解码两端。

</aside>

<aside>
🩹

**图生图新坑:采样跑完、最后一步 VAE 解码才崩(同 tile,编码不崩、解码崩)。** 现象:采样 `100%|10/10` 跑完,日志冒出 `Requested to load AutoencodingEngine ... 495 MB usable`,随后直接「请按任意键继续」退出、**没出图**。根因:解码排在采样**之后**,此时 UNet 还占着显存、整卡只剩约 495MB,512 的解码一申请工作显存就崩;而同样是 512 的**编码却不崩**——因为编码排在 UNet 装载**之前**跑,那会儿显存还宽裕。**解法:把分块VAE「解码」的 tile 降到 256(不行再降 128),编码 512 可暂留。** tile 调小只拖慢解码这一步(GPU 上多约 10~30 秒)、**不影响画质**(重叠区无缝混合);只有 256/128 都还崩,才上 CPU VAE 兜底。

</aside>

### 记录二:动漫放大改用 2x 专用模型(4x 会过度锐化/变形)

正文二次元用的是 `RealESRGAN_x4plus_anime_6B`(4x)。实测在 512×768 小底图上放到 4x,会**过度锐化、有些地方变形**。改用 **2x 动漫专用模型**更稳(2x 放大倍率小,锐化不会被放那么大)。

| 模型 | 架构 | 说明 | 下载 |
| --- | --- | --- | --- |
| **2x-AnimeSharpV3**(首选) | ESRGAN | 现代动画 2x,锐利但忠实、几乎无伪影 | [点此下载](https://github.com/Kim2091/Kim2091-Models/releases/download/2x-AnimeSharpV3/2x-AnimeSharpV3.pth) |
| **2xHFA2kCompact**(更轻更快/更温和) | Compact | 仅 4.6MB,RX 580 上飞快 | [点此下载](https://huggingface.co/Phips/2xHFA2kCompact/resolve/main/2xHFA2kCompact.pth) |

<aside>
⚠️

**只下 ESRGAN/Compact 架构的版本!** 别下 RCAN/RealPLKSR/MoSR/DAT 这些新架构(比如 AnimeSharp V4 是 RCAN、V2 里的 RealPLKSR/MoSR 版)——钉死的老版本 ComfyUI(spandrel 太旧)加载它们会直接报错。国内慢可在 GitHub 链接前加 `https://gh-proxy.com/`,或把 `huggingface.co` 换成 `hf-mirror.com`。

</aside>

### 记录三:进阶——换 SDXL 强动漫模型

SD1.5(MeinaMix)属于轻量老架构。真正强的现代动漫模型在 **SDXL 档(1024 原生)**,细节/手/构图全面更强。8G 卡能跑,只是慢一点(1024 出图约 2~4 分钟)。

| 模型 | 特点 | 下载(HF,可换 [hf-mirror.com](http://hf-mirror.com)) |
| --- | --- | --- |
| **Animagine XL 4.0 Opt**(推荐先试) | 纯 SDXL 精调,提示词友好,直链干净 | [点此下载](https://huggingface.co/cagliostrolab/animagine-xl-4.0/resolve/main/animagine-xl-4.0-opt.safetensors) |
| **Illustrious XL** | 社区 meta,danbooru 标签理解最强,LoRA 生态最大 | [仓库页](https://huggingface.co/OnomaAIResearch/Illustrious-XL-v2.0) |
| **Pony Diffusion V6 XL** | 角色/姿势极强(需 `score_9` 类标签) | [仓库页](https://huggingface.co/LyliaEngine/Pony_Diffusion_V6_XL) |

<aside>
✅

**【已验证·8G 卡跑 SDXL 的正确姿势:必须用 GGUF 量化版】**

直接下 SDXL 的 **fp16 原版**(如 animagine-xl-4.0-opt,6.94G)在 8G 卡上**根本跑不起来**——模型还没开始采样就把显存占爆、控制台直接 `请按任意键继续` 闪退(内存也只 16G、没法靠 lowvram 卸载到内存时尤其如此)。

**解法:改用 GGUF Q8 量化版(UNet 仅 2.74G),实测文生图完美跑通。** 跟 Z-Image 同理,但 SDXL 要把模型拆成三块分别加载:

- **主模型(UNet)用 GGUF** → `Unet加载器(GGUF)`,放 `models\unet`
- **CLIP 用 safetensors 版**(ComfyUI 的 GGUF 版 CLIP 还不支持 SDXL 的 clip_g)→ `双CLIP加载器(DualCLIPLoader)`:clip1=clip_g、clip2=clip_l、type 选 `sdxl`,放 `models\clip`
- **VAE** → `VAE加载器`,选 sdxl_vae.safetensors

**下载(WAI-illustrious 动漫,一个仓库全有,hf-mirror 直链):**

- 主模型 Q8:`https://hf-mirror.com/nuupy/WAI-illustrious-SDXL-GGUF/resolve/main/WAI-illustrious-SDXL-v170-Q8_0.gguf?download=true`
- clip_g:`https://hf-mirror.com/nuupy/WAI-illustrious-SDXL-GGUF/resolve/main/clip/clip_g.safetensors?download=true`
- clip_l:`https://hf-mirror.com/nuupy/WAI-illustrious-SDXL-GGUF/resolve/main/clip/clip_l.safetensors?download=true`

**采样:** `euler_ancestral` / `normal` / 步数 28 / CFG 6;尺寸 832×1216(竖)或 1024×1024;CLIP Skip -2;VAE 解码用分块 tile 256。

**Q8 画质≈fp16,几乎无损。** ⚠️ Animagine 4.0 的 GGUF 是 stable-diffusion.cpp 格式、**ComfyUI 不兼容**,别下错。

</aside>

放进 `models\checkpoints\`(注:上表为 **fp16 原版直链,仅供大显存卡参考**;8G 卡实战请用上面绿框的 **GGUF 量化版**)。换 SDXL 必须改的几件事:

- **VAE 换 fp16-fix 版**(否则黑图):[sdxl-vae-fp16-fix](https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl_vae.safetensors) → 放 `models\vae\`,用 VAE加载器加载它,别用 checkpoint 自带 VAE。
- **分辨率改 1024 档**:竖图用 832×1216 或 896×1152,别再用 512×768。
- **采样器**(ComfyUI 的 `K采样器` 把它拆成两个框,别在一个框里找完整名字):**采样器(sampler_name)** 选 `dpmpp_2m_sde`(WebUI 里叫 "DPM++ 2M SDE",ComfyUI 用代码名;找不到就用 `dpmpp_2m_sde_gpu`),**调度器(scheduler)** 选 `karras`。步数 20~28,CFG 4~6。
- **CLIP Skip**:Animagine/Illustrious 用 -2;Pony 用 -1。
- **提示词**(这类模型看「标签」说话,每家的质量词是各自训练的,不能混用):
    - **Animagine XL 4.0**:结构 `1girl/1boy, 角色名, 作品名, rating, 其它标签`,质量增强词放在**结尾**:`masterpiece, high score, great score, absurdres`(别用旧版的 `best quality, newest`,也别放到开头)。负面词官方推荐:`lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry`。
    - **Pony V6**:必须加 `score_9, score_8_up, score_7_up`。
    - **Illustrious**:直接堆 danbooru 标签。

<aside>
🧠

**显存提醒(8G):** SDXL 主模型一加载就吃约 6.5G,**别把「生图 + 4x 放大」塞进同一流程**(必爆)。走法:先出 1024 图保存,要放大时另开一个只有放大模型、不加载大模型的流程跑 GAN 放大。图生图接法和记录一完全一样,只是换成 SDXL 模型加这个 fp16-fix VAE。

</aside>

<aside>
📝

**状态:** SDXL 文生图(GGUF Q8 + WAI-illustrious)**已实测跑通** ✅;SDXL 图生图卡在 **ZLUDA 跑 VAE 编码必崩**(fp16/bf16/分块全试过,与显存无关,是 gfx803 的 kernel 坑),解法待验证:① Windows 注册表 TdrDelay=60 放宽驱动看门狗超时;② 装 ComfyUI-AnyDeviceOffload 把 VAE 丢到 CPU 跑。2x 动漫放大模型仍待验证。

</aside>