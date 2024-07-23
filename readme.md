[English version](readme_en.md)

### 末次更新：20240723
20240723 --更新了中文readme
# GameInvasion
该项目是我的某课程作业。
纯python游戏，老师的初衷是“外星人入侵”但我觉得这个名字实在是太丑陋了（）
该项目旨在自行学习和编写一个基于纯python的游戏引擎，并基于该引擎开发一个游戏。
PyPi项目地址：https://pypi.org/project/gameInvasion3/

## 安装
请确保你的python版本大于3.9
### 从源码进行安装
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
安装好该项目之后，你可以进入项目目录，运行develop_main.py
### 从pip进行安装
当然，如果你只是想要玩玩我的这个游戏demo，你也可以：
```bash
#下载我的项目
pip install gameInvasion3
#运行可执行文件
gameInvasion3
```
使用非pypi官方源的小伙伴注意：我的包可能并未及时同步到各个镜像上。
因此如果上述指令显示包不存在，或者你想确保安装最新版本，请试试使用官方源来安装
```bash
#下载我的项目
pip install gameInvasion3 -i https://pypi.org/simple
#运行可执行文件
gameInvasion3
```
## 项目结构
### invasionEngine:游戏引擎本体
其中包括了组件-游戏对象-场景的基本游戏引擎组织结构。也包括一些常数定义和游戏事件的定义。一般来说，仅仅是使用本项目时无需修改其中的代码。
### invasion_game_demo：
这里是游戏demo
