from custom_scenes.main_game import MainGame
from start_menu.game_start_screen import GameStartScreen
from start_menu.story_teller import StoryTeller
import cProfile
texts = [
        "二十一世纪中叶，宇宙探索热潮再启。\n少年吉诺坐在电脑前，屏幕上的新闻标题不停变换。",
        "人们在社交网络上激烈探讨。\n“时光流转，科技的脚步不停歇。超越光速，第四次工业革命已经到来。”\n“科学的奇迹在星际间交相辉映，外来星球的电磁信号解析成功。”\n“地球文明的孤岛已被打破。世界工业大会开幕，本期主题：守护文明。”\n“跃迁引擎横空出世，先遣队成立，他们将冲锋在前，为人类的未来开疆拓土。”",
        "新闻上大大的跃迁标志，逐渐变淡，变成钢印，投射到工厂正在生产的引擎上。\n流水线移动，“跃迁”型引擎被打好标签，套壳装袋，运往各大船厂。\n飞船装载上引擎。转瞬间，引擎轰鸣，力场涌动，超越宇宙第三速度，飞向深空……",
        "宇宙的深处，星河灿烂。\n一片黑布抖出，意欲遮蔽星河光辉，却只能蒙住人类的眼睛，创造出无边黑暗的假象。\n而就在这片黑暗中，一场大战拉开序幕，片名浮出水面...\n做好迎接挑战的准备吧！"
    ]

def main():
    MainGame().loop()
# sc = GameStartScreen()
# st = StoryTeller()
# if sc.run():
#     st.run(texts)
#     cProfile.run('main()')
cProfile.run('main()','performance.txt')
    

# if GameStartScreen().run():
#     StoryTeller().run(texts)
#     MainGame().loop()
