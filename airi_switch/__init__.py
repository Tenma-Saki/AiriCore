import os
import time
import nonebot
from nonebot import on_fullmatch, require, get_driver
from nonebot.message import event_preprocessor
from nonebot.permission import SUPERUSER
from nonebot.adapters import Bot as BaseBot, Event as BaseEvent
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
import json
from datetime import datetime, timezone, timedelta

async def decimal_to_quaternary(decimal_num):
    if decimal_num == 0:
        return "0"    
    quaternary = ""
    num = decimal_num
    while num > 0:
        remainder = num % 4
        quaternary = str(remainder) + quaternary
        num = num // 4    
    return quaternary[::-1]

async def format_qq_data(data_list):   
    UTC_PLUS_8 = timezone(timedelta(hours=8))
    msg = []
    for user in data_list:
        output_lines = []
        nickname = user.get('nickname', user.get('nick', 'N/A'))
        qq_number = user.get('uin', '0')
        reg_timestamp = user.get('reg_time', 0)
        reg_time = "未知"
        if reg_timestamp > 0:
            dt = datetime.fromtimestamp(reg_timestamp, tz=UTC_PLUS_8)
            reg_time = dt.strftime("%Y年%m月%d日 %H:%M:%S")
        qq_level = user.get('qqLevel', 0)
        qid = user.get('qid', 'N/A')
        is_vip = user.get('is_vip', False)
        vip_level = user.get('vip_level', 0)
        vip_info = ('\n' + f"是，VIP等级：{vip_level}") if is_vip else "否"
        output_lines.append(f"=== {nickname} ===")
        output_lines.append(f"-QQ号：{qq_number}")
        output_lines.append(f"-QID：{qid if len(qid) else '无'}")
        qq_level_signal = ['⭐', '🌙', '☀️', '👑', '🐧']
        qq_level_str2 = ''
        if qq_level == 0:
            qq_level = "未知"
        else:
            qq_level_str1 = await decimal_to_quaternary(qq_level)
            for i in range(len(qq_level_str1)):
                for j in range(int(qq_level_str1[i])):
                    qq_level_str2 += qq_level_signal[i]
        #output_lines.append(f"-注册时间：{reg_time}")
        output_lines.append(f"-QQ等级：{qq_level} {qq_level_str2[::-1]}".strip())
        output_lines.append(f"-是否为VIP及VIP等级：{vip_info}")
        msg.append({"type": "node", "data": {"name": nickname, "uin": qq_number, "content": '\n'.join(output_lines)}})
    return msg

reloader = require('nonebot_plugin_reboot').Reloader
timing = require("nonebot_plugin_apscheduler").scheduler
timing.add_job(reloader.reload, "cron", hour=23, minute=55, misfire_grace_time=3600, coalesce=True)

driver = get_driver()
@driver.on_bot_connect
async def remind(bot: Bot):
    try:
        user_nick = await bot.get_group_member_info(group_id=XXXXXXXXXXXXXX, user_id=bot.self_id)
        user_nick = (user_nick.get("card") or user_nick.get("nickname") or user_id)
        await bot.send_private_msg(user_id=XXXXXXXXXXXXXX, message=f'{user_nick} 已上线！')
    except:
        return

airi_query_accounts = on_fullmatch('airiquery', priority=5, block=True, permission=SUPERUSER)
@airi_query_accounts.handle()
async def _(bot: Bot, ev: MessageEvent):
    qq_list = [x.self_id for x in nonebot.get_bots().values()]
    data_list = []
    for qq in qq_list:
        qqinfo = await bot.get_stranger_info(user_id=qq)
        data_list.append(qqinfo)
    res = await format_qq_data(data_list)
    await bot.send_group_forward_msg(group_id=ev.group_id, messages=res)
