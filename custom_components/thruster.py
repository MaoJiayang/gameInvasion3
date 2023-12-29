from invasionEngine.components import PIDController,ComponentBase
from .constants import CustomConstants as Constants
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