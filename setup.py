from setuptools import setup, find_packages

with open('requirements.txt',encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name='gameInvasion',
    version='3.0.0',
    url='https://github.com/MaoJiayang/gameInvasion3',
    author='Jiayang Mao',
    author_email='Nucleon_17th@njust.edu.cn',
    description='a python game engine for my 2D game development',
    packages=find_packages(),    
    install_requires=requirements,
)
