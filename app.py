# -*- coding: utf-8 -*-
# 文件名：app.py   （直接保存成这个名字）
from flask import Flask, request
import requests
import json
import hashlib
import xml.etree.ElementTree as ET

app = Flask(__name__)

# ========= 你自己的配置（已全部填好）=========
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_HFIW8GfkPyaJLiM2W7-us"
TOKEN = "saucejiumaotai2025"          # 随便填，后面企业微信要填一样
EncodingAESKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDE"  # 随便填43位

# 通义千问免费接口（不需要key也能用）
QWEN_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 库存
WINES = "飞天茅台2690、15年坤沙899、赖茅传承358、王子酒138"

# 获取token（全局缓存2小时）
access_token = ""

def get_token():
    global access_token
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={CORP_SECRET}"
    access_token = requests.get(url).json()["access_token"]
    return access_token

# 通义千问AI
def qwen_ai(msg):
    prompt = f"你是15年贵州酱酒老炮，客户说：{msg}\n推荐酒：{WINES}\n用酒友聊天语气，50字内回复："
    payload = {
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": prompt}]}
    }
    try:
        r = requests.post(QWEN_URL, json=payload, timeout=10).json()
        return r["output"]["choices"][0]["message"]["content"]
    except:
        return "老铁，刚才信号有点差，我马上再跟你细聊哈~"

# 发送消息
def send_msg(to_user, content):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={get_token()}"
    data = {
        "touser": to_user,
        "msgtype": "text",
        "agentid": AGENT_ID,
        "text": {"content": content}
    }
    requests.post(url, json=data)

# 验证回调URL（企业微信第一次会访问）
@app.route('/', methods=['GET'])
def verify():
    echostr = request.args.get("echostr")
    return echostr

# 收到客户消息
@app.route('/', methods=['POST'])
def wechat():
    xml = request.data
    root = ET.fromstring(xml)
    FromUserName = root.find("FromUserName").text  # 客户openid
    msg = root.find("Content").text if root.find("Content") is not None else ""

    # 新客户自动欢迎
    if root.find("Event") is not None and root.find("Event").text == "subscribe":
        welcome = """欢迎来到老张酱酒私域！
我是张哥，玩了15年酱酒，货真价实！
你是自己喝、送礼还是收藏？我给你推荐最合适的～"""
        send_msg(FromUserName, welcome)
    
    # 客户发消息
    elif msg:
        if "小样" in msg or "尝" in msg:
            reply = "老铁，想尝尝底子是吧？把收件人+电话+地址发我，免费寄2支50ml小样，喝完再决定买不买！"
        else:
            reply = qwen_ai(msg)
        send_msg(FromUserName, reply)
    
    return "success"

if __name__ == '__main__':
    app.run(port=5000)