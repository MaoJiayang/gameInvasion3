import math
import weakref
import random
from enum import Enum, auto
from typing import Optional,Tuple,Literal
import pygame
from pygame.surface import Surface
import pymunk
from pymunk.vec2d import Vec2d
from abc import ABC, abstractmethod
from invasionEngine.constants import Constants
from invasionEngine.events import Event
from invasionEngine.components import ComponentBase
from invasionEngine.game_objects import PhysicalGO,Projectile
from invasionEngine.events import CreateEvent
from invasionEngine.components import ResourceManager
from invasionEngine.components import PIDController,ComponentBase
from invasionEngine.utils import GeometryUtils

class CustomConstants(Constants):
    #以下是事件类型常量
    HIT_EVENT: int = None
    KINETIC_HIT_EVENT: int = None
    RADAR_SEARCH: int = None
    RADAR_ECHO: int = None
    #以下是游戏对象类型常量
    SHIP: int = None
    PLAYERSHIP: int = None
    BULLET: int = None
    ENEMYSHIP: int = None
    #以下是游戏固定常量

class HitEvent(Event):
    def __init__(self, source, target, damage):
        super().__init__(source, target)
        self.event_type:int = CustomConstants.HIT_EVENT
        self.damage:float = damage

class KineticHitEvent(Event):
    def __init__(self, source, target,speed:pymunk.vec2d = 0,mass: float = 0):
        super().__init__(source, target)
        self.event_type:int  = CustomConstants.KINETIC_HIT_EVENT
        self.speed:pymunk.vec2d = speed
        self.mass:float = mass

class RadarSearchEvent(Event):
    def __init__(self,source,echo_type:int,target = None):
        """
        source:雷达发射源
        echo_type:雷达反射源类型,参考CustomConstants游戏对象类型常量
        target:处理探测逻辑的对象。
        """
        super().__init__(source, target)
        self.event_type:int  = CustomConstants.RADAR_SEARCH
        self.echo_type:int = echo_type

class RadarEchoEvent(Event):
    def __init__(self, source, target):
        super().__init__(source, target)#source是发射源，target是反射源。这里为上级的目标也设为源是为了方便事件处理器发送事件
        self.event_type:int  = CustomConstants.RADAR_ECHO

# 初始化pygame解决初始化问题
pygame.init()
#读取默认子弹资源
default_bullet_images = ResourceManager('resources\\bullet')   
default_autocannon_assers = ResourceManager('resources\\autocannon')
default_gatling_assers = ResourceManager('resources\gatling')
default_railgun_assers = ResourceManager('resources\\railgun')
class Bullet(Projectile):
    def __init__(self, 
            position: Tuple[int, int], 
            space: pymunk.space, 
            screen: Surface,
            angle: float = 0,
            mass: float = 0.5,
            shape_type: Literal['box', 'circle', 'poly'] = 'circle',
            elasticity: float = 1,
            friction: float= 0,
            assets: ResourceManager = None,
            time_to_live: int = 3000,
            collision_type: int = CustomConstants.BULLET,
            **kwargs
            ):
        '''
        子弹类
        position: 初始位置
        images: 图片列表
        space: 物理空间
        screen: 屏幕
        angle: 初始角度
        mass: 质量
        moment: 转动惯量
        shape_type: 形状类型
        elasticity: 弹性
        friction: 摩擦力
        time_to_live: 子弹存活时间（毫秒）
        '''
        super().__init__(
            position = position,
            space = space,
            screen = screen,
            angle = angle,
            mass = mass,
            shape_type = shape_type,
            elasticity = elasticity,
            friction = friction,
            assets = assets,
            time_to_live= time_to_live,
            **kwargs
        )
        self.physics_part.shape.collision_type = collision_type# 设置碰撞类型
    @property
    def bullet_type(self):
        return self.physics_part.shape.collision_type
    
class Gun(ComponentBase,ABC):
    """
    一个发射组件，用于包装飞船发射子弹所需的属性和方法
    一般来说，对于外部的游戏对象，只需要调用update方法即可
    """
        
    def __init__(self,
                 attached_gameobject: PhysicalGO,
                 power:float = 50,
                 bullet_assers: ResourceManager = default_bullet_images,
                 bullet_type: int = CustomConstants.BULLET,
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
        self.power = power * CustomConstants.PIXELS_PER_METER
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


class Autocannon(Gun):
    """
    一个自动发射组件，用于包装飞船发射子弹所需的属性和方法
    一般来说，对于外部的游戏对象，只需要调用update方法即可
    """
    def __init__(self,
                 attached_gameobject: PhysicalGO,
                 power:float = 75,
                 bullet_assers: ResourceManager = default_autocannon_assers,
                 bullet_type: int = CustomConstants.BULLET,
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

class Gatling(Gun):
    def __init__(self, attached_gameobject: PhysicalGO, power: float = 50,
                 bullet_assets: ResourceManager = default_gatling_assers,
                 bullet_type: int = CustomConstants.BULLET, bulletTTL: int = 3000,
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

import pygame.mixer
class Railgun(Gun):
    def __init__(self, attached_gameobject: PhysicalGO, power: float = 150,
                 bullet_assets: ResourceManager = default_railgun_assers,
                 bullet_type: int = CustomConstants.BULLET, bulletTTL: int = 3000,
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

class Gyroscope(ComponentBase):
    #陀螺仪组件，用于控制施加于飞船上的力矩(或者任意一维量的控制)
    def __init__(self,stop_threshold: float = 0.3,
                 max_torque: float = 5000,
                 kp:float = 1000,
                 ki:float = 0.5,
                 kd:float = 100000
                 ) -> None:

        super().__init__()
        self.stop_threshold=stop_threshold, 

        if type(self.stop_threshold) != float:#如果停止阈值是一个有一个元素的元组，则取出元组的第一个元素。否则报错
            if len(self.stop_threshold) == 1:
                self.stop_threshold = self.stop_threshold[0]
            else:#这是个莫名其妙的错误，不知道为什么会出现。明明输入的是一个元组，但是却不是一个元组
                raise TypeError("stop_threshold must be a tuple with one element or a float,get:",self.stop_threshold)
            
        self.max_torque=max_torque * CustomConstants.PIXELS_PER_METER
        self.PIDController: PIDController = PIDController(kp, ki, kd, 0)


    def level_limit(self, torque: float) -> tuple[float, float]:
        #将力矩限制在最大和最小
        if abs(torque) < self.stop_threshold:
            torque = 0
        else:
            torque = max(min(torque, self.max_torque), -self.max_torque)
        return torque
    
    def upgrade(self) -> None:
        self.max_torque += 1000

    def downgrade(self) -> None:
        if self.max_torque > 1000:
            self.max_torque -= 1000

    def update(self,current:float = 0,target:float = 0) -> float:
        '''
        根据当前角度和目标角度，输出力矩
        '''
        torque = self.PIDController.update(current, target)
        return self.level_limit(torque)
    
    def destroy(self):
        pass


class HealthSystem(ComponentBase):
    """ 游戏对象生命系统. """

    def __init__(self, max_health: int, health_bar_size: tuple[int,int] = (50, 10)):
        self.max_health: float = max_health
        self.current_health: float = max_health
        self.health_bar_size: tuple[int,int] = health_bar_size
        #如果元组中存在负数则报错
        if self.health_bar_size[0] < 0 or self.health_bar_size[1] < 0:
            raise ValueError("health_bar_size",health_bar_size,"中存在负数")
        
        #绘制血条边框
        self.bar_surface = pygame.Surface(self.health_bar_size, pygame.SRCALPHA)
        border_color = (192, 192, 192)  # 银色
        border_rect = pygame.Rect(0, 0, self.health_bar_size[0], self.health_bar_size[1])
        pygame.draw.rect(self.bar_surface, border_color, border_rect, 2)  # 最后一个参数是边框的宽度

    def take_damage(self, amount: float) -> None:
        """ 接受伤害.不论正负都是接受伤害"""
        self.current_health -= abs(amount)
        if self.current_health < 0:
            self.current_health = 0

    def heal(self, amount: float) -> None:
        """ 恢复生命值.不论正负都是恢复"""
        self.current_health += abs(amount)
        if self.current_health > self.max_health:
            self.current_health = self.max_health

    @property
    def alive(self) -> bool:
        """ Returns True if the object is still alive, otherwise False. """
        return self.current_health > 0
    @property
    def health_status(self) -> float:
        """ 返回当前生命值与最大生命值的比值. """
        return self.current_health/self.max_health#TODO:检查一下为什么当前生命会大于最大生命
    @property
    def health_bar(self) -> pygame.Surface:
        """ 返回一个血条surface. """
        green = int(255 * self.health_status)
        red = max(0,255 - green)
        color = (red, green, 0)

        # 计算血条的宽度
        health_width = int((self.health_bar_size[0] - 4) * self.health_status)  # 减去边框的宽度
        bar_surface = self.bar_surface.copy()
        # 在Surface对象上绘制血条
        pygame.draw.rect(bar_surface, color, pygame.Rect(2, 2, health_width, self.health_bar_size[1] - 4))  # 减去边框的宽度

        return bar_surface

    @property
    def current_health(self):
        return self._current_health

    @current_health.setter
    def current_health(self, value: float):
        if value > self.max_health:
            self._current_health = self.max_health
        elif value < 0:
            self._current_health = 0
        else:
            self._current_health = value
    
    def update(self) -> None:
        pass
    
    def destroy(self) -> None:  
        pass

class State(Enum):#下文NPC行为中的行为状态定义
    COLLIDE = auto()
    KEEP_DISTANCE = auto()
    ORBIT = auto()

class Behavior(ComponentBase, ABC):
    def __init__(self, game_object: PhysicalGO,random_offset:float = 2.5):
        super().__init__()
        self.game_object = game_object
        self._target: Optional[weakref.ref] = None  # 目标对象的弱引用
        self.target_position: Vec2d = Vec2d(0, 0)  # 目标位置
        self.target_angle: float = 0  # 目标角度（弧度制）
        self.state: State = State.KEEP_DISTANCE  # 初始状态
        self.random_offset:float = random_offset * Constants.PIXELS_PER_METER

        offset_x = random.uniform(-self.random_offset, self.random_offset)
        offset_y = random.uniform(-self.random_offset, self.random_offset)
        self.random_offset_vector = Vec2d(offset_x, offset_y)

    @property
    def target(self) -> Optional[PhysicalGO]:
        if self._target is not None:
            return self._target()
        return None

    @target.setter
    def target(self, target: PhysicalGO):
        self._target = weakref.ref(target)

    @abstractmethod
    def update(self) -> Tuple[Tuple[float, float], float]:
        """根据状态更新行为，并返回目标位置和角度"""
        return tuple(self.target_position), math.degrees(self.target_angle)

    def collide_behavior(self):
        """实现冲撞行为"""
        if self.target:
            self.target_position = GeometryUtils.to_vec2d(self.target.position)
            self.target_angle = self.calculate_angle_towards_target()

    def keep_distance_behavior(self, min_distance: float, max_distance: float):
        """实现保持距离行为"""
        self.random_offset_update()
        if self.target.destroyed:
            return
        if self.target is not None:
            min_distance *= Constants.PIXELS_PER_METER
            max_distance *= Constants.PIXELS_PER_METER
            game_object_position = GeometryUtils.to_vec2d(self.game_object.position)
            target_position = GeometryUtils.to_vec2d(self.target.position)

            distance_vector = game_object_position - target_position
            current_distance = distance_vector.length
            
            # 维持在最小和最大距离之间
            if current_distance < min_distance or current_distance > max_distance:
                distance_vector = distance_vector.normalized() * ((min_distance + max_distance) / 2)
            self.target_position = GeometryUtils.to_vec2d(self.target.position) + distance_vector

            # 在目标周围的范围内添加轻微随机位移
            self.target_position += self.random_offset_vector

            self.target_angle = self.calculate_angle_towards_target()


    def orbit_behavior(self, orbit_distance: float, angular_velocity: float = math.pi / 12):
        """实现环绕行为"""
        self.random_offset_update()
        if not hasattr(self, 'orbit_angle'):
            self.orbit_angle: float= 0  # 如果不存在orbit_angle，则创建一个
        if self.target:
            delta_time = (pygame.time.get_ticks() - self.game_object.last_frame_update_time) / 1000.0  # 获取时间间隔，单位为秒
            self.orbit_angle += angular_velocity * delta_time  # 增加环绕角度
            self.orbit_angle = self.orbit_angle % (2 * math.pi)  # 限制在 0 到 2pi 之间
            self.target_position = self.target.position + Vec2d(math.sin(self.orbit_angle), math.cos(self.orbit_angle)) * orbit_distance * Constants.PIXELS_PER_METER + self.random_offset_vector
            self.target_angle = self.calculate_angle_towards_target()

    def calculate_angle_towards_target(self) -> float:
        """计算应该朝向目标的角度,y+为0度，顺时针增加"""
        if self.target:
            game_object_position = GeometryUtils.to_vec2d(self.game_object.position)
            target_position = GeometryUtils.to_vec2d(self.target.position)
            diff = target_position - game_object_position
            return math.atan2(diff.x, diff.y) 
        
    def random_offset_update(self):
        #通过时间判断self.random_offset_vector是否需要更新
        if pygame.time.get_ticks() % 500 <= 2:
            offset_x = random.uniform(-self.random_offset, self.random_offset)
            offset_y = random.uniform(-self.random_offset, self.random_offset)
            self.random_offset_vector = Vec2d(offset_x, offset_y)

    def destroy(self):
        """销毁对象"""
        self.game_object = None
        super().destroy()
        
class ChaseAndAimingBehavior(Behavior):
    def __init__(self, game_object: PhysicalGO, min_distance: float = 10, max_distance: float = 20,random_offset:float = 2.5):
        """初始化行为.要设置目标，请使用target属性"""
        super().__init__(game_object,random_offset=random_offset)
        self.state = State.KEEP_DISTANCE  # 固定状态为KEEP_DISTANCE
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.previous_target_velocity = Vec2d(0, 0)
        self.previous_target_position = Vec2d(0, 0)
        self.predicted_position = Vec2d(0, 0)
        #使用自省功能检查game_object内是否有Gun类成员，如果有，则将其赋值给self.gun
        for name, value in vars(game_object).items():
            if isinstance(value, Gun):
                self.gun = value
                break
        else:
            raise Exception('Aiming行为附加的',type(game_object),'内没有Gun类成员')
        
    def calculate_lead_angle(self) -> float:
        # 一阶提前量
        if self.target != None and not self.target.destroyed:
            target_velocity = GeometryUtils.to_vec2d(self.target.physics_part.body.velocity)
            shooter_velocity = GeometryUtils.to_vec2d(self.game_object.physics_part.body.velocity)
            relative_velocity = target_velocity - shooter_velocity
            bullet_speed = self.gun.power

            lead_time = self.calculate_lead_time(relative_velocity, bullet_speed)
            predicted_position = GeometryUtils.to_vec2d(self.target.position) + relative_velocity * lead_time

            diff = predicted_position - GeometryUtils.to_vec2d(self.game_object.position)
            self.predicted_position = predicted_position
            return math.atan2(diff.x, diff.y)
        return 0.0

    def calculate_lead_time(self, relative_velocity: Vec2d, bullet_speed: float) -> float:
        # 一阶时间计算
        # 这里可能需要根据游戏的具体情况进行调整
        return relative_velocity.length / bullet_speed
    
    def update(self,allow_firing:bool = True) -> Tuple[Tuple[float, float], float]:
        """根据状态更新行为，并返回目标位置和角度"""
        for name, value in vars(self.game_object).items():
            if isinstance(value, Gun):
                self.gun = value
                # print(self.game_object,type(self.gun))
                break
        if self.target == None:
            return tuple(self.target_position), math.degrees(self.target_angle)
        self.keep_distance_behavior(self.min_distance, self.max_distance)
        # self.orbit_behavior(orbit_distance=(self.min_distance + self.max_distance) / 2)
        lead_angle = self.calculate_lead_angle()#计算提前量
        self.target_angle = lead_angle

        
        # 生成单位向量
        go_angle = math.radians(self.game_object.angle)
        current_direction = Vec2d(math.cos(go_angle), math.sin(go_angle))
        target_direction = Vec2d(math.cos(self.target_angle), math.sin(self.target_angle))

        # 计算两个向量之间的夹角
        angle_difference = math.degrees(math.acos(current_direction.dot(target_direction)))

        if abs(angle_difference) < 2 and allow_firing:# 如果角度接近目标角度，触发发射
            self.gun.override_launch()

        return tuple(self.target_position), math.degrees(self.target_angle)
    
class Thruster(ComponentBase):
    #推进器组件，用于控制飞船的出力(或者任意二维量的控制)
    def __init__(self,stop_threshold: float = 0.3,
                 maxForce: float = 500,
                 kp:float = 1000,
                 ki:float = 0,
                 kd:float = 400000
                 ) -> None:
        super().__init__()
        self.stop_threshold=stop_threshold, 

        if type(self.stop_threshold) != float:#如果停止阈值是一个有一个元素的元组，则取出元组的第一个元素。否则报错
            if len(self.stop_threshold) == 1:
                self.stop_threshold = self.stop_threshold[0]
            else:#这是个莫名其妙的错误，不知道为什么会出现。明明输入的是一个元组，但是却不是一个元组
                raise TypeError("stop_threshold must be a tuple with one element or a float,get:",self.stop_threshold)
            
        self.maxForce=maxForce * Constants.PIXELS_PER_METER
        self.xPIDController: PIDController = PIDController(kp, ki, kd)
        self.yPIDController: PIDController = PIDController(kp, ki, kd)

    def forceLevelLimit(self, force: tuple[float, float]) -> tuple[float, float]:
        #将推力限制在最大推力和最小推力之间
        forceX, forceY = force
        if abs(forceX) < self.stop_threshold:
            forceX = 0
        else:
            forceX = max(min(forceX, self.maxForce), -self.maxForce)
        if abs(forceY) < self.stop_threshold:
            forceY = 0
        else:
            forceY = max(min(forceY, self.maxForce), -self.maxForce)
        return (forceX, forceY)
    
    def upgrade(self) -> None:#推荐将1000作为最大推力最小值,500为一个等级。之后的推进器升级可以增加这个值
        self.maxForce += 500
    def downgrade(self) -> None:
        if self.maxForce > 500:
            self.maxForce -= 500

    def update(self,currentCoordinate:tuple[float,float],targetCoordinate:tuple[float,float]) -> tuple[float, float]:
        '''
        根据当前坐标和目标坐标，输出推力
        '''
        currentX, currentY = currentCoordinate
        targetX, targetY = targetCoordinate
        forceX = self.xPIDController.update(currentX, targetX)
        forceY = self.yPIDController.update(currentY, targetY)
        return self.forceLevelLimit((forceX, forceY))
    
    def destroy(self):
        pass