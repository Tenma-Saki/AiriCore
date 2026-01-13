import re
import os
import gc
import cv2
import time
import hashlib
import nonebot
import datetime
import chinese_calendar
from nonebot import on_message, on_startswith, on_fullmatch, require
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent

tmxx_notice_time = 0
tmxx_work_status = 0 # 0 not work; 1 work
BLACKLIST = []

query_tmxx_status = on_message(priority=1,block=False)
'''
change_tmxx_work_status = on_startswith('工作状态',priority=99,block=False)
query_tmxx_work_status = on_fullmatch('查询工作状态',priority=99,block=False)

async def shangban():
    cur_time = datetime.datetime.now()
    if chinese_calendar.is_holiday(cur_time): return
    global tmxx_work_status
    tmxx_work_status = 1
    bot = list(nonebot.get_bots().values())[0]
    await bot.send_private_msg(user_id=XXXXXXXXXXXXXXXXXXXXX,message='{}\n已自动设置工作状态为：工作中'.format(str(cur_time)))
        
async def xiaban():
    cur_time = datetime.datetime.now()
    if chinese_calendar.is_holiday(cur_time): return
    global tmxx_work_status
    tmxx_work_status = 0
    bot = list(nonebot.get_bots().values())[0]
    await bot.send_private_msg(user_id=XXXXXXXXXXXXXXXXXXXXX,message='{}\n已自动设置工作状态为：下班！'.format(str(cur_time)))
    
timing = require("nonebot_plugin_apscheduler").scheduler
timing.add_job(shangban,"cron", hour=8,minute=30, misfire_grace_time=3600, coalesce=True)
timing.add_job(xiaban,"cron", hour=12, misfire_grace_time=3600, coalesce=True)
timing.add_job(shangban,"cron", hour=14,minute=30, misfire_grace_time=3600, coalesce=True)
timing.add_job(xiaban,"cron", hour=17,minute=30, misfire_grace_time=3600, coalesce=True)
'''
@query_tmxx_status.handle()
async def query_tmxx_status_func(bot: Bot, ev: MessageEvent):
    global tmxx_notice_time, tmxx_work_status, BLACKLIST
    
    # if tmxx_work_status == 0: return
    if str(ev.get_session_id()).split('_')[1] in BLACKLIST: return
    
    msg = str(ev.message).lower()

    if "image" in msg: return

    tmxx_is_mentioned = 0
    xxtp = 0
    
    keywords = []
    for keyword in keywords:
        if keyword in msg:
            tmxx_is_mentioned = 1
            break
    '''       
    if not tmxx_is_mentioned:
        at_list = re.findall(r'\[CQ:at,qq=\d+.*\]',msg)
        at_qq = []
        for i in at_list:
            at_qq.append(re.findall('\d+',i)[0])
        if 'XXXXXXXXXXXXXXXXXXXXX' in at_qq:
            tmxx_is_mentioned = 1
    '''      
    if tmxx_is_mentioned:
        #await query_tmxx_status.finish('关键词检测成功')
        cur_timing = int(time.time())
        need_notice=0
        if cur_timing - tmxx_notice_time > 600 and str(ev.get_session_id()).split('_')[1] not in BLACKLIST:
            tmxx_notice_time = cur_timing
            need_notice=1
        if 1:
            cur_time = datetime.datetime.now()
            session_id = str(ev.get_session_id())
            if 'group' in session_id:
                split_id = session_id.split('_')
                qq_id = split_id[2]
                gruop_id = split_id[1]
            else:
                qq_id = session_id
                gruop_id = None
            '''
            has = hashlib.md5()
            has.update('{} {} {} {}'.format(str(cur_time),qq_id,gruop_id,str(ev.message)).encode('utf-8'))
            has = has.hexdigest()[:16].upper()
            '''
            user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=qq_id)
            user_nick = (user_nick.get("card") or user_nick.get("nickname") or qq_id)
            gr_list = await bot.get_group_list()
            gr_name = ''
            for gr in gr_list:
                if int(gr["group_id"]) == int(gruop_id):
                    gr_name = gr["group_name"]
            #bot = list(nonebot.get_bots().values())[0]
            mesg = '📣 新消息提醒\n🕗 {}\n👨‍ {}({})\n📀 {}({})\n📩 {}'.format(str(cur_time)[:-7],user_nick,qq_id,gr_name,gruop_id,str(ev.message))
            if tmxx_work_status and need_notice and str(ev.get_session_id()).split('_')[1] not in BLACKLIST and not xxtp:
                pass
                '''
                mesg += "\n（已留言提醒）"
               	notice_png = cv2.imread(os.path.join(os.path.dirname(__file__), 'tmxx_work_notice.jpg'))
               	cv2.putText(notice_png,has,(705,460),cv2.FONT_HERSHEY_PLAIN,1.5,(255,255,255),2)
               	notice_png = cv2.imencode(".jpg", notice_png)[1].tobytes()
               	await query_tmxx_status.send(MessageSegment.text('\n(本消息由爱莉代发)\n')+MessageSegment.image(notice_png)+MessageSegment.text(f'\n{has}'),at_sender=True)
                '''
            await bot.send_private_msg(user_id=XXXXXXXXXXXXXXXXX,message=mesg)
            del gr_list
            gc.collect()
            	
            #await query_tmxx_status.finish('(调试信息)\n关键词检测成功，冷却时间20s\ntmxx:{}\ncur:{}'.format(tmxx_notice_time,cur_time))
        #else:
            #await query_tmxx_status.finish('(调试信息)\n冷却时间：{}s\ntmxx:{}\ncur:{}'.format(cur_time - tmxx_notice_time,tmxx_notice_time,cur_time))
        return
'''        
@change_tmxx_work_status.handle()
async def change_tmxx_work_status_func(bot: Bot, ev: MessageEvent):
    global tmxx_work_status
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split('_')
        qq_id = split_id[2]
        gruop_id = split_id[1]
    else:
        qq_id = session_id
        gruop_id = None
    #await bot.send(ev,'{} {}'.format(qq_id,gruop_id))
    if qq_id != 'XXXXXXXXXXXXXXXXXXXXX': return
    split_msg = str(ev.message)[4:].lstrip()
    #await bot.send(ev,str(split_msg))
    if len(split_msg) == 0: return
    if split_msg in ['1','work','上班','工作']:
        tmxx_work_status = 1
        await change_tmxx_work_status.finish('已设置田麻小溪工作状态为：工作中')
        return
    else:
        tmxx_work_status = 0
        await change_tmxx_work_status.finish('已设置田麻小溪工作状态为：下班！')
        return
        
@query_tmxx_work_status.handle()
async def query_tmxx_work_status_func(bot: Bot, ev: MessageEvent):
    global tmxx_work_status
    if tmxx_work_status:
        #notice_png = cv2.imread(os.path.join(os.path.dirname(__file__), 'tmxx_work.jpg'))
        #notice_png = cv2.imencode(".jpg", notice_png)[1].tobytes()
        #await query_tmxx_work_status.finish(MessageSegment.image(notice_png))
        await query_tmxx_work_status.finish(MessageSegment.image(os.path.join(os.path.dirname(__file__), 'tmxx_work.jpg')))
        return
    else:
        #notice_png = cv2.imread(os.path.join(os.path.dirname(__file__), 'tmxx_rest.jpg'))
        #notice_png = cv2.imencode(".jpg", notice_png)[1].tobytes()
        #await query_tmxx_work_status.finish(MessageSegment.image(notice_png))
        await query_tmxx_work_status.finish(MessageSegment.image(os.path.join(os.path.dirname(__file__), 'tmxx_rest.jpg')))
        return
'''
