from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
    
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, StickerSendMessage, LocationMessage

from LineBot.models import user

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

def user_exist(user_id):
    return False

def create_new_user(user_id, name='null'):
    return

@csrf_exempt
def callback(request):
    
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
    
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
    
        for event in events:
            if isinstance(event, MessageEvent):
                if not user_exist(event.source.user_id):
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='看來您還沒有申請為使用者, 請告訴我您的本名')
                    )
                    user.objects.create(line_user_id=event.source.user_id, real_name='none', operation_status='AddUserName')
                    continue
                if event.message.text == '預約':
                    print('預約!')
                elif event.message.text == '個人設定':
                    print('個人設定!')
                elif event.message.text == '最新消息':
                    print('最新消息!')

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=event.message.text)
                )
        return HttpResponse()
    else:
        return HttpResponseBadRequest()
'''
{
"message": {
    "id": "14106814847816", "text": "\u6e2c", "type": "text"
    }, 
"mode": "active", 
"replyToken": "6ba474fc231f445482d26d17d2dc9525", 
"source": {
    "type": "user", "userId": "U5bc226fa6aea7f7243b5832df7bd5187"
    }, 
"timestamp": 1621860612220, "type": "message"
}
'''