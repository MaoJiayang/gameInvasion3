from setuptools import setup, find_packages

with open('requirements.txt',encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name='gameInvasion3',
    version='1.1.23',
    url='https://github.com/MaoJiayang/gameInvasion3',
    author='Jiayang Mao',
    author_email='Nucleon_17th@njust.edu.cn',
    description='a python game engine for my 2D game development',
    packages=['invasion_game_demo','invasionEngine'],
    package_data={
        'invasion_game_demo': ['resources/**/*'],
    },  
    install_requires=requirements,
    python_requires='>=3.9, <3.13',
    entry_points={
        'console_scripts': [
            'gameInvasion3=invasion_game_demo.main:main', 
        ],
    },

)