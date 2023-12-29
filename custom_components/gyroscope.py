from invasionEngine.components import PIDController,ComponentBase
from .constants import CustomConstants as Constants
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
            
        self.max_torque=max_torque * Constants.PIXELS_PER_METER
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