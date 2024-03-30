### 末次更新：20240330
# GameInvasion
该项目是我的某课程作业。
纯python游戏，老师的初衷是“外星人入侵”但我觉得这个名字实在是太丑陋了（）
该项目旨在自行学习和编写一个基于纯python的游戏引擎，并基于该引擎开发一个游戏。

## 安装

要安装这个项目，你可以在命令行运行：
```bash
# 克隆仓库
git clone https://github.com/MaoJiayang/gameInvasion3
# 切换到项目目录
cd gameInvasion3
# 安装依赖
pip install -r requirements.txt
```
或者下载代码压缩包，并在本地运行：
```bash
pip install -r requirements.txt
```
当然，如果你只是想要玩玩我的这个游戏，你也可以：
```bash
#下载我的项目
pip install gameInvasion==3.0.0
#运行主脚本
python -m gameInvasion.main
```
使用非pypi官方源的小伙伴注意：我的包可能并未同步到各个镜像上。因此请使用官方源来安装
## 项目结构
### invasionEngine:游戏引擎本体
其中包括了组件-游戏对象-场景的基本游戏引擎组织结构。也包括一些常数定义和游戏事件的定义。一般来说，仅仅是使用本项目时无需修改其中的代码。
### 各类以custom_开头的目录：
这里是游戏引擎基础上自定义的组件-游戏对象-场景结构。
### resources:
游戏用到的资源文件应该放在这里。
### start_menu:
目前游戏还未将游戏界面编辑集成至引擎内。所以这里存储着完全外置的开始菜单模块。