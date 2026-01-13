import os, time
from nonebot import on_fullmatch, on_startswith
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import MessageEvent

last_notice = 0

dklmt = on_startswith(('打卡啦摩托','打卡拉摩托','大卡拉摩托','大卡啦摩托'), priority=99)
wdh = on_startswith(('汪大吼','wonderhoi','wonderhoy','わんだほ~い '), priority=99,ignorecase=True)
ngg = on_startswith("你过关", priority=99)
cgdz = on_startswith("闯关弟子注意", priority=99)
ncddl = on_startswith("你从丹东来", priority=99)

@dklmt.handle()
async def _(bot: Bot, ev: MessageEvent):
    global last_notice
    if time.time() - last_notice > 10:
        last_notice = time.time()
        message = MessageSegment.record(os.path.join(os.path.dirname(__file__), 'dklmt.wav'))   
        await dklmt.send(message)
    
@wdh.handle()
async def _(bot: Bot, ev: MessageEvent):
    global last_notice
    if time.time() - last_notice > 10:
        last_notice = time.time()
        message = MessageSegment.record(os.path.join(os.path.dirname(__file__), 'wdh.wav'))
        await wdh.send(message)

@ngg.handle()
async def _(bot: Bot, ev: MessageEvent):
    global last_notice
    if time.time() - last_notice > 10:
        last_notice = time.time()
        message = MessageSegment.record(os.path.join(os.path.dirname(__file__), 'ngg.wav'))
        await ngg.send(message)
        
@cgdz.handle()
async def _(bot: Bot, ev: MessageEvent):
    global last_notice
    if time.time() - last_notice > 10:
        last_notice = time.time()
        message = MessageSegment.record(os.path.join(os.path.dirname(__file__), 'cgdz.wav'))
        await cgdz.send(message)

@ncddl.handle()
async def _(bot: Bot, ev: MessageEvent):
    global last_notice
    if time.time() - last_notice > 10:
        last_notice = time.time()
        message = MessageSegment.record(os.path.join(os.path.dirname(__file__), 'ncddl.wav'))
        await ncddl.send(message)
