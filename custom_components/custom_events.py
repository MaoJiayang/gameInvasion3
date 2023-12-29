from .constants import CustomConstants as Constants
from invasionEngine.events import Event
import pymunk
class HitEvent(Event):
    def __init__(self, source, target, damage):
        super().__init__(source, target)
        self.event_type:int = Constants.HIT_EVENT
        self.damage:float = damage

class KineticHitEvent(Event):
    def __init__(self, source, target,speed:pymunk.vec2d = 0,mass: float = 0):
        super().__init__(source, target)
        self.event_type:int  = Constants.KINETIC_HIT_EVENT
        self.speed:pymunk.vec2d = speed
        self.mass:float = mass

class RadarSearchEvent(Event):
    def __init__(self,source,echo_type:int,target = None):
        """
        source:雷达发射源
        echo_type:雷达反射源类型,参考custom_components.constants.CustomConstants游戏对象类型常量
        target:处理探测逻辑的对象。
        """
        super().__init__(source, target)
        self.event_type:int  = Constants.RADAR_SEARCH
        self.echo_type:int = echo_type

class RadarEchoEvent(Event):
    def __init__(self, source, target):
        super().__init__(source, target)#source是发射源，target是反射源。这里为上级的目标也设为源是为了方便事件处理器发送事件
        self.event_type:int  = Constants.RADAR_ECHO