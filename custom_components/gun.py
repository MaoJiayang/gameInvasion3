from invasionEngine.components import ComponentBase
from invasionEngine.game_objects import PhysicalGO
from invasionEngine.events import CreateEvent
from custom_gos.bullet import Bullet
from abc import ABC, abstractmethod
import pygame
import random
import math
from invasionEngine.components import ResourceManager
from .constants import CustomConstants as Constants
# 初始化pygame解决初始化问题
pygame.init()
#读取默认子弹资源
default_bullet_images = ResourceManager()
default_bullet_images.load_resources('resources\\bullet')
class Gun(ComponentBase,ABC):
    """
    一个发射组件，用于包装飞船发射子弹所需的属性和方法
    一般来说，对于外部的游戏对象，只需要调用update方法即可
    """
        
    def __init__(self,
                 attached_gameobject: PhysicalGO,
                 power:float = 50,
                 bullet_assers: ResourceManager = default_bullet_images,
                 bullet_type: int = Constants.BULLET,
                 bulletTTL: int = 3000,
                 bullet_mass: float = 0.5,
                 bullet_shape_type: str = 'circle',
                 fire_rate: float = 10#每秒最多发射子弹数
                ):
        """
        space: 物理空间
        screen: 屏幕
        pending_events: 事件队列，这个事件队列必须是所属游戏对象的事件队列
        power: 子弹的速度（模）
        bulletTTL: 子弹的生存时间（毫秒）
        """
        self.attached_gameobject = attached_gameobject
        self.bullet_assers = bullet_assers
        self.power = power * Constants.PIXELS_PER_METER
        self.bullet_type = bullet_type
        self.bulletTTL = bulletTTL
        self.bullet_mass = bullet_mass
        self.bullet_shape_type = bullet_shape_type
        self.min_fire_interval = 1000 / fire_rate  # Calculate the minimum interval in milliseconds
        self.last_fire_time = 0
        super().__init__()

    def _fire(self):
        """
        调用此方法发射子弹
        """
        current_time = pygame.time.get_ticks()
        if current_time - self.last_fire_time > self.min_fire_interval:
            #通过角度和速度模计算给予子弹的初速度(会受到飞船的速度影响)
            angle = math.radians(-self.attached_gameobject.angle + 90)#处理反转加90度是因为，游戏中0度是向上的，正向是顺时针。而一般数学概念中0度是向右的，正向是逆时针
            #angle = math.radians(self.attached_gameobject.angle)
            bounding_box = self.attached_gameobject.physics_part.shape.bb
            width = bounding_box.right - bounding_box.left
            height = bounding_box.top - bounding_box.bottom
            bias = max(width, height) / 2 + 10
            #将长度修正投影到x轴和y轴，并分别加到x和y上
            launchPoint = (self.attached_gameobject.position[0] + bias * math.cos(angle), 
                        self.attached_gameobject.position[1] + bias * math.sin(angle))

            initial_speed = (self.power * math.cos(angle),self.power * math.sin(angle))
            base_speed = self.attached_gameobject.physics_part.body.velocity
            initial_speed = (initial_speed[0] + base_speed[0],initial_speed[1] + base_speed[1])

            #TODO 创建一个子弹对象(子弹头朝向还有些问题)
            bulletToFire = Bullet(position=launchPoint,
                                space=self.attached_gameobject.space,
                                screen=self.attached_gameobject.screen,
                                mass=self.bullet_mass,
                                shape_type=self.bullet_shape_type,
                                assets=self.bullet_assers,
                                time_to_live=self.bulletTTL,
                                collision_type = self.bullet_type)
            #激活子弹
            bulletToFire.activate(initial_speed)
            #包装一个CreateEvent事件，将其加入代办事件队列等待事件管理器收集
            createEvent = CreateEvent(bulletToFire)
            self.attached_gameobject.pending_events.append(createEvent)
            self._play_firing_sound()
            self.last_fire_time = current_time
            return True
        return False
    @abstractmethod
    def _play_firing_sound(self):
        """播放发射音效，会在_fire方法中调用，由子类实现"""
        pass
    @abstractmethod
    def _check_trigger(self):
        """
        检查是否触发发射子弹的条件，如果满足会调用_fire.
        该方法在update方法中调用
        """
        pass

    def override_launch(self):
        """
        超控发射方法，无视当前的触发条件，直接发射子弹(原始方法无音效)
        """
        self._fire()
     
    def update(self):
        """
        更新方法，用于检查是否触发发射子弹的条件.如果触发，则调用_fire方法发射子弹
        """
        self._check_trigger()
        super().update()

    def destroy(self):
        """
        销毁方法，用于销毁该组件
        """
        self.attached_gameobject = None
        self.bullet_assers = None
        self.power = None
        self.bulletTTL = None
        super().destroy()


default_autocannon_assers = ResourceManager('resources\\autocannon')
class Autocannon(Gun):
    """
    一个自动发射组件，用于包装飞船发射子弹所需的属性和方法
    一般来说，对于外部的游戏对象，只需要调用update方法即可
    """
    def __init__(self,
                 attached_gameobject: PhysicalGO,
                 power:float = 75,
                 bullet_assers: ResourceManager = default_autocannon_assers,
                 bullet_type: int = Constants.BULLET,
                 bulletTTL: int = 3000,
                 fire_rate: float = 6):#每秒最多发射子弹数
        """
        power: 子弹的速度（模）
        bulletTTL: 子弹的生存时间（毫秒）
        """
        super().__init__(attached_gameobject,power,bullet_assers,bullet_type,bulletTTL,fire_rate=fire_rate)
        self.mouse_left_down = False
        
    def _play_firing_sound(self):
        """
        播放发射音效
        """
        sound = self.bullet_assers.get('sounds')
        sound = sound[random.randint(0,len(sound)-1)]
        sound.set_volume(0.1)
        sound.play()

    def _check_trigger(self):
        """
        检查是否触发发射子弹的条件，如果满足会调用_fire.
        该方法在update方法中调用
        机炮使用半自动，鼠标左键触发
        """
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:  # 如果左键被按下
            if not self.mouse_left_down:  # 如果之前没有按下鼠标
                self._fire()
                self.mouse_left_down = True  # 设置标志
                
        else:
            self.mouse_left_down = False

default_gatling_assers = ResourceManager('resources\gatling')
class Gatling(Gun):
    def __init__(self, attached_gameobject: PhysicalGO, power: float = 50,
                 bullet_assets: ResourceManager = default_gatling_assers,
                 bullet_type: int = Constants.BULLET, bulletTTL: int = 3000,
                 fire_rate: int = 10,
                 bullet_mass: float= 0.25):  # fire_rate as bullets per second
        super().__init__(attached_gameobject, power, bullet_assets, bullet_type, bulletTTL,bullet_mass = bullet_mass,fire_rate=fire_rate)
    def _play_firing_sound(self):
        """
        播放发射音效
        """
        sound = self.bullet_assers.get('sounds')
        sound = sound[random.randint(0,len(sound)-1)]
        sound.set_volume(0.1)
        sound.play()

    def _check_trigger(self):

        if pygame.mouse.get_pressed()[0]:
            self._fire()

default_railgun_assers = ResourceManager('resources\\railgun')
import pygame.mixer
class Railgun(Gun):
    def __init__(self, attached_gameobject: PhysicalGO, power: float = 150,
                 bullet_assets: ResourceManager = default_railgun_assers,
                 bullet_type: int = Constants.BULLET, bulletTTL: int = 3000,
                 max_charge_time: int = 2500):  # max_charge_time in milliseconds

        fire_rate = 1000 / max(1,max_charge_time-50) 
        super().__init__(attached_gameobject, power, bullet_assets, bullet_type, bulletTTL,2,fire_rate=fire_rate,bullet_shape_type='poly')
        self.current_power = 0
        self.max_charge_time = max_charge_time
        self.charge_start_time = None

    def _get_free_channel(self):
        """
        获取当前空闲的声音频道
        """
        return pygame.mixer.find_channel()
    

    def _play_firing_sound(self):
        """播放发射音效，根据蓄力百分比决定播放哪种音效"""
        if hasattr(self, 'sound_channel'):
            self.sound_channel.stop()
        # 计算蓄力百分比
        power_percent = self.current_power / self.power
        # 根据蓄力百分比选择音效
        if power_percent >= 1:
            sound_files = self.bullet_assers.get('sounds', filename='RailGun_Shot')

        else:
            sound_files = self.bullet_assers.get('sounds', filename='Autocannon_Shot')

        # 随机选择一个音效文件并播放
        sound = sound_files[random.randint(0, len(sound_files) - 1)]
        sound.set_volume(0.1)
        sound.play()

    def _check_trigger(self):
        if pygame.mouse.get_pressed()[0]:
            if self.charge_start_time is None:
                self.current_power = 0
                self.charge_start_time = pygame.time.get_ticks()
                charge_sound = self.bullet_assers.get(resource_type='sounds', filename='Charge')[0]
                charge_sound.set_volume(0.1)
                self.sound_channel = self._get_free_channel()  # 获取一个空闲的频道
                self.sound_channel.play(charge_sound)  # 播放充能音效

            # 计算充能百分比
            current_time = pygame.time.get_ticks()
            charge_duration = current_time - self.charge_start_time
            charge_percent = min(charge_duration / self.max_charge_time, 1)

            # 根据充能百分比设置 current_power
            self.current_power = self.power * charge_percent

            # 检查是否达到最大充能时间，如果是，则自动发射
            if charge_duration >= self.max_charge_time:
                self._fire()
                self.current_power = 0  # Reset current_power to zero after firing
                self.charge_start_time = None

        else:
            if self.charge_start_time is not None:#该分支用于处理非满蓄力发射
                # 停止充能音效
                max_power = self.power
                self.power = self.current_power# 磁轨炮在非满蓄力发射时，应该使用当前的current_power。所以这里需要暂时修改power
                self.current_power = 0
                self.sound_channel.stop()
                self._fire()# 发射方法是在父类中定义的，发射力度使用power
                self.charge_start_time = None
                self.power = max_power

    def override_launch(self):
        if self.charge_start_time is None:
            self.current_power = 0
            self.charge_start_time = pygame.time.get_ticks()
            charge_sound = self.bullet_assers.get(resource_type='sounds', filename='Charge')[0]
            charge_sound.set_volume(0.1)
            self.sound_channel = self._get_free_channel()  # 获取一个空闲的频道
            self.sound_channel.play(charge_sound)  # 播放充能音效

        # 计算充能百分比
        current_time = pygame.time.get_ticks()
        charge_duration = current_time - self.charge_start_time
        charge_percent = min(charge_duration / self.max_charge_time, 1)

        # 根据充能百分比设置 current_power
        self.current_power = self.power * charge_percent

        # 检查是否达到最大充能时间，如果是，则自动发射
        if charge_duration >= self.max_charge_time:
            self._fire()
            self.current_power = 0  # Reset current_power to zero after firing
            self.charge_start_time = None
        
