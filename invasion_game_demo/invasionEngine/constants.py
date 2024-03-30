'''
该包中定义了游戏引擎中的各种常量
在游戏引擎外，可用通过import constants后，通过访问 Constants.常量名 来访问常量
也可以通过继承Constants类来创建自定义常量
'''
import pygame
# 初始化pygame
pygame.init()
# 获取屏幕宽度和高度
infoObject = pygame.display.Info()

class ConstantMeta(type):
    #这个元类用来自动分配常量值
    USEREVENT = pygame.USEREVENT
    def __new__(cls, name, bases, attrs):
        for attr_name, attr_value in attrs.items():
            if attr_value is None:
                attrs[attr_name] = cls.USEREVENT
                cls.USEREVENT += 1
        return super().__new__(cls, name, bases, attrs)

class Constants(metaclass=ConstantMeta):
    '''
    该类中定义了游戏引擎中的各种常量
    可以通过继承Constants类来创建自定义常量
    '''
    #以下是事件类型常量
    DESTROY_GAME_OBJECT_EVENT: int = None
    CREATE_GAME_OBJECT_EVENT: int = None
    #以下是游戏对象类型常量
    TERRIAN: int = None
    GAME_OBJECT: int = None
    #以下是游戏固定常量
    #通过pygame自动获取屏幕宽高并设置为游戏窗口的宽高
    
    # SCREEN_WIDTH: int = infoObject.current_w
    # SCREEN_HEIGHT: int = infoObject.current_h
    SCREEN_WIDTH: int = 1024
    SCREEN_HEIGHT: int = 768

    # 游戏最高帧率，不管性能如何，由于pygame限制，实测最多为500
    FPS: int = 240

    # 游戏物理世界的时间步长，单位为秒。需要确保该值小于1/FPS。该值越小，物理模拟越收敛于现实情况。太小会导致预先定义的控制器效果变差
    DELTA_TIME: float = 1/3600

    #游戏对象本身动画帧切换的时间间隔，单位为毫秒
    ANIMATION_INTERVAL: int = 60

    #警告：如果多边形的边数过多，会导致碰撞变得鬼畜
    MAX_ALLOWED_POLY_EDGES: int = 200

    # 说明：质量单位为kg，时间单位为s。这两者均不需要特殊处理。
    # 而长度单位在像素（游戏显示）和米（国际单位）之间并不统一，因此需要一个系数。这个系数就是PIXELS_PER_METER
    # 每米对应的像素数.这个值的改变会影响涉及到距离物理计算的地方，比如转动惯量
    PIXELS_PER_METER: int = 50

    #游戏摄像机的缩放范围.注意，这里的缩放范围不是指摄像机的范围，而是指摄像机的缩放倍数。大数决定能放大到多大，小数决定能缩小到多小
    ZOOM_RANGE: tuple[float, float] = (0.2, 1.1)

    #游戏包名
    GAME_PACKAGE_NAME: str = 'gameInvasion3'
    
