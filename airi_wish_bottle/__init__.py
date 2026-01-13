import os
import gc
import re
import json
import time
import math
import base64
import random
import hashlib
import nonebot
import requests
import datetime
from io import BytesIO
from nonebot import get_driver, on_regex, on_startswith, on_fullmatch, require
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
import smtplib
from email.mime.text import MIMEText
from email.header import Header

timings = require("nonebot_plugin_apscheduler").scheduler
driver = get_driver()
data = {}
email_list = []

bottlehelp = on_fullmatch(('心愿瓶帮助','心愿瓶help'),priority=5,block=True)
rxyp = on_startswith('扔心愿瓶',priority=5,block=True)
jxyp = on_startswith('捡心愿瓶',priority=5,block=True)
plxyp = on_startswith('评论心愿瓶',priority=5,block=True)
wdxyp = on_fullmatch('我的心愿瓶',priority=5,block=True)
xgxyp = on_startswith('修改心愿瓶',priority=5,block=True)
zyxyp = on_startswith('转移心愿瓶',priority=5,block=True)
xhxyp = on_startswith('销毁心愿瓶',priority=5,block=True)
jbxyp = on_startswith('举报心愿瓶',priority=5,block=True)
btshenhe = on_startswith(('btapprove ','btreject '),priority=5,block=True,permission=SUPERUSER)
plshenhe = on_startswith(('plapprove ','plreject '),priority=5,block=True,permission=SUPERUSER)
jbshenhe = on_startswith(('jbapprove ','jbreject '),priority=5,block=True,permission=SUPERUSER)
pdbt = on_startswith('pending_bottle',priority=5,block=True,permission=SUPERUSER)
pdpl = on_startswith('pending_comment',priority=5,block=True,permission=SUPERUSER)
pdjb = on_fullmatch('pending_jb',priority=5,block=True,permission=SUPERUSER)

async def email_login():
    global server
    try:
        server.connect()
    except:
        server = smtplib.SMTP_SSL("XXXXXXXXXXXXXXXXXXXXXXXXX")
        server.login('XXXXXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXX')
        server.close()

@driver.on_startup
async def load_json():
    global data
    #await email_login()
    data = json.load(open(os.path.join(os.path.dirname(__file__), 'data.json'),'r'))
    gc.collect()

@driver.on_shutdown
async def save_to_json():
    global data, email_list
    json.dump(data, open(os.path.join(os.path.dirname(__file__), 'data.json'),'w', encoding="utf-8"), ensure_ascii=False)
    if len(email_list):
        try:
            sev = smtplib.SMTP_SSL("XXXXXXXXXXXXXXXXXXXXXX")
            sev.login('XXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXX')
            for mail in email_list:
                msg = MIMEText(mail[2], 'plain', 'utf-8')
                msg['From'] = f"{Header('XXXXXXXXXXXXXXXX', 'utf-8')} <XXXXXXXXXXXXXXXX>"
                msg['To'] = Header(mail[0])
                msg['Subject'] = Header(mail[1])
                sev.sendmail('XXXXXXXXXXXXXXXXXXXXXX', mail[0], msg.as_string())
            sev.quit()
            del sev
            email_list = []
        except Exception as expt:
            return str(expt)
 
async def daily_clear():
    global data
    data["comments_daily"]={}
    data["drop_daily"]=[]
    await save_to_json()

async def save_data_backup():
    await save_to_json()
    json_dir = os.path.join(os.path.dirname(__file__), "data.json")
    os.system("cp "+json_dir+" "+json_dir+".bak")

timings.add_job(daily_clear, "cron", hour=0, misfire_grace_time=3600, coalesce=True)
timings.add_job(save_data_backup, "cron", hour=23, minute=50, misfire_grace_time=3600, coalesce=True)
timings.add_job(save_to_json, "interval", minutes=5, misfire_grace_time=3600, coalesce=True)
#timings.add_job(email_login, "interval", minutes=60, misfire_grace_time=3600, coalesce=True)

#--------------------------------

async def check_weijinci(text):
    try:
        return requests.get(f'https://v2.xxapi.cn/api/detect?text={text.replace("=","")}', timeout=5).json()["data"]["is_prohibited"]
    except:
        return 1

decr=lambda x:"".join([hex(i)[2:] for i in list(base64.b64decode(x.encode()))])
encr=lambda ff:base64.b64encode(bytes([int(ff[i:i+2],16) for i in range(0,len(ff),2)])).decode()
nxcr=lambda x:encr(hex(int(decr(x),16)+1)[2:])

async def generate_unique_id(content):
    global data
    unique_id = encr(hashlib.md5(content.encode()).hexdigest()[:12])
    unique_id_list = list(data["bottles"].keys()) + list(data["pending_bottles"].keys())
    while unique_id in unique_id_list:
        unique_id = nxcr(unique_id)
    return unique_id
    
#--------------------------------

def add_bottle(unique_id, owner=-1, owner_id=-1, content=-1, comments=-1, times=-1):
    global data
    try:
        bottle_tmp = data['bottles'][unique_id]
    except:
        if owner==-1: owner = 'XXXXXXXXXXXXXXXXXXXXXX'
        if owner_id==-1: owner_id = 'XXXXXXXXXXXXXXXX'
        if content==-1: content = ''
        if comments==-1: comments = []
        if times==-1: times = 0
        data['bottles'][unique_id] = {"owner":owner,"owner_id":owner_id,"content":content,"comments":comments,"times":times}
        try:
            data['collections'][owner_id].append(unique_id)
        except:
            data['collections'][owner_id] = [unique_id]
    else:
        for i in range(len(data['collections'][bottle_tmp["owner_id"]])):
            if data['collections'][bottle_tmp["owner_id"]][i] == unique_id:
                data['collections'][bottle_tmp["owner_id"]].pop(i)
                break
        if owner!=-1: bottle_tmp['owner'] = str(owner)
        if owner_id!=-1: bottle_tmp['owner_id'] = str(owner_id)
        if content!=-1: bottle_tmp['content'] = str(content)
        if comments!=-1: bottle_tmp['comments'] = comments
        if times!=-1: bottle_tmp['times'] = int(times)
        data['bottles'][unique_id] = bottle_tmp
        try:
            data['collections'][owner_id].append(unique_id)
        except:
            data['collections'][owner_id] = [unique_id]

def delete_bottle(unique_id):
    global data
    try:
        user_id = data['bottles'][unique_id]['owner_id']
    except:
        pass
    else:
        del data['bottles'][unique_id]
        for i in range(len(data['collections'][user_id])):
            if data['collections'][user_id][i] == unique_id:
                data['collections'][user_id].pop(i)
                break
                
def sync_bottle():
    global data
    collections = {}
    for i in data["bottles"].keys():
        user_id = str(data["bottles"][i]['owner_id'])
        try:
            collections[user_id].append(i)
        except:
            collections[user_id] = [i]
    data["collections"] = collections
    del collections
    gc.collect()

def send_email(dest, subject, text):
    global email_list
    email_list.append([dest, subject, text])

#--------------------------------

@rxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id)
    src = str(ev.message).strip()
    if src == "扔心愿瓶":
        await rxyp.finish('💫 指令用法：扔心愿瓶 内容', reply_message = True)
    src = [0,src[4:].strip()]
    '''
    if user_id in data["drop_daily"]:
        await rxyp.finish('❌ 今天已经扔过心愿瓶了，明天再来吧......', reply_message = True)
    '''
    #src[1] = src[1].strip()
    if len(src[1]) > 500:
        await rxyp.finish(f'❌ 心愿长度超出500字限制，请重新填写！当前字数：{len(src[1])}', reply_message = True)
    #data["drop_daily"].append(user_id)
    iswj = await check_weijinci(src[1])
    if iswj:
        unique_id = await generate_unique_id(src[1])
        data['pending_bottles'][unique_id] = {"owner":user_nick,"owner_id":user_id,"content":src[1],"comments":[],"times":0}
        await bot.send_private_msg(user_id=XXXXXXXXXXXXXXXX,message=f'📛 心愿瓶审核：{unique_id}\n{src[1]}')
        await rxyp.finish('❌ 未通过机器审核，请等待人工审核。人工审核结果将会以邮件形式告知。', reply_message = True)
    else:
        unique_id = await generate_unique_id(src[1])
        '''
        data['bottles'][unique_id]={"owner":user_nick,"owner_id":user_id,"content":src[1],"comments":[],"times":0}
        try:
            data['collections'][user_id]
        except:
            data['collections'][user_id] = [unique_id]
        else:
            data['collections'][user_id].append(unique_id)
        '''
        add_bottle(unique_id, user_nick, user_id, src[1], [], 0)
        await rxyp.finish(f'✅ 您的心愿瓶编号：{unique_id}，等待有缘人的开启......', reply_message = True)
        
@jxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id)
    src = str(ev.message).split(' ',1)
    if len(src) == 1:
        if src[0] == "捡心愿瓶":
            unique_id = random.choice(list(data["bottles"].keys()))
        else:
            unique_id = src[0][4:].strip()
    else:
        unique_id = src[1].strip()
    if len(unique_id) != 8:
        await jxyp.finish(f'❌ 请检查心愿瓶编号格式！', reply_message = True)
    elif unique_id not in data["bottles"].keys():
        await jxyp.finish(f'❌ 编号为{unique_id}的心愿瓶不存在！', reply_message = True)
    msg = []
    res = f'💫 {user_nick}拾取的心愿瓶'
    msg.append({"type": "node", "data": {"name": "Momoi Airi Wish Bottle", "uin": bot.self_id, "content": res}})
    res = data["bottles"][unique_id]["content"]
    msg.append({"type": "node", "data": {"name": "心愿瓶内容", "uin": bot.self_id, "content": res}})
    res = f'{unique_id}'
    msg.append({"type": "node", "data": {"name": "心愿瓶编号", "uin": bot.self_id, "content": res}})
    data["bottles"][unique_id]["times"] += 1
    res = f'心愿瓶持有者：{data["bottles"][unique_id]["owner"]}\n\
被拾取次数：{data["bottles"][unique_id]["times"]}'
    msg.append({"type": "node", "data": {"name": "心愿瓶基本信息", "uin": bot.self_id, "content": res}})
    res = "暂无评论" if not len(data["bottles"][unique_id]["comments"]) else '//: '.join(data["bottles"][unique_id]["comments"][::-1])
    msg.append({"type": "node", "data": {"name": "心愿瓶评论", "uin": bot.self_id, "content": res}})
    await bot.send_group_forward_msg(group_id=ev.group_id, messages=msg)
    del msg, res
    gc.collect()

@plxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id)
    src = str(ev.message).split()
    if len(src) <= 2:
        await jxyp.finish('💫 指令用法：评论心愿瓶 编号 评论内容', reply_message = True)
    else:
        unique_id = src[1].strip()
    if len(unique_id) != 8:
        await jxyp.finish(f'❌ 请检查心愿瓶编号格式！', reply_message = True)
    elif unique_id not in data["bottles"].keys():
        await jxyp.finish(f'❌ 编号为{unique_id}的心愿瓶不存在！', reply_message = True)
    try:
        data["comments_daily"][user_id]
    except:
        data["comments_daily"][user_id] = 0
    if data["comments_daily"][user_id] > 10:
        await jxyp.finish(f'❌ 该账号今日可评论次数已达上限', reply_message = True)
    comment = " ".join(src[2:])
    if len(comment) > 20:
        await rxyp.finish(f'❌ 评论长度超出20字限制，请重新填写！当前字数：{len(comment)}', reply_message = True)
    data["comments_daily"][user_id] += 1
    iswj = await check_weijinci(comment)
    if iswj:
        uqid = await generate_unique_id(comment)
        comment_unique_id = str(time.time()) + '_' + uqid
        data['pending_comment'][comment_unique_id]={"comment_to":unique_id,"from":user_nick+'_'+user_id,"content":comment}
        await bot.send_private_msg(user_id=XXXXXXXXXXXXXXXX,message=f'📛 评论审核：{unique_id}\n{comment}')
        await rxyp.finish('❌ 未通过机器审核，请等待人工审核。人工审核结果将会以邮件形式告知。', reply_message = True)
    else:
        data['bottles'][unique_id]['comments'].append(comment)
        if len(data['bottles'][unique_id]['comments']) > 30:
            data['bottles'][unique_id]['comments'].pop(0)
        await rxyp.finish(f'✅ 已评论编号为{unique_id}的心愿瓶：{comment}', reply_message = True)

@wdxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id)
    try:
        data['collections'][user_id]
    except:
        data['collections'][user_id] = []
    msg = []
    res = f'💫 昵称：{user_nick}\nQQ号：{user_id}\n你总共有{len(data["collections"][user_id])}个心愿瓶'
    msg.append({"type": "node", "data": {"name": "Momoi Airi Wish Bottle", "uin": bot.self_id, "content": res}})
    res = ''
    for unique_id in data['collections'][user_id]:
        res += f'心愿瓶编号：{unique_id}\n内容摘要：{data["bottles"][unique_id]["content"][:8]}\n\n'
    if len(res): msg.append({"type": "node", "data": {"name": "我的心愿瓶", "uin": bot.self_id, "content": res.strip()}})
    await bot.send_group_forward_msg(group_id=ev.group_id, messages=msg)
    del msg, res
    gc.collect()

@xgxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id)   
    src = str(ev.message).split()
    if len(src) <= 2:
        await jxyp.finish('💫 指令用法：修改心愿瓶 编号 内容', reply_message = True)
    else:
        unique_id = src[1].strip()
    if len(unique_id) != 8:
        await jxyp.finish(f'❌ 请检查心愿瓶编号格式！', reply_message = True)
    elif unique_id not in data["bottles"].keys():
        await jxyp.finish(f'❌ 编号为{unique_id}的心愿瓶不存在！', reply_message = True)
    if data["bottles"][unique_id]["owner_id"] != user_id:
        await jxyp.finish(f'❌ 你不是该心愿瓶的拥有者！', reply_message = True)
    #comment = " ".join(src[2:])
    comment = str(ev.message)
    comment = comment[comment.find(unique_id)+8:].strip()
    iswj = await check_weijinci(comment)
    if iswj:
        data['pending_bottles'][unique_id]={"owner":user_nick,"owner_id":user_id,"content":comment,"comments":data["bottles"][unique_id]["comments"],"times":data["bottles"][unique_id]["times"]}
        await rxyp.finish('❌ 未通过机器审核，请等待人工审核。人工审核结果将会以邮件形式告知。', reply_message = True)
    else:
        data['bottles'][unique_id]['owner'] = user_nick
        data['bottles'][unique_id]['content'] = comment
        await rxyp.finish(f'修改成功', reply_message = True)
        
@zyxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id) 
    #await jxyp.finish('❌ 该功能暂未开放', reply_message = True)
    src = str(ev.message).split()
    if len(src) != 3:
        await jxyp.finish('💫 指令用法：转移心愿瓶 编号 @...', reply_message = True)
    else:
        unique_id = src[1].strip()
    if len(unique_id) != 8:
        await jxyp.finish(f'❌ 请检查心愿瓶编号格式！', reply_message = True)
    elif unique_id not in data["bottles"].keys():
        await jxyp.finish(f'❌ 编号为{unique_id}的心愿瓶不存在！', reply_message = True)
    if data["bottles"][unique_id]["owner_id"] != user_id:
        await jxyp.finish(f'❌ 你不是该心愿瓶的拥有者！', reply_message = True)
    try:
        cq_code = re.findall(r'\[CQ:at,qq=\d+.*\]',src[2].strip())[0]
        transfer_id = re.findall('\d+',cq_code)[0]
        transfer_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=transfer_id)
        transfer_nick = (transfer_nick.get("nickname") or transfer_nick.get("card") or transfer_id) 
        add_bottle(unique_id, transfer_nick, transfer_id)
    except:
        await jxyp.finish('❌ 系统繁忙，请稍后再试......', reply_message = True)
    else:
        await jxyp.finish(f'✅ 操作成功！您已将编号为{unique_id}的心愿瓶转交给{transfer_nick}', reply_message = True)
    
@xhxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id) 
    src = str(ev.message).split()
    if len(src) != 2:
        await jxyp.finish('💫 指令用法：销毁心愿瓶 编号', reply_message = True)
    else:
        unique_id = src[1].strip()
    if len(unique_id) != 8:
        await jxyp.finish(f'❌ 请检查心愿瓶编号格式！', reply_message = True)
    elif unique_id not in data["bottles"].keys():
        await jxyp.finish(f'❌ 编号为{unique_id}的心愿瓶不存在！', reply_message = True)
    if data["bottles"][unique_id]["owner_id"] != user_id:
        await jxyp.finish(f'❌ 你不是该心愿瓶的拥有者！', reply_message = True)
    '''
    del data['bottles'][unique_id]
    for i in range(len(data['collections'][user_id])):
        if data['collections'][user_id][i] == unique_id:
            data['collections'][user_id].pop(i)
            break
    '''
    delete_bottle(unique_id)
    await jxyp.finish(f'🗑️ 编号为{unique_id}的心愿瓶已销毁', reply_message = True)
    
@jbxyp.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    session_id = str(ev.get_session_id())
    if 'group' in session_id:
        split_id = session_id.split("_")
        user_id = split_id[2]
        gruop_id = split_id[1]
    else:
        user_id = session_id
        gruop_id = None
    user_nick = await bot.get_group_member_info(group_id=gruop_id, user_id=user_id)
    user_nick = (user_nick.get("nickname") or user_nick.get("card") or user_id)   
    src = str(ev.message).split()
    if len(src) <= 2:
        await jxyp.finish('💫 指令用法：举报心愿瓶 编号 举报理由', reply_message = True)
    else:
        unique_id = src[1].strip()
    if len(unique_id) != 8:
        await jxyp.finish(f'❌ 请检查心愿瓶编号格式！', reply_message = True)
    elif unique_id not in data["bottles"].keys():
        await jxyp.finish(f'❌ 编号为{unique_id}的心愿瓶不存在！', reply_message = True)
    comment = " ".join(src[2:])
    jb_unique_id = str(time.time()) + '_' + unique_id
    data['pending_jb'][jb_unique_id] = {'jbr':f'{user_nick}_{user_id}','unique_id':unique_id,'comment':comment}
    await bot.send_private_msg(user_id=XXXXXXXXXXXXXXXX,message=f'📛 举报审核：{jb_unique_id}')
    await jxyp.finish(f'💬 您的举报已收到，请等待核实......', reply_message = True)

@bottlehelp.handle()
async def _(bot: Bot, ev: MessageEvent):
    msg = []  
    res = '“セカイ”それは、『本当の想い』を見つけられる場所——初音 ミク\n\
「世界」，那是一个能找到“真正的心愿”的地方。——初音未来\n\n\
心愿，是心灵的信使，载着未曾言说的困惑、隐秘的期待或温柔的故事，穿越茫茫人海，飘扬在充满希望的「世界」中。何不抛却身份束缚，匿名书写真实自我，或许下一秒，就有陌生灵魂拾起你的心愿，以文字共鸣，开启一场不期而遇的治愈对话。\n\n\
💫 欢迎使用 爱莉心愿瓶\n\
（Momoi Airi Wish Bottle）'
    msg.append({"type": "node", "data": {"name": "Momoi Airi Wish Bottle", "uin": bot.self_id, "content": res}})
    '''
    res = '该插件为v0.0.1元初版，所有功能都在测试中，欢迎向田麻小溪反映bug。'
    msg.append({"type": "node", "data": {"name": "小提示", "uin": bot.self_id, "content": res}})
    '''
    res = '📒 指令列表：\n\
 -扔心愿瓶 [内容]：记下你的心愿并装入具有唯一编号的心愿瓶内，等待有缘人的开启。\n\
 -捡心愿瓶：随机捡起一个心愿瓶阅读。\n\
 -捡心愿瓶 [编号]：捡起特定编号的心愿瓶阅读。\n\
 -评论心愿瓶 [编号] [评论内容]：在特定编号的心愿瓶里写下你的评论。\n\
 -我的心愿瓶：查看本人持有的心愿瓶情况。\n\
 -修改心愿瓶 [编号] [内容]：修改本人持有的特定编号心愿瓶里的心愿内容。\n\
 -转移心愿瓶 [编号] [@...]：将你所持有的特定编号的心愿瓶转交给你@的人。\n\
 -销毁心愿瓶 [编号]：将你所持有的特定编号的心愿瓶销毁。\n\
 -举报心愿瓶 [编号] [举报理由]：如果你发现特定编号的心愿瓶中存在违规内容，举报一下！（奖励见下）\n\n\
*注意：参数之间请使用空格隔开！\n\
正确示范：捡心愿瓶 xxx\n\
错误示范：捡心愿瓶xxx'
    msg.append({"type": "node", "data": {"name": "指令列表", "uin": bot.self_id, "content": res}})
    
    res = '☑️ 游戏玩法：\n\
类似于漂流瓶。\n\
相较于普通漂流瓶，爱莉心愿瓶的提供了更多有趣的玩法。'
    msg.append({"type": "node", "data": {"name": "游戏玩法", "uin": bot.self_id, "content": res}})
    
    res = '☑️ 心愿上限为500字，不支持图片。\n\
每人每天可发表十条评论，单条评论上限为20字，一条心愿最多保留30条评论。'
    msg.append({"type": "node", "data": {"name": "一些限制", "uin": bot.self_id, "content": res}})
    
    res = '☑️ 任何心愿瓶的内容及评论都需经过多道审核工序。\n\
如果当场通过机器审核，心愿瓶编号会当场发放。如果未通过机器审核转人工，会在审核之后决定是否发放。\n\
举报心愿瓶，经核实情况属实，奖励举报人还未被其他人持有的特定编号心愿瓶一个（编号由你决定）。多次恶意举报或多次投放恶意内容者，奖励爱莉永久黑名单特权。'
    msg.append({"type": "node", "data": {"name": "内容审核", "uin": bot.self_id, "content": res}})
    
    res = '☑️ 这一栏介绍扔心愿瓶时，唯一编号的生成算法。\n\
爱莉会将心愿内容过一遍md5哈希，得到一段32位长的0-f字符串。取前12位用base64编码，得到对应的8位心愿瓶编号。如果编号已经存在，就自然往后挪动一位，直到找到可用编号为止。\n\
有本事的话，用你的技术力去争夺属于你的唯一编号吧。'
    msg.append({"type": "node", "data": {"name": "心愿瓶编号的生成算法", "uin": bot.self_id, "content": res}})

    msg.append({"type": "node", "data": {"name": "版权信息", "uin": bot.self_id, "content": 'Powered By airi_wish_bottle\nAuthor：Makino.S'}})     
    await bot.send_group_forward_msg(group_id=ev.group_id, messages=msg)
    del msg, res
    gc.collect()
    
@pdbt.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    res = ''
    for unique_id in data['pending_bottles'].keys():
        res += f'ID：{unique_id}\n来源：{data["pending_bottles"][unique_id]["owner"]}_{data["pending_bottles"][unique_id]["owner_id"]}\n内容：{data["pending_bottles"][unique_id]["content"]}\n\n'
    res = res.strip()
    if not len(res): res = "暂无"
    await superuser_debug.finish(res, reply_message = True)
    
@pdpl.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    res = ''
    for unique_id in data['pending_comment'].keys():
        # {"comment_to":unique_id,"from":user_id,"content":comment}
        res += f'评论来源ID：{data["pending_comment"][unique_id]["comment_to"]}\n评论人QQ：{data["pending_comment"][unique_id]["from"]}\n评论内容：{data["pending_comment"][unique_id]["content"]}\n\n'
    res = res.strip()
    if not len(res): res = "暂无"
    await superuser_debug.finish(res, reply_message = True)
    
@pdjb.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    res = ''
    for unique_id in data['pending_jb'].keys():
        # {'jbr':f'{user_nick}_{user_id}','unique_id':unique_id,'comment':comment}
        res += f'举报人：{data["pending_jb"][unique_id]["jbr"]}\n举报ID：{data["pending_jb"][unique_id]["unique_id"]}\n举报理由：{data["pending_jb"][unique_id]["comment"]}\n\n'
    res = res.strip()
    if not len(res): res = "暂无"
    await superuser_debug.finish(res, reply_message = True)

@btshenhe.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    src = str(ev.message).split()
    if len(src) != 2:
        await jxyp.finish('格式错误', reply_message = True)
    else:
        unique_id = src[1].strip()
    if src[0] == 'btapprove' and unique_id == 'all':
        pd_bt = list(data["pending_bottles"].keys())
        for unique_id in pd_bt:
            if unique_id in data["bottles"].keys():
                if data["bottles"][unique_id]['owner_id'] == data["pending_bottles"][unique_id]['owner_id']:
                    data["bottles"][unique_id] = data["pending_bottles"][unique_id]
                else:
                    unique_id_tmp = await generate_unique_id(data["pending_bottles"][unique_id]["content"])
                    data["bottles"][unique_id_tmp] = data["pending_bottles"][unique_id]
                    unique_id = unique_id_tmp                    
            else:
                data["bottles"][unique_id] = data["pending_bottles"][unique_id]
            try:
                data['collections'][data["pending_bottles"][unique_id]['owner_id']]
            except:
                data['collections'][data["pending_bottles"][unique_id]['owner_id']] = []
            data['collections'][data["pending_bottles"][unique_id]['owner_id']].append(unique_id)
            send_email(f'{data["bottles"][unique_id]["owner_id"]}@qq.com', f'您的心愿瓶{unique_id}已通过审核', f'尊敬的{data["bottles"][unique_id]["owner"]}：\n    您的心愿瓶“{data["bottles"][unique_id]["content"][:20]+("......" if len(data["bottles"][unique_id]["content"])>20 else "")}”已通过人工审核，编号为 {unique_id} ，感谢使用爱莉心愿瓶。\n\n此致，\nMomoi Airi 开发团队')
            del data["pending_bottles"][unique_id]
    elif src[0] == 'btreject' and unique_id == 'all':
        for unique_id in data['pending_bottles'].keys():
            send_email(f'{data["pending_bottles"][unique_id]["owner_id"]}@qq.com', f'您的心愿瓶{unique_id}未通过审核', f'尊敬的{data["pending_bottles"][unique_id]["owner"]}：\n    您的心愿瓶“{data["pending_bottles"][unique_id]["content"][:20]+("......" if len(data["pending_bottles"][unique_id]["content"])>20 else "")}”未通过人工审核。如果对审核结果有异议，可于收到该邮件发送邮件至saki@saki.ln.cn申请复核。\n\n此致，\nMomoi Airi 开发团队')
        data["pending_bottles"] = {}
    elif unique_id not in data["pending_bottles"].keys():
        await jxyp.finish(f'编号为{unique_id}的心愿瓶不存在！', reply_message = True)
    elif src[0] == 'btapprove':
        if unique_id in data["bottles"].keys():
            if data["bottles"][unique_id]['owner_id'] == data["pending_bottles"][unique_id]['owner_id']:
                data["bottles"][unique_id] = data["pending_bottles"][unique_id]
            else:
                unique_id_tmp = unique_id
                while unique_id_tmp in data["bottles"].keys():
                    unique_id_tmp = nxcr(unique_id_tmp)
                data["bottles"][unique_id_tmp] = data["pending_bottles"][unique_id]
                unique_id = unique_id_tmp
        else:
            data["bottles"][unique_id] = data["pending_bottles"][unique_id]
        try:
            data['collections'][data["pending_bottles"][unique_id]['owner_id']]
        except:
            data['collections'][data["pending_bottles"][unique_id]['owner_id']] = []
        data['collections'][data["pending_bottles"][unique_id]['owner_id']].append(unique_id)
        send_email(f'{data["bottles"][unique_id]["owner_id"]}@qq.com', f'您的心愿瓶{unique_id}已通过审核', f'尊敬的{data["bottles"][unique_id]["owner"]}：\n    您的心愿瓶“{data["bottles"][unique_id]["content"][:20]+("......" if len(data["bottles"][unique_id]["content"])>20 else "")}”已通过人工审核，编号为 {unique_id} ，感谢使用爱莉心愿瓶。\n\n此致，\nMomoi Airi 开发团队')
        del data["pending_bottles"][unique_id]
    elif src[0] == 'btreject':
        send_email(f'{data["pending_bottles"][unique_id]["owner_id"]}@qq.com', f'您的心愿瓶{unique_id}未通过审核', f'尊敬的{data["pending_bottles"][unique_id]["owner"]}：\n    您的心愿瓶“{data["pending_bottles"][unique_id]["content"][:20]+("......" if len(data["pending_bottles"][unique_id]["content"])>20 else "")}”未通过人工审核。如果对审核结果有异议，可于收到该邮件三日内发送邮件至saki@saki.ln.cn申请复核。\n\n此致，\nMomoi Airi 开发团队')
        del data["pending_bottles"][unique_id]
    await jxyp.finish('操作成功', reply_message = True)
    
@plshenhe.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    src = str(ev.message).split()
    if len(src) != 2:
        await jxyp.finish('格式错误', reply_message = True)
    else:
        unique_id = src[1].strip()
    if src[0] == 'plapprove' and unique_id == 'all':
        pd_pl = list(data["pending_comment"].keys())
        for unique_id in pd_pl:
            data['bottles'][data["pending_comment"][unique_id]["comment_to"]]['comments'].append(data["pending_comment"][unique_id]["content"])
            if len(data['bottles'][data["pending_comment"][unique_id]["comment_to"]]['comments']) > 30:
                data['bottles'][data["pending_comment"][unique_id]["comment_to"]]['comments'].pop(0)
            send_email(f'{data["pending_comment"][unique_id]["from"].split("_")[1]}@qq.com', f'您的评论{unique_id[-8:]}已通过审核', f'尊敬的{data["pending_comment"][unique_id]["from"].split("_")[0]}：\n    您的评论“{data["pending_comment"][unique_id]["content"]}”已通过人工审核，感谢使用爱莉心愿瓶。\n\n此致，\nMomoi Airi 开发团队')
            del data["pending_comment"][unique_id]
    elif src[0] == 'plreject' and unique_id == 'all':
        for unique_id in data["pending_comment"].keys():
            send_email(f'{data["pending_comment"][unique_id]["from"].split("_")[1]}@qq.com', f'您的评论{unique_id[-8:]}未通过审核', f'尊敬的{data["pending_comment"][unique_id]["from"].split("_")[0]}：\n    您的评论“{data["pending_comment"][unique_id]["content"]}”未通过人工审核。如果对审核结果有异议，可于收到该邮件三日内发送邮件至saki@saki.ln.cn申请复核。\n\n此致，\nMomoi Airi 开发团队')
        data["pending_comment"] = {}
    elif unique_id not in data["pending_comment"].keys():
        await jxyp.finish(f'编号错误', reply_message = True)
    elif src[0] == 'plapprove':
        data['bottles'][data["pending_comment"][unique_id]["comment_to"]]['comments'].append(data["pending_comment"][unique_id]["content"])
        if len(data['bottles'][data["pending_comment"][unique_id]["comment_to"]]['comments']) > 30:
            data['bottles'][data["pending_comment"][unique_id]["comment_to"]]['comments'].pop(0)
        send_email(f'{data["pending_comment"][unique_id]["from"].split("_")[1]}@qq.com', f'您的评论{unique_id[-8:]}已通过审核', f'尊敬的{data["pending_comment"][unique_id]["from"].split("_")[0]}：\n    您的评论“{data["pending_comment"][unique_id]["content"]}”已通过人工审核，感谢使用爱莉心愿瓶。\n\n此致，\nMomoi Airi 开发团队')    
        del data["pending_comment"][unique_id]
    elif src[0] == 'plreject':
        send_email(f'{data["pending_comment"][unique_id]["from"].split("_")[1]}@qq.com', f'您的评论{unique_id[-8:]}未通过审核', f'尊敬的{data["pending_comment"][unique_id]["from"].split("_")[0]}：\n    您的评论“{data["pending_comment"][unique_id]["content"]}”未通过人工审核。如果对审核结果有异议，可于收到该邮件三日内发送邮件至saki@saki.ln.cn申请复核。\n\n此致，\nMomoi Airi 开发团队')
        del data["pending_comment"][unique_id]
    await jxyp.finish('操作成功', reply_message = True)
    
@jbshenhe.handle()
async def _(bot: Bot, ev: MessageEvent):
    global data
    src = str(ev.message).split()
    if len(src) != 2:
        await jxyp.finish('格式错误', reply_message = True)
    else:
        unique_id = src[1].strip()
    if src[0] == 'jbapprove' and unique_id == 'all':
        pd_jb = list(data["pending_jb"].keys())
        for unique_id in pd_jb :
            #user_id = data['bottles'][data["pending_jb"][unique_id]["unique_id"]]['owner_id']
            send_email(f'{data["pending_jb"][unique_id]["jbr"].split("_")[1]}@qq.com', f'您的举报{unique_id[-8:]}已通过审核', f'尊敬的{data["pending_jb"][unique_id]["jbr"].split("_")[0]}：\n    您举报的编号为 {data["pending_jb"][unique_id]["unique_id"]} 的心愿瓶经核实，违规情况成立，目前开发团队已依规处理该心愿瓶。感谢您为爱莉萝卜做出的贡献。\n    凭该邮件可申领自定义编号心愿瓶一个，请联系saki@saki.ln.cn。\n\n此致，\nMomoi Airi 开发团队')    
            del data["pending_jb"][unique_id]
            '''
            del data['bottles'][data["pending_jb"][unique_id]["unique_id"]]
            for i in range(len(data['collections'][user_id])):
                if data['collections'][user_id][i] == unique_id:
                    data['collections'][user_id].pop(i)
                    break
            '''
    elif src[0] == 'jbreject' and unique_id == 'all':
        for unique_id in data["pending_jb"].keys():
            send_email(f'{data["pending_jb"][unique_id]["jbr"].split("_")[1]}@qq.com', f'您的举报{unique_id[-8:]}未通过审核', f'尊敬的{data["pending_jb"][unique_id]["jbr"].split("_")[0]}：\n    您举报的编号为 {data["pending_jb"][unique_id]["unique_id"]} 的心愿瓶经核实，未发现违规情况，请谅解。如果对审核结果有异议，可于收到该邮件三日内发送邮件至saki@saki.ln.cn申请复核。\n\n此致，\nMomoi Airi 开发团队')    
        data["pending_jb"] = {}
    elif unique_id not in data["pending_jb"].keys():
        await jxyp.finish(f'编号错误', reply_message = True)
    elif src[0] == 'jbapprove':
        #user_id = data['bottles'][data["pending_jb"][unique_id]["unique_id"]]['owner_id']
        send_email(f'{data["pending_jb"][unique_id]["jbr"].split("_")[1]}@qq.com', f'您的举报{unique_id[-8:]}已通过审核', f'尊敬的{data["pending_jb"][unique_id]["jbr"].split("_")[0]}：\n    您举报的编号为 {data["pending_jb"][unique_id]["unique_id"]} 的心愿瓶经核实，违规情况成立，目前开发团队已依规处理该心愿瓶。感谢您为爱莉萝卜做出的贡献。\n    凭该邮件可申领自定义编号心愿瓶一个，请联系saki@saki.ln.cn。\n\n此致，\nMomoi Airi 开发团队')    
        del data["pending_jb"][unique_id]
        '''
        del data['bottles'][data["pending_jb"][unique_id]["unique_id"]]
        for i in range(len(data['collections'][user_id])):
            if data['collections'][user_id][i] == unique_id:
                data['collections'][user_id].pop(i)
                break
        '''
    elif src[0] == 'jbreject':
        send_email(f'{data["pending_jb"][unique_id]["jbr"].split("_")[1]}@qq.com', f'您的举报{unique_id[-8:]}未通过审核', f'尊敬的{data["pending_jb"][unique_id]["jbr"].split("_")[0]}：\n    您举报的编号为 {data["pending_jb"][unique_id]["unique_id"]} 的心愿瓶经核实，未发现违规情况，请谅解。如果对审核结果有异议，可于收到该邮件三日内发送邮件至saki@saki.ln.cn申请复核。\n\n此致，\nMomoi Airi 开发团队')
        del data["pending_jb"][unique_id]
    await jxyp.finish('操作成功', reply_message = True)
