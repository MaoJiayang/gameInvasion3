#定义一个继承自pygame.sprite.Sprite的基类，用于创建游戏中的各种对象。
#其坐标需要使用pymunk坐标作为绝对坐标。其渲染需要根据摄像机的位置进行渲染。
#方法包括：
#初始化方法：__init__(self,position:tuple[float,float],image:list(pygame.Surface),space: pymunk.Space,screen: pygame.Surface)，用于初始化对象。
#update方法：update(self,eventManager)，用于更新对象的状态。
#render方法：render(self,camera)，用于相对于摄像机渲染对象。默认根据pygame时钟每30帧切换一次图片。子类如果需要自定义渲染，需要重写此方法。
#destroy方法：destroy(self)，用于销毁对象。
#handleEvents方法：handleEvents(self,events)，用于处理事件。会在事件管理器中被注册，在事件触发时被调用。子类需要重写此方法。
#sendEvents方法：sendEvent(self,eventManager)，用于向事件管理器发送事件。该方法会在update方法中最后被调用，用于发送并清空自身的待发送事件队列。
import sys
import math
import pygame
import pymunk
from typing import List, Tuple, Union
from pygame.surface import Surface
from pygame.rect import Rect
from pygame.mixer import Sound
from pygame.sprite import Sprite
from pygame.font import Font
from pymunk.pygame_util import to_pygame, from_pygame
from pymunk.vec2d import Vec2d
from .components import Camera,physicsComponent,EventManager,ResourceManager
from .constants import Constants
from .utils import TextureUtils,GeometryUtils
from typing import TYPE_CHECKING, ForwardRef
from abc import abstractmethod
if TYPE_CHECKING:
    from .events import Event
    from .scenes import Scene
Event = ForwardRef('Event')

class GameObject(Sprite):
    def __init__(self, 
                 position: Tuple[int, int], 
                 space: pymunk.space, 
                 screen: Surface, 
                 angle: float = 0,
                 assets: ResourceManager = None,
                 texture_fill: bool = False,
                 scaling: float = 1,):
        """
        初始化游戏对象的实例。

        Args:
            position (Tuple[int, int]): 游戏对象的初始位置坐标。
            space (pymunk.space): 游戏对象所在的物理空间。
            screen (Surface): 游戏对象所在的屏幕表面。
            angle (float, optional): 游戏对象的初始角度，默认为0。
            assets (ResourceManager, optional): 资源管理器对象，用于加载游戏对象的纹理资源，默认为None。
            texture_fill (bool, optional): 是否填充游戏对象的纹理，默认为False。
            scaling (float, optional): 放缩系数，用于放大缩小物体尺寸及视角放缩，默认为1。

        Raises:
            ValueError: 如果放缩系数不是数字或小于等于0，则抛出此异常。

        """
        super().__init__()
        self.position: tuple[float,float] = position
        self.angle: float = angle
        self.load_assets(assets,texture_fill)
        self.space: pymunk.space.Space = space
        self.screen: Surface = screen
        if not isinstance(scaling, (int, float)):
            raise ValueError("scale must be a number")
        if scaling <= 0:
            raise ValueError("scale must be greater than 0")
        self.scaling: float = scaling
        self.last_frame_update_time = pygame.time.get_ticks()
        self.initial_time = self.last_frame_update_time
        self.pending_events: List[Event] = []#待发送事件队列
        self.destroyed: bool= False

    def load_assets(self,assets: ResourceManager,texture_fill:bool) -> None:
        '''
        游戏对象从资源管理器中加载资源
        重写时必须调用父类的load_assets方法。可重写资源内容如下:
        self.images: dict[str,Surface] = assets.get('images',with_name=True)
        self.texture: dict[str,Surface] = assets.get('textures',with_name=True)
        self.sounds: dict[str,Sound] = assets.get('sounds',with_name=True)
        '''
        if assets is not None:
            self.assets: ResourceManager = assets
        else: 
            self.assets = ResourceManager()
        self.image_index: int = 0
        self.texture_index: int = 0
        self.texture_fill: bool = texture_fill
        #通过assets获取图片和音频资源，默认在这里获取全部资源，后续可以根据需要在子类进行重写
        self.images: dict[str,Surface] = self.assets.get('images',with_name=True)
        self.textures: dict[str,Surface] = self.assets.get('textures',with_name=True)
        self.sounds: dict[str,Sound] = self.assets.get('sounds',with_name=True)
        #如果材质字典为空
        if self.textures == {} and self.texture_fill == True:
            self.texture_fill = False
            print(f'警告:资源管理器{id(self.assets)}无法获取材质字典，已关闭材质填充功能')
            
        if self.images == {}:
            self.current_image = Surface((100, 100), flags=pygame.SRCALPHA)
            # font = Font(None, 24)
            # text_surface = font.render('NoneImg', True, (255, 0, 0))
            # self.current_image.blit(text_surface, (50, 50))
            self.rect: Rect = self.current_image.get_rect()
            self.images: dict[str,Surface] = {'NoneImg':self.current_image}

        self.current_image: Surface = list(self.images.values())[0]
        self.rect: Rect = self.current_image.get_rect()

    def update(self, event_manager: EventManager) -> None:
        """
        更新游戏对象的状态。

        Args:
            event_manager (EventManager): 事件管理器对象。

        """
        self.animation_update()
        self.send_events(event_manager)

    def render(self, camera: Camera) -> None:
        '''
        渲染方法，用于渲染对象
        子类在重写此方法时，绝大多数情况下都应该调用父类的render方法

        Args:
            camera (Camera): 相机对象。

        '''
        screen_position = camera.apply(self.position)#坐标系变换
        zoom = self.scaling * camera.zooming()
        # 计算放缩后的边界矩形
        zoomed_width = int(self.current_image.get_width() * zoom)
        zoomed_height = int(self.current_image.get_height() * zoom)
        diagonal_length = (zoomed_width ** 2 + zoomed_height ** 2) ** 1/2#一个矩形可能旋转的区域是一个以对角线为直径的圆。新的判定rect可以以直径作为正方形rect的边长来解决旋转渲染问题
        judgement_rect = pygame.Rect(0, 0, diagonal_length, diagonal_length)
        judgement_rect.center = screen_position
        if not camera.is_in_viewport(judgement_rect):
            return
        #object_rect = pygame.Rect(0, 0,zoomed_width,zoomed_height)
        image_to_render = self.assets.get_cached_image(self.current_image, zoom, -self.angle)
        # image_to_render = pygame.transform.scale(self.current_image, (int(self.current_image.get_width() * zoom ), int(self.current_image.get_height() * zoom )))
        # image_to_render = pygame.transform.rotate(image_to_render, - self.angle)
        
        # image_to_render = pygame.transform.rotate(self.current_image, -self.angle)#渲染角度和物理角度相反
        # image_to_render = pygame.transform.scale(image_to_render, (int(image_to_render.get_width() * zoom ), int(image_to_render.get_height() * zoom )))
        rect = image_to_render.get_rect()
        rect.center = screen_position  # 设置rect的中心为screen_position
        self.rect = rect
        self.screen.blit(image_to_render, rect.topleft)  # 使用rect的左上角作为渲染位置
        

    def handle_event(self, event: Event) -> None:
        """
        处理游戏对象的事件。

        Args:
            event (Event): 事件对象。

        """
        pass

    def send_events(self, event_manager: EventManager) -> None:
        """
        将游戏对象的待处理事件发送给事件管理器。

        Args:
            event_manager (EventManager): 事件管理器对象。

        """
        for event in self.pending_events:
            event_manager.add_event(event)
            #print('游戏对象',self,'提交事件:',event)
        self.pending_events = []

    def animation_update(self):
        '''
        动画更新函数，用于更新动画帧
        （不包括渲染部分，只负责逻辑更新）
        该方法会在update方法中被调用
        子类可以重写此方法，实现自定义的动画更新
        '''
        # 获取当前时间
        current_time = pygame.time.get_ticks()
        # 计算时间差
        time_diff = current_time - self.last_frame_update_time
        # 如果时间差大于等于帧切换的时间间隔（例如，每100毫秒切换一次帧）
        if time_diff >= Constants.ANIMATION_INTERVAL:
            # 更新当前帧
            self.image_index = (self.image_index + 1) % len(self.images)
            # 更新当前材质
            if self.texture_fill == True:
                self.texture_index = (self.texture_index + 1) % len(self.textures)
                current_texture_name = list(self.textures.keys())[self.texture_index]
                current_image_name = list(self.images.keys())[self.image_index]
                textured_image_name = current_texture_name+'_'+current_image_name
                self.current_image = self.assets.get('textured_images',textured_image_name)[0]
                self.last_frame_update_time = current_time
            else:
                self.current_image = list(self.images.values())[self.image_index]
                # 更新最后更新时间
                self.last_frame_update_time = current_time

    def destroy(self) -> None:
        """
        销毁游戏对象。

        """
        self.kill()
        for attr in self.__dict__:
            setattr(self, attr, None)
        self.destroyed = True
        #使用自省功能将所有成员变量设为None


from typing import List, Tuple, Literal

class PhysicalGO(GameObject):
    '''
    物理游戏对象类。一般是动态的。
    为避免碰撞体不匹配的问题，此类物理游戏对象不可任意指定形状和尺寸，会根据图像自动确定形状和尺寸。
    不支持创建线段类型的物理对象，不支持动态碰撞体。
    创建多边形物理体会自动获取传入贴图的非透明部分轮廓。
    多边形目前仅支持凸多边形碰撞体。凹多边形会在凸包算法过程中转换为凸多边形。

    属性:
        shape: 物理部分的形状。

    方法:
        __init__: 初始化物理游戏对象。
        update: 更新物理游戏对象的状态。
        destroy: 销毁物理游戏对象。
        physical_update: 更新物理部分的状态。
        handle_event: 处理游戏事件。
    '''
    def __init__(self, 
                position: Tuple[int, int],  
                space: pymunk.space, 
                screen: Surface,
                angle: float = 0,
                mass: float = 0.5,
                shape_type: Literal['box', 'circle', 'poly'] = 'box',
                elasticity: float = 1,
                friction: float= 0,
                assets: ResourceManager = None,
                texture_fill: bool = False,
                bodyType: Literal['dynamic', 'kinematic', 'static'] = 'dynamic',
                scaling: float = 1,
                **kwargs
                 ):
        """
        初始化物理游戏对象。

        参数:
            position (Tuple[int, int]): 对象的初始位置。
            space (pymunk.space): 对象所在的pymunk空间。
            screen (Surface): 对象将被渲染的表面。
            angle (float, optional): 对象的初始角度，以弧度为单位。默认为0。
            mass (float, optional): 对象的质量。默认为0.5。
            shape_type (Literal['box', 'circle', 'poly'], optional): 对象的形状类型。默认为'box'。
            elasticity (float, optional): 对象的弹性。默认为1。
            friction (float, optional): 对象的摩擦力。默认为0。
            assets (ResourceManager, optional): 对象的资源管理器。默认为None。
            texture_fill (bool, optional): 是否用纹理填充对象的形状。默认为False。
            bodyType (Literal['dynamic', 'kinematic', 'static'], optional): 对象的身体类型。默认为'dynamic'。
            scaling (float, optional): 对象的缩放因子。默认为1。
            **kwargs: 其他关键字参数。

        抛出:
            ValueError: 如果shape_type不被PhysicalGO支持。
        """
        super().__init__(position=position, space=space, screen=screen, angle=angle, assets=assets, texture_fill=texture_fill,scaling=scaling)
        if shape_type == 'box':
            size = (self.rect.size[0] * scaling, self.rect.size[1] * scaling)
        elif shape_type == 'circle':
            size = max(self.rect.size[0], self.rect.size[1]) / 2 * scaling
        elif shape_type == 'poly':
            size = kwargs.get('shape_size', None)
            if size == None:
                size = assets.get('image_polygons')[0]
            size = GeometryUtils.scale_polygon(size, scaling)
        else:
            raise ValueError(f"shape_type {shape_type} not supported by PhysicalGO")
        
        self.physics_part: physicsComponent = physicsComponent(
            x = position[0],
            y = position[1],
            angle = angle,
            mass = mass,
            space = space,
            surface = screen,
            body_type = bodyType,
            shape_type = shape_type,
            shape_size = size,
            elasticity = elasticity,
            friction = friction,
        )

    def update(self, event_manager: EventManager) -> None:
        """
        更新物理游戏对象的状态。

        参数:
            event_manager (EventManager): 事件管理器。
        """
        if self.destroyed:
            return
        #更新动画部分
        self.animation_update()
        #更新物理部分
        self.physical_update()
        if self.destroyed:#如果在物理更新中被销毁，就不再更新
            return
        self.position = self.physics_part.body.position#一定要记得更新自己的位置（实体对齐？lol）
        self.angle = self.physics_part.body.angle%360
        #print(self.position)
        #print(self.angle)
        #self.rect.center = self.physics_part.center
        self.send_events(event_manager)

    def destroy(self) -> None:
        """
        销毁物理游戏对象。
        """
        self.kill()
        self.physics_part.destroy()
        super().destroy()
        
    
    @property
    def shape(self):
        if self.physics_part is None:
            return None
        return self.physics_part.shape  

    def physical_update(self) -> None:
        '''
        物理更新函数，用于更新物理部分
        该方法会在update方法中被调用
        子类可以重写此方法，实现自定义的物理更新
        '''
        force = (0,0)
        rotationTorque = 0
        self.physics_part.update(force,rotationTorque)

    def handle_event(self, event: Event) -> None:
        """
        处理游戏事件。交由子类重写。

        参数:
            event (Event): 要处理的事件。
        """
        pass
    

#TODO:
# 另起一类，不通过贴图而是通过指定形状和尺寸创建物理游戏对象。该类仅支持材质填充，不支持贴图。
# 该类的物理游戏对象多用于创建地图，例如墙壁等。默认为static类型，支持四类pymunk形状：box、circle、poly、segment。
# 继承自GameObject，并重写load_assets方法，在执行父类的load_assets方法后
# 直接根据传入的尺寸（也和形状有关）创建多边形轮廓，
# 并据此从self.texture中依次取出对应的值使用TextureUtils.fill_polygon_with_texture并替换。
# 由于其指定了形状和尺寸，所以其材质填充需要在创建时进行。不应该在游戏循环中大量创建该类对象。
class TerrainGO(GameObject):
    '''
    通过指定形状和尺寸创建物理游戏对象
    默认为static类型，支持四类pymunk形状：box、circle、poly、segment
    虽然形状可选，但是碰撞体统一采用poly
    创建线段时，position将被覆写为线段的中点
    '''
    def __init__(self, 
                position: Tuple[int, int],  
                space: pymunk.space, 
                screen: Surface,
                mass: float = 1,
                angle: float = 0,
                body_type: Literal['dynamic', 'kinematic', 'static'] = 'static',
                shape_type: Literal['box', 'circle', 'poly', 'segment'] = 'box',
                shape_size: Tuple[float, float] = (50, 50),
                elasticity: float = 1,
                friction: float = 0,
                assets: ResourceManager = None,
                color: Tuple[int, int, int] = (255, 0, 0),
                **kwargs
                 ):
        super().__init__(
            position=position,
            space=space,
            screen=screen,
            angle=angle,
            assets=assets,
            texture_fill = False
        )
        # 如果材质字典为空
        if self.textures == {}: 
            #使用纯色填充一个Surface,并将其作为默认材质
            texture = Surface((25, 25), flags = pygame.SRCALPHA)
            texture.fill(color)
            self.textures['default_texture'] = texture

        shape_type, shape_size = self.create_shape(shape_type, shape_size,**kwargs)#创建形状

            
        self.physics_part: physicsComponent = physicsComponent(
            x = self.position[0],
            y = self.position[1],
            angle = angle,
            mass = mass,
            space = space,
            surface = screen,
            body_type = body_type,
            shape_type = shape_type,
            shape_size = shape_size,
            elasticity = elasticity,
            friction = friction,
            radius = kwargs.get('radius', 1),
        )
        

    def create_shape(self, shape_type: Literal['box', 'circle', 'poly', 'segment'], shape_size: Union[tuple, float, list[tuple]],**kwargs) -> None:
        '''
        根据指定的形状和尺寸创建物理和多边形形状
        在__init__方法中被调用的一个筛子方法，会处理传入的参数并返回处理后的参数

        '''
        if shape_type == 'box':
            # 检查shape_size是否为tuple
            assert isinstance(shape_size, tuple), f"shape_size for box {shape_size} is not a tuple"
            # 根据长（x）宽（y）创建一个元组列表，表示形状轮廓
            size_x, size_y = shape_size
            rendering_shape = [(0, 0), (0, size_y), (size_x, size_y), (size_x, 0)]#矩形无所谓反转y轴
        elif shape_type == 'circle':
            # 检查shape_size是否为float
            assert isinstance(shape_size, (float, int)), f"shape_size for circle: {shape_size} is not a float or int"
            # 根据半径创建一个圆形Surface
            radius = shape_size
            shape = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shape, (255, 255, 255), (radius, radius), radius)
            rendering_shape = GeometryUtils.get_edge_pixels(shape)#圆无所谓反转y轴
        elif shape_type == 'poly':
            # 检查shape_size是否为list[tuple]
            assert isinstance(shape_size, list), f"shape_size for poly {shape_size} is not a list"
            # 获取矩形区域高
            size_y = max(point[1] for point in shape_size) - min(point[1] for point in shape_size)
            # 在该区域进行y轴反转
            shape = [(x, size_y - y) for x, y in shape_size]
            rendering_shape = shape_size = GeometryUtils.make_centroid(shape)
        elif shape_type == 'segment':
            shape_type = 'poly'#实际上在使用poly去实现segment功能
            point1, point2 = shape_size#获取端点
            phsycal_shape = GeometryUtils.generate_segment_from_endpoints(shape_size, kwargs.get('radius', 1))
            # 得到外切矩形的y轴长度
            size_y = max(phsycal_shape, key=lambda point: point[1])[1] - min(phsycal_shape, key=lambda point: point[1])[1]
            # 在该区域进行y轴反转
            rendering_shape = [(x, size_y - y) for x, y in phsycal_shape]
            self.position = ((point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2)
            shape_size = GeometryUtils.make_centroid(phsycal_shape)
        else:
            raise ValueError(f"shape_type {shape_type} not supported by ShapeDefinedGO")
        
        if self.images != {}:
            self.images = {}
            print('警告：ShapeDefinedGO的images属性不为空，已清空')
        # 遍历textures字典，使用TextureUtils.fill_polygon_with_texture方法填充多边形轮廓并加入images字典
        for texture_name, texture in self.textures.items():
            self.images[texture_name] = TextureUtils.fill_polygon_with_texture(rendering_shape, texture)
        return shape_type,shape_size
    
    def update(self, event_manager: EventManager) -> None:
        #更新动画部分
        self.animation_update()
        #更新物理部分
        self.physical_update()
        
        self.position = self.physics_part.body.position#一定要记得更新自己的位置（实体对齐？lol）
        self.angle = self.physics_part.body.angle
        self.send_events(event_manager)

    def physical_update(self) -> None:
        '''
        物理更新函数，用于更新物理部分
        该方法会在update方法中被调用
        子类可以重写此方法，实现自定义的物理更新
        '''
        force = (0,0)
        rotationTorque = 0
        self.physics_part.update(force,rotationTorque)

class Projectile(PhysicalGO):
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
            time_to_live: int = sys.maxsize,
            **kwargs
            ):
        '''
        抛体类，继承自PhysicalGO
        主要特性是一个有限的存活时间(毫秒)
        主要方法是activate方法，用于激活抛体赋予初速度
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
                         texture_fill = False,
                         **kwargs
                         )
        self.time_to_live = time_to_live
        self.active = False

    def activate(self, speed: Tuple[float, float] = (0, 0)):
        self.active = True
        self.physics_part.body.velocity = speed
        #通过速度计算角度
        self.physics_part.body.angle = - math.degrees(Vec2d(speed[0],speed[1]).angle) + 90


    def update(self, event_manager: EventManager) -> None:
        #获取当前时间
        current_time = pygame.time.get_ticks()
        #如果抛体存活时间超过了指定时间，则自毁
        if current_time - self.initial_time > self.time_to_live:
            self.destroy()
            self.active = False
            return
        super().update(event_manager)
        
    def destroy(self) -> None:
        super().destroy()
        self.active = False

    def handle_event(self, event: Event) -> None:
        #主要是处理碰撞之后的自身销毁事件
        if event.event_type == Constants.DESTROY_GAME_OBJECT_EVENT:
            if event.target == self:
                self.destroy()
                self.active = False
                #print('bullet destroyed')
                return