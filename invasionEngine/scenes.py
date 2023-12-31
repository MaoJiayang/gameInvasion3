from .constants import Constants
from abc import ABC, abstractmethod
import pygame
import pymunk
from .components import Camera,EventManager
from .constants import Constants
from .events import Event
from .game_objects import GameObject
class Scene(ABC):
    """
    Scene是游戏中的场景基类，所有场景都应该继承自该类。
    """

    def __init__(self,screen_height:int = Constants.SCREEN_HEIGHT,screen_width:int = Constants.SCREEN_WIDTH):
        """
        初始化场景。
        一些可以模块化的初始化，比如加载地图，初始化游戏对象，可以在子类另写初始化方法并在这里调用。
        还可以在这里初始化资源管理器。用于提前加载一些资源，避免在游戏中加载时卡顿。
        """
        self.all_sprites = pygame.sprite.Group()
        self.event_manager = EventManager()
        pygame.init()
        # 初始化 mixer 模块
        pygame.mixer.init()
        # 设置通道数量
        pygame.mixer.set_num_channels(64)
        self.space = pymunk.Space()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        #创建一个相机
        self.camera = Camera(self.screen,initial_position=(Constants.SCREEN_WIDTH/2,Constants.SCREEN_HEIGHT/2))
        self.running = True
        self.clock = pygame.time.Clock()  # 添加Clock对象
        

    def loop(self):
        """
        场景主循环。
        在这里调用事件管理器的事件分发方法，更新场景中的所有对象（对象在update中提交事件），渲染场景中的所有对象。
        """
        while self.running:
            self.event_dispatch()
            self.update()
            self.render()
            #TODO:在这里需要加入场景切换的逻辑
            #self.clock.tick_busy_loop(Constants.FPS)# 限制帧率
            self.clock.tick(Constants.FPS)# 限制帧率
        self.destroy()

    def event_dispatch(self):
        """
        Dispatch events in the scene.
        """
        self.event_manager.dispatch_events()

    def handle_event(self, event):
        """
        Handle a event.
        场景自身的事件处理，比如某游戏对象申请向场景中加入，场景可以在这里处理。
        场景本身在初始化的时候就向事件管理器注册了自身的事件处理方法。
        """
        pass

    @abstractmethod
    def destroy(self):
        """
        Destroy the scene and clean up resources.
        """
        pass

    @abstractmethod
    def update(self):
        """
        Update the state of the scene.
        """
        pass

    def render(self):
        """
        Render the scene.
        """
        self.screen.fill((0,0,0))
        #遍历所有精灵，渲染
        for sprite in self.all_sprites:
            sprite:GameObject
            sprite.render(self.camera)
        pygame.display.flip()
        # pygame.display.update()
class MenuScene(Scene):
    def __init__(self,title:str = 'Menu'):
        '''
        MenuScene是游戏各类菜单使用的场景。该场景不支持物理游戏对象的管理
        '''
        super().__init__()
        # 初始化场景
        # 一些可以模块化的初始化，比如加载地图，初始化游戏对象，可以在子类另写初始化方法并在这里调用。
        # 还可以在这里初始化资源管理器。用于提前加载一些资源，避免在游戏中加载时卡顿。
        pygame.display.set_caption(title)
        

        #加载精灵
        self.load_spirites()

    def update(self):
        # 更新游戏对象
        # 一般来说，更新逻辑应该在游戏对象中实现，而不是在场景中实现。
        # 但是，如果有一些特殊的更新逻辑，比如切换场景，可以在这里实现。
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.running = False

        #self.all_sprites.update(self.event_manager)
        for sprite in self.all_sprites:
            if not sprite.destroyed:
                sprite.update(self.event_manager)
        self.camera.update()

    def destroy(self):
        # 销毁场景
        # 一些可以模块化的销毁，比如销毁地图，销毁游戏对象，可以在子类另写销毁方法并在这里调用。
        # 还可以在这里销毁资源管理器。
        # 销毁所有精灵
        for sprite in self.all_sprites:
            sprite.destroy()

    def load_spirites(self):
        '''
        加载精灵
        1.创建精灵（可能需要用资源管理器读取资源）
        2.将精灵加入精灵组
        '''
        pass

from weakref import WeakValueDictionary
from .game_objects import PhysicalGO

class GameScene(Scene):
    def __init__(self,title:str = 'Game'):
        '''
        GameScene是游戏场景。该场景可以支持物理游戏对象的管理
        '''
        super().__init__()
        # 初始化场景
        # 一些可以模块化的初始化，比如加载地图，初始化游戏对象，可以在子类另写初始化方法并在这里调用。
        # 还可以在这里初始化资源管理器。用于提前加载一些资源，避免在游戏中加载时卡顿。
        pygame.display.set_caption(title)
        #加载精灵
        self.load_spirites()
        #加载地图
        self.load_map()
        # 创建一个弱引用字典，用于存储场景中所有存在的 PhysicalGO 的 shape 和对象本身，用于碰撞检测
        self.shapes_go_dict = WeakValueDictionary()
        #向事件管理器注册自身的事件处理方法
        self.event_manager.subscribe(self,Constants.CREATE_GAME_OBJECT_EVENT)

        self.last_physics_update_time = self.clock.get_time()

    def update(self):
        # 更新游戏对象
        # 一般来说，更新逻辑应该在游戏对象中实现，而不是在场景中实现。
        # 但是，如果有一些特殊的更新逻辑，比如切换场景，可以在这里实现。
        for event in pygame.event.get(pygame.QUIT):
            self.running = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.running = False
        self.camera.update()

        # 更新 shapes 字典
        for sprite in self.all_sprites:
            #self.shapes_go_dict = WeakValueDictionary()#重置字典
            if not sprite.destroyed:
                sprite.update(self.event_manager)
                if isinstance(sprite, PhysicalGO):
                    self.shapes_go_dict[sprite.shape] = sprite#TODO：被初步验证的功能。后续需要进一步实践验证
        
        self.physics_space_update()

    def physics_space_update(self):
        '''
        通过更新时间间隔计算物理世界应该走过的物理步数，来更新物理世界
        小时间间隔隔的多次循环更新可以保证物理世界的稳定性和收敛性
        '''
        # 计算需要更新的时间（毫秒）
        delta_time = pygame.time.get_ticks() - self.last_physics_update_time
        # 计算所需更新的物理步数
        physical_steps_per_frame = int(delta_time / (Constants.DELTA_TIME * 1000))
        #print(physical_steps_per_frame)
        # 更新物理世界
        for _ in range(physical_steps_per_frame):
            self.space.step(Constants.DELTA_TIME)
        self.last_physics_update_time = pygame.time.get_ticks()

    def destroy(self):
        # 销毁场景
        # 一些可以模块化的销毁，比如销毁地图，销毁游戏对象，可以在子类另写销毁方法并在这里调用。
        # 还可以在这里销毁资源管理器。

        # 销毁所有精灵
        for sprite in self.all_sprites:
            sprite.destroy()

    def handle_event(self, event: Event):
        '''
        场景自身的事件处理，比如某游戏对象申请向场景中加入，场景可以在这里处理。
        场景本身在初始化的时候就向事件管理器注册了自身的事件处理方法。
        在默认的实现中，场景只处理了创建游戏对象的事件。
        '''
        if event.event_type == Constants.CREATE_GAME_OBJECT_EVENT:
            #print('创建事件')
            #print(event.target)
            self.all_sprites.add(event.source)

    def load_spirites(self):
        '''
        加载精灵
        1.创建精灵（可能需要用资源管理器读取资源）
        2.将精灵加入精灵组
        '''
        pass

    def load_map(self):
        '''
        加载地图
        '''
        pass