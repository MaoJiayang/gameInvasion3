from setuptools import setup, find_packages
import codecs

with open('requirements.txt',encoding='utf-8') as f:
    requirements = f.read().splitlines()

# 使用codecs模块打开MANIFEST.in文件，并指定编码为utf-8
with codecs.open('MANIFEST.in', 'r', 'utf-8') as f:
    manifest = f.read()

setup(
    name='gameInvasion3',
    version='1.1.0',
    url='https://github.com/MaoJiayang/gameInvasion3',
    author='Jiayang Mao',
    author_email='Nucleon_17th@njust.edu.cn',
    description='a python game engine for my 2D game development',
    packages=find_packages(),    
    install_requires=requirements,
    # 添加manifest参数
    manifest=manifest,
)