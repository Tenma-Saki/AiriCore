import os
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import GroupIncreaseNoticeEvent
from nonebot.adapters.onebot.v11.bot import Bot, MessageSegment

intro = """Lovely！Fairy！Momoi Airi！
Momoi Airi 爱莉萝卜是一款基于AiriCoreᵀᴹ的高性能群聊bot，人物原型取自手游Project SEKAI。
airi提供PJSK查卡功能，签到、漂流瓶等娱乐功能，更多功能请发送 help 查看。
bot一群：1030569383
bot二群：808085026
airi是完全公益的，不接受任何形式的收费和赞助。如果你遇到收费拉群、索要赞助等情况，请联系bot主举报！
bot主联系邮箱：saki@saki.ln.cn
"""

group_increase = on_notice(priority=5, block=False)

@group_increase.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    global intro
    try:
        bot_id = int(bot.self_id)
        user_id = event.user_id
        
        if user_id == bot_id:
            group_id = event.group_id
       
            await bot.send_group_msg(group_id=group_id, message=MessageSegment.text(intro)+MessageSegment.image(os.path.join(os.path.dirname(__file__), 'airi.jpg')))
            
    except Exception as e:
        logger.error(f"处理入群事件时发生错误：{str(e)}", exc_info=True)







