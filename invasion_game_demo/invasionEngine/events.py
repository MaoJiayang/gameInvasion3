#该文件中定义了游戏中的各种事件，包括飞船的被击中，飞船的爆炸等等
#事件的定义包括事件的类型，事件的源，事件的目标
#若要创建单对象的事件，请将目标设置为None
import weakref
from pygame import Surface
from .constants import Constants 

#弱引用版本
# class Event:
#     def __init__(self,source,target):
#         self._event_type = None
#         self._source = weakref.ref(source) if source is not None else None
#         self._target = weakref.ref(target) if target is not None else None

#     @property
#     def targetAlive(self):
#         return self._target and self._target() is not None
#     @property
#     def sourceAlive(self):
#         return self._source and self._source() is not None
#     @property
#     def target(self):
#         if self.targetAlive:
#             return self._target()
#         else:
#             print('target is None')
#             return None
#     @property
#     def source(self):
#         if self.sourceAlive:
#             return self._source()
#         else:
#             print('source is None')
#             return None
#     @property
#     def event_type(self):
#         return self._event_type
        
# class CreateEvent(Event):
#     def __init__(self,source):
#         super().__init__(source,None)
#         self._event_type = Constants.CREATE_GAME_OBJECT_EVENT

# class DestoryEvent(Event):
#     def __init__(self, source):
#         super().__init__(source,None)
#         self._event_type = Constants.DESTORY_GAME_OBJECT_EVENT

#强引用版本
class Event:
    def __init__(self, source, target):
        self._event_type = None
        self._source = source
        self._target = target

    @property
    def targetAlive(self):
        return self._target is not None

    @property
    def sourceAlive(self):
        return self._source is not None

    @property
    def target(self):
        if self.targetAlive:
            return self._target
        else:
            print('target is None')
            return None

    @property
    def source(self):
        if self.sourceAlive:
            return self._source
        else:
            print('source is None')
            return None

    @property
    def event_type(self):
        return self._event_type
    
    @event_type.setter
    def event_type(self, value):
        self._event_type = value

class CreateEvent(Event):
    def __init__(self, source):
        super().__init__(source, None)
        self._event_type = Constants.CREATE_GAME_OBJECT_EVENT#说明：自定义事件类型就需要使用@event_type.setter


class DestroyEvent(Event):
    def __init__(self, source):
        super().__init__(source, None)
        self._event_type = Constants.DESTROY_GAME_OBJECT_EVENT