import os
import re
import math
from abc import ABC, abstractmethod
import pygame
import random
from .constants import Constants
from typing import Union,Tuple
import pymunk
from pymunk.pygame_util import to_pygame, from_pygame
import pygame
from pygame.mixer import Sound
from queue import Queue
import weakref
import inspect
from .events import Event
from .utils import GeometryUtils,TextureUtils
from typing import Literal, List, Dict, Tuple, Union,Any
from typing import TYPE_CHECKING, ForwardRef
if TYPE_CHECKING:
    from .game_objects import GameObject#只是用于类型提示
    from .scenes import Scene
GameObject = ForwardRef('GameObject')
Scene = ForwardRef('Scene')
pymunk.Constraint
# 组件基类
class ComponentBase(ABC):
    @abstractmethod
    def __init__(self):
        pass
    @abstractmethod
    def update(self):
        pass
    @abstractmethod
    def destroy(self):
        pass

class Camera(ComponentBase):
    '''
    摄像头系统，为游戏对象提供渲染坐标转换，将会根据游戏对象的物理坐标换算为屏幕渲染坐标
    '''
    def __init__(self, 
                 screen: pygame.Surface,
                 width: int = Constants.SCREEN_WIDTH, 
                 height: int = Constants.SCREEN_HEIGHT,
                 initial_position: Tuple[float, float] = (0, 0),
                 ):
        
        super().__init__()

        # 新增属性以存储摄像头的目标位置
        # 使用 Vec2d 替代单独的 x, y 坐标
        self.center = pymunk.Vec2d(initial_position[0], initial_position[1])
        self.target_center = pymunk.Vec2d(initial_position[0], initial_position[1])
        self.move_speed: float = 0.1  # 新增移动速度属性
        self.bottomleft: Tuple[float, float] = (self.center.x - width / 2, self.center.y - height / 2)

        self.width: int = width
        self.height: int = height
        self.screen: pygame.Surface = screen# ?似乎没有意义

        #self.focus: GameObject = None
        self.rect = pygame.Rect(0, 0, self.width, self.height)#用于表示摄像头矩形范围，用于渲染检测

        self.zoom: float = 1.0  # 新增zoom属性
        self.max_zoom: float = max(Constants.ZOOM_RANGE[0],Constants.ZOOM_RANGE[1])
        self.min_zoom: float = min(Constants.ZOOM_RANGE[0],Constants.ZOOM_RANGE[1])
        self.target_zoom: float = 1.0  # 新增target_zoom属性
        self.zoom_speed: float = 0.005  # 新增zoom_speed属性



    @property
    def focus(self):
        if self._focus is not None:
            return self._focus()
        return None

    @focus.setter
    def focus(self, game_object: GameObject):
        '''
        设置摄像头的焦点
        focus: 焦点
        取消焦点:set_focus(None)
        '''
        if game_object == None:
            self._focus == None
            return
        self._focus = weakref.ref(game_object)

    def apply(self, position: Tuple[float, float]) -> Tuple[float, float]:
        '''
        将物理坐标转换为相对于摄像头的坐标
        return: 屏幕坐标
        '''
        # 将物理坐标转换为相对于摄像头的坐标
        x, y = position[0] * self.zoom, position[1] * self.zoom  # 对物理坐标进行放缩
        x -= self.bottomleft[0]
        y -= self.bottomleft[1]
        #将相对于摄像头的坐标转换为屏幕坐标，y轴反转
        screen_position = (x, self.height - y)
        return screen_position#返回屏幕坐标
    
    def zooming(self,step: float = 0) -> float:
        '''
        缩放摄像头.调用此方法除了可以缩放摄像头，还可以获取当前缩放值
        step: 缩放倍数步长，可以为正数或者负数
        return: 缩放后的zoom
        '''
        if step == 0:
            return self.zoom
        self.target_zoom = max(self.zoom + step, self.min_zoom)
        self.target_zoom = min(self.target_zoom, self.max_zoom)
        return self.target_zoom

    def is_in_viewport(self, target: pygame.Rect) -> bool:
        #判断目标是否在摄像头视野内，用于游戏对象渲染方法中的渲染检测
        return self.rect.colliderect(target)
    
    def update(self, target_position: Tuple[float, float] = (0,0)) -> None:
        '''
        更新摄像头位置和缩放值
        target_position: 目标位置
        有两种方式更新摄像头位置：
        1.直接指定目标位置
        2.调用方法指定一个游戏对象，摄像头会跟随游戏对象。此时不需要指定，也会忽视传入的目标位置
        非常建议使用第二种方式。
        '''
        # 更新摄像头位置
        if self.focus is not None and not self.focus.destroyed:
            target_position = (self.focus.position[0] * self.zoom, self.focus.position[1] * self.zoom)
        self.target_center = pymunk.Vec2d(target_position[0],target_position[1])
        # self.center = self.target_center

        # 逐渐改变摄像头的位置
        # 使用向量插值进行平滑移动
        self.center += (self.target_center - self.center) * self.move_speed
        
        self.bottomleft = (self.center.x - self.width / 2, self.center.y - self.height / 2)

        # 在每一帧中逐渐改变zoom属性的值
        if self.zoom < self.target_zoom:
            self.zoom = min(self.zoom + self.zoom_speed, self.target_zoom)
        elif self.zoom > self.target_zoom:
            self.zoom = max(self.zoom - self.zoom_speed, self.target_zoom)

    def destroy(self) -> None:
        self.screen = None
        self.focus = None
        print(f'摄像头{id(self)}已经被销毁')

class physicsComponent(ComponentBase):
    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        mass: float,
        space: pymunk.Space,
        body_type: Literal['dynamic', 'kinematic', 'static'] = 'dynamic',
        shape_type: Literal['box', 'circle', 'poly', 'segment'] = 'box',  
        shape_size: Union[tuple, float, list[tuple]] = (100, 50),
        elasticity: float = 1,
        friction: float = 0,
        **kwargs
    ):
        '''
        物理组件，用于创建物理体
        现已不需要传入moment，会自动根据形状和质量计算。暂不支持轴心偏移
        对于shape_size的说明：
        1.如果shape_type是'box'，则shape_size是一个tuple，表示长和宽
        2.如果shape_type是'circle'，则shape_size是一个float，表示半径
        3.如果shape_type是'poly'，则shape_size是一个list[tuple]，表示多边形的顶点坐标
        4.如果shape_type是'segment'，则shape_size是一个list[tuple]，表示线段的两个端点坐标，并接受一个额外的radius参数指定线段的半径，默认为1
        '''
        #初始化基类
        super().__init__()
        #判定body类型
        if body_type == 'dynamic':
            body_type = pymunk.Body.DYNAMIC
        elif body_type == 'kinematic':
            body_type = pymunk.Body.KINEMATIC
        elif body_type == 'static':
            body_type = pymunk.Body.STATIC
        else:
            raise ValueError(f'bodyType {body_type} not supported by physicsComponent')
        self.space = space
        
        #判定shape类型
        if shape_type == 'box':
            standardized_size = (shape_size[0]/Constants.PIXELS_PER_METER,shape_size[1]/Constants.PIXELS_PER_METER)#标准化尺寸
            self.body = pymunk.Body(mass, pymunk.moment_for_box(mass,standardized_size), body_type)#计算惯性矩并创建物理体
            self.body.position = (x, y)
            self.body.angle = angle
            self.shape = pymunk.Poly.create_box(self.body, shape_size)#创建形状
        elif shape_type == 'circle':
            standardized_size = shape_size/Constants.PIXELS_PER_METER
            self.body = pymunk.Body(mass, pymunk.moment_for_circle(mass,0,standardized_size), body_type)
            self.body.position = (x, y)
            self.body.angle = angle
            self.shape = pymunk.Circle(self.body, shape_size)
        elif shape_type == 'poly':
            standardized_size = [(x/Constants.PIXELS_PER_METER,y/Constants.PIXELS_PER_METER) for x,y in shape_size]
            self.body = pymunk.Body(mass, pymunk.moment_for_poly(mass, standardized_size), body_type)
            self.body.position = (x, y)
            self.body.angle = angle
            self.shape = pymunk.Poly(self.body, shape_size, radius=2)
            # print(pymunk.Body(mass, pymunk.moment_for_poly(mass, shape_size), body_type) == pymunk.Body(mass, pymunk.moment_for_poly(mass, standardized_size), body_type))
        elif shape_type == 'segment':
            standardized_size = [(x/Constants.PIXELS_PER_METER,y/Constants.PIXELS_PER_METER) for x,y in shape_size]
            self.body = pymunk.Body(mass, pymunk.moment_for_segment(mass,standardized_size[0], standardized_size[1], kwargs.get('radius', 1)), body_type)
            self.body.position = (x, y)
            self.body.angle = angle
            self.shape = pymunk.Segment(self.body, shape_size[0], shape_size[1], kwargs.get('radius', 1))
        else:
            raise ValueError(f'shape_type {shape_type} not supported by physicsComponent')
        self.shape.elasticity = elasticity
        self.shape.friction = friction
        space.add(self.body, self.shape)
        self.destroyed = False

    def update(self, force: tuple = (0, 0), rotation_torque: float = 0) -> None:

        if self.destroyed:
            print('物理体',self,'已经被销毁')
            return
        if self.body.space is None:
            self.destroyed = True#可能在其他地方被销毁了
            print('物理体',self,'已经被销毁')
            return

        # # 将力从世界坐标系转换到物体的局部坐标系
        # force = pymunk.Vec2d(force[0],force[1]).rotated(-self.body.angle)
        # 施加力
        self.body.apply_force_at_world_point(force, (0, 0))
        # 将这个力矩施加到物体上
        self.body.torque = rotation_torque


    def destroy(self) -> None:#销毁物理体
        self.space.remove(self.body, self.shape)
        self.space = None
        self.body = None
        self.shape = None
        self.surface = None
        self.destroyed = True
        #print('物理体',self,'已经被销毁')
    
    @property
    def center(self) -> tuple:
        return self.body.position
    
    @property
    def velocity(self) -> pymunk.vec2d:
        """经过放缩处理的速度，匹配了游戏内全局国际单位"""
        return self.body.velocity / Constants.PIXELS_PER_METER
    
    @property
    def kinetic_energy(self) -> float:
        """经过放缩处理的动能，匹配了游戏内全局国际单位"""
        return self.body.kinetic_energy / (Constants.PIXELS_PER_METER**2)
    
class PIDController(ComponentBase):
    def __init__(self, kp: float, ki: float, kd: float, setpoint: float = 0):
        #初始化基类
        super().__init__()
        self.kp = kp  # 比例系数
        self.ki = ki  # 积分系数
        self.kd = kd  # 微分系数
        self.setpoint = setpoint  # 设定点，即目标位置
        self.integral = 0  # 积分项的累积值
        self.previous_error = 0  # 上一次的误差值

    def update(self, measurement: float, setpoint: float) -> float:
        # 更新设定点
        self.setpoint = setpoint

        # 计算误差
        error = self.setpoint - measurement

        # 计算比例项
        P_value = self.kp * error

        # 计算积分项
        self.integral += error
        I_value = self.ki * self.integral

        # 计算微分项
        D_value = self.kd * (error - self.previous_error)
        self.previous_error = error

        # 计算 PID 控制器的输出
        output = P_value + I_value + D_value

        return output
    
    def destroy(self) -> None:  
        pass

class EventManager(ComponentBase):
    def __init__(self):
        super().__init__()
        self.event_queue: Queue[Event] = Queue()
        self.subscribers: Dict[int, weakref.WeakSet] = {}  # 使用字典存储订阅者和其关心的事件类型

    def add_event(self, event: Event) -> None:
        #print('事件已添加:',event)
        self.event_queue.put(event)

    def dispatch_events(self) -> None:
        while not self.event_queue.empty():
            event = self.event_queue.get()
            if event.targetAlive:
                # 如果事件有指定目标，则仅发送给目标
                event.target.handle_event(event)
                #print("事件",event,"已分发给：",event.target)
            else:
                # 如果事件没有指定目标，则根据类型调用注册的回调函数
                self.__notify_subscribers(event)
                #print('事件已分发:',event)

    def subscribe(self, subscriber: Union[GameObject,Scene], event_type: int) -> None:
        # 订阅者可以根据事件类型订阅事件
        if event_type not in self.subscribers:
            self.subscribers[event_type] = weakref.WeakSet()
        self.subscribers[event_type].add(subscriber)
        print(f'订阅者{subscriber}已订阅事件{event_type}')

    def unsubscribe(self, subscriber: Union[GameObject,Scene], event_type: int) -> None:
        # 取消订阅者对特定类型事件的订阅
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(subscriber)
        else :
            raise ValueError(f"Event type {event_type} not found in subscribers")

    def __notify_subscribers(self, event: Event) -> None:
        # 根据事件类型调用注册的回调函数
        event_type = event.event_type
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                subscriber.handle_event(event)
                #print("事件",event,"已分发给：",subscriber)

    def destroy(self) -> None:
        self.event_queue = None
        self.subscribers = None
        print(f'事件管理器{id(self)}已经被销毁')
    def update(self) -> None:
        pass

class ResourceManager(ComponentBase):
    """
    资源管理器
    用于加载和管理游戏中某个目录的资源，并加载为游戏资产
    加载完成后，可以按文件名称（不包括后缀）和类型获取资源
    当前支持的资源类型有：
    images: 图像(.png, .jpg, .jpeg, .bmp),
    image_polygons: 自动计算的图像的近似多边形轮廓
    textured_images: 使用材质填充的图像
    textures: 材质(.texture)
    sounds: 声音(.wav, .mp3, .ogg, .flac)
    """

    def __init__(self, resources_dir: str = None):
        super().__init__()
        self.images: Dict[str, pygame.Surface] = {}
        self.image_polygons: Dict[str, List[Tuple[int, int]]] = {}
        self.textures: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, Sound] = {}
        self.textured_images: Dict[str, pygame.Surface] = {}

        # 用于获取所有资源的字典
        self.resource_map: Dict[str, Dict[str, Any]] = self._get_resource_map()
        self.img_cache: SurfaceCache = SurfaceCache()  # 图像缓存
        if resources_dir:
            self.load_resources(resources_dir)

    def _get_resource_map(self) -> Dict[str, Dict[str, Any]]:
        """
        获取资源字典，以便整理每种资源按照资源名称中的数字排序
        """
        return {name: attr for name, attr in inspect.getmembers(self) if not name.startswith('_') and not inspect.ismethod(attr)}

    def load_resources(self, directory: str) -> None:
        """
        加载指定目录中的资源，并按照一定规则整理
        """
        directory = os.path.normpath(directory)  # 规范化路径
        for filename in os.listdir(directory):
            if not os.path.isfile(os.path.join(directory, filename)):
                continue
            name, ext = os.path.splitext(filename)
            if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                if name in self.images:
                    print(f"警告: 图像 {name} 已经存在，将被覆盖")
                self.images[name] = pygame.image.load(os.path.join(directory, filename))
                # 从图像中提取非透明区域的多边形轮廓
                self.image_polygons[name] = GeometryUtils.get_edge_pixels(self.images[name])
            elif ext in ['.texture']:
                if name in self.textures:
                    print(f"警告: 材质 {name} 已经存在，将被覆盖")
                self.textures[name] = pygame.image.load(os.path.join(directory, filename))
            elif ext in ['.wav', '.mp3', '.ogg', '.flac']:
                if name in self.sounds:
                    print(f"警告: 声音 {name} 已经存在，将被覆盖")
                self.sounds[name] = Sound(os.path.join(directory, filename))

        # 在所有资源加载完之后，为所有的image_polygons都创建一个填充过的Surface
        for texture_name, texture in self.textures.items():
            for polygon_name, polygon in self.image_polygons.items():
                filled_surface = TextureUtils.fill_polygon_with_texture(polygon, texture)
                self.textured_images[f"{texture_name}_{polygon_name}"] = filled_surface

        # 整理每种资源，按照资源名称中的数字排序
        for resource_type, resources in self.resource_map.items():
            self.resource_map[resource_type] = {
                k: v for k, v in sorted(
                    resources.items(),
                    key=lambda item: self.__extract_number_from_name(item[0])
                )
            }
        resource_counts = ';'.join(f"{resource_type}:{len(resources)}" for resource_type, resources in self.resource_map.items())
        print(f"资源管理器{id(self)}:{directory}加载完成。{resource_counts}")
        # 检查图像大小是否一致，如果不一致则输出提示
        if self.images:
            first_image_size = next(iter(self.images.values())).get_size()
            for name, image in self.images.items():
                if image.get_size() != first_image_size:
                    print(f"警告: {directory}中的图片尺寸不一致\n碰撞体积将会按照编号第一的图片大小计算")
                    break

    def get(self, resource_type: str, filename: str = '', with_name: bool = False) -> Union[pygame.Surface, List[pygame.Surface], Dict[str, pygame.Surface], Dict[str, Sound]]:
        """
        获取指定类型的资源。
        当前支持的资源类型有:images, image_polygons, textures, sounds, textured_images

        Args:
            resource_type: 资源类型，可选值为当前资源管理器支持的资源类型
            filename: 可以选择返回包含指定字符串的资源, 如果不指定，则返回所有资源
            with_name: 可以选择返回资源的含名称字典或者资源本身
            
        Returns:
            根据参数返回对应的资源结果
        """
        if resource_type not in self.resource_map:
            raise ValueError(f"Invalid resource type: {resource_type}, valid types are: {list(self.resource_map.keys())}")
        resources = {name: res for name, res in self.resource_map[resource_type].items() if filename in name}  # 遍历所有资源，如果资源的名称包含 filename，就将它添加到 resources 字典中
        # if not resources:
        #     print(f"资源管理器{id(self)}警告：{resource_type} resource {filename} not found in resources")
        if filename != '':
            resources = {  # 按照资源名称中的数字排序
                k: v for k, v in sorted(
                    resources.items(),
                    key=lambda item: self.__extract_number_from_name(item[0])
                )
            }
        if with_name:
            return resources
        else:
            return list(resources.values())
        
    def get_cached_image(self, original_image: pygame.Surface, zoom: float, angle: float) -> pygame.Surface:
        return self.img_cache.get(original_image, zoom, angle)
           
    def destroy(self) -> None:
        for name, attr in inspect.getmembers(self):
            if not name.startswith('_') and not inspect.ismethod(attr) and isinstance(attr, dict):
                attr.clear()
        print(f'资源管理器{id(self)}已经清空')

    def update(self) -> None:
        pass
        
    @staticmethod
    def __extract_number_from_name(name: str) -> int:
            #只会提取第一串数字
            match = re.search(r'\d+', name)
            return int(match.group()) if match else 0

class KeyboardController(ComponentBase):
    '''
    控制器类，用于获取游戏中键盘控制信号并输出控制三元组,多用于控制游戏对象
    传参时可以指定按键，需要传入pygame的按键常量，
    如果不指定则使用默认按键adwsqe
    鼠标由于已经具有类似的pygame.mouse.get_pressed()功能，所以不需要单独实现
    '''
    def __init__(self, 
                 left_key:int = pygame.K_a,
                 right_key:int = pygame.K_d,
                 up_key:int = pygame.K_w,
                 down_key:int = pygame.K_s,       
                 rotate_left_key:int = pygame.K_q, 
                 rotate_right_key:int = pygame.K_e):
        #初始化基类
        super().__init__()
        self._left_key: int = left_key
        self._right_key: int = right_key
        self._up_key: int = up_key
        self._down_key: int = down_key
        self._rotate_left_key: int = rotate_left_key
        self._rotate_right_key: int = rotate_right_key

        self.x_axis: int = 0
        self.y_axis: int = 0
        self.rotation: int = 0

    def update(self) -> None:
        keys = pygame.key.get_pressed()
        # 根据按键状态更新控制器状态
        self.x_axis = keys[self._right_key] - keys[self._left_key]
        self.y_axis = keys[self._up_key] - keys[self._down_key]
        self.rotation = keys[self._rotate_right_key] - keys[self._rotate_left_key]

    @property
    def control_values(self) -> tuple[int,int,int]:
        self.update()
        return (self.x_axis, self.y_axis, self.rotation)
    
    def destroy(self) -> None:  
        pass

import functools
class SurfaceCache(ComponentBase):
    """
    由于pygame的Surface对象创建和销毁比较耗时，所以使用缓存来管理Surface对象
    尤其是加入摄像头系统后，每帧都会对surface进行旋转和缩放，所以更需要缓存
    其接受一个key = (original_image, zoom, angle)作为索引，返回一个缓存的surface
    为了避免空间无限的增加，缓存中存储的zoom和angle有粒度，并不是连续值。
    传入的zoom和angle会被转换为最接近的缓存值
    """
    def __init__(self,zoom_granularity_factor: float = 0.003,
                 angle_granularity_factor: float = 0.004,
                 zoom_range: tuple[float,float] = Constants.ZOOM_RANGE,
                 angle_range: tuple[float,float] = (0,360)):
        super().__init__()
        self.cache: Dict[Tuple[pygame.Surface, float, float], pygame.Surface] = {}
        self.zoom_granularity: float = zoom_granularity_factor * abs(zoom_range[1] - zoom_range[0])
        self.angle_granularity: float = angle_granularity_factor * abs(angle_range[1] - angle_range[0])

    #定义一个粒度调整函数，用于将传入的zoom和angle调整为最接近的缓存值
    def __granularity_adjust(self, zoom: float, angle: float) -> float:
        adjusted_zoom = round(zoom / self.zoom_granularity) * self.zoom_granularity
        adjusted_angle = round(angle / self.angle_granularity) * self.angle_granularity
        return (adjusted_zoom,adjusted_angle)
    
    # @functools.lru_cache(maxsize = None)
    # def  __surface_process(self, original_surface: pygame.Surface, zoom: float, angle: float) -> pygame.Surface:
    #     # 缩放和旋转图像
    #     processed_surface = pygame.transform.rotozoom(original_surface, angle, zoom)#这样处理比上面的方法质量更高耗时稍长
    #     return processed_surface
    
    # def get(self, original_surface: pygame.Surface, zoom: float, angle: float) -> pygame.Surface:
    #     adjusted_zoom, adjusted_angle = self.__granularity_adjust(zoom, angle)
    #     return self.__surface_process(original_surface, adjusted_zoom, adjusted_angle)
    
    def get(self, original_surface: pygame.Surface, zoom: float, angle: float) -> pygame.Surface:
        #需要在游戏对象的render方法中调用。备注
        # 对zoom和angle应用粒度调整
        adjusted_zoom, adjusted_angle = self.__granularity_adjust(zoom, angle)

        key = (original_surface, adjusted_zoom, adjusted_angle)

        if key not in self.cache:
            # 缩放和旋转图像
            # scaled_surface = pygame.transform.scale(original_surface, (int(original_surface.get_width() * adjusted_zoom), int(original_surface.get_height() * adjusted_zoom)))
            # rotated_surface = pygame.transform.rotate(scaled_surface, adjusted_angle)
            # self.cache[key] = rotated_surface

            processed_surface = pygame.transform.rotozoom(original_surface, adjusted_angle, adjusted_zoom)#这样处理比上面的方法质量更高耗时稍长
            self.cache[key] = processed_surface
            
        return self.cache[key]
        # return pygame.transform.rotozoom(original_surface, adjusted_angle, adjusted_zoom)

    def update(self):
        super().update()
    def destroy(self):
        self.cache = None
        self.__surface_process.cache_clear()
        super().destroy()
# class Animation:
#     '''
#     动画类
#     用于播放一组图像
#     '''
#     def __init__(self, images: List[pygame.Surface], frame_duration: int = 1000, loop: bool = True):
#         self.images = images
#         self.frame_duration = frame_duration
#         self.loop = loop
#         self.last_frame_update_time = 0
#         self.image_index = 0
#         self.current_image = self.images[self.image_index]

#     def update(self) -> None:
#         # 获取当前时间
#         current_time = pygame.time.get_ticks()
#         # 计算时间差
#         time_diff = current_time - self.last_frame_update_time
#         # 如果时间差大于等于帧切换的时间间隔（例如，每100毫秒切换一次帧）
#         if time_diff >= self.frame_duration:
#             # 更新当前帧
#             self.image_index = (self.image_index + 1) % len(self.images)
#             self.current_image = self.images[self.image_index]
#             # 更新最后更新时间
#             self.last_frame_update_time = current_time

#     def reset(self) -> None:
#         self.last_frame_update_time = 0
#         self.image_index = 0
#         self.current_image = self.images[self.image_index]