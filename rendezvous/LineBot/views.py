from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
    
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, StickerSendMessage, LocationMessage, ButtonsTemplate, ConfirmTemplate, TemplateSendMessage, MessageTemplateAction

from LineBot.models import Reservation, Location, User, Message, Report

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


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
                user = User.objects.filter(line_user_id=event.source.user_id)
                if not user.count(): # Confirm whether the user exists.
                    User.objects.create(line_user_id=event.source.user_id, real_name='none', operation_status='ChangingUserName')
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='看來您還沒有申請為使用者, 請告訴我您的本名是 ?')
                    )
                    continue
                
                # Continue unfinished operations.
                user_status = user[0].operation_status
                if not user_status == 'None':
                    if user_status == 'ChangingUserName':
                        user.update(real_name=event.message.text, operation_status='None')
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text='新名稱設定完成\nHi, {}!'.format(event.message.text))
                        )
                    elif user_status == 'ChoosingReservationLocation':
                        print('輸出可預約時間')
                        user.update(operation_status='ChoosingTimePeriod')
                        print('接收可預約時間')
                    elif user_status == 'ChoosingTimePeriod':
                        print('建立預約')
                        print('回覆預約資訊')
                        user.update(operation_status='None')
                    elif user_status == 'ChoosingCancelReservation':
                        print('刪除所選預約')
                        user.update(operation_status='None')
                    elif user_status == 'ReportProblem':
                        Report.objects.create(author=user[0].real_name, ocntent=event.message.text)
                        user.update(operation_status='None')
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text='感謝，已收到您的回報 !')
                        )

                # Commands on richmenu.
                if event.message.text == '預約':
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='預約',
                            template=ButtonsTemplate(
                                title='您今天想...?',
                                text='選擇一個功能：',
                                actions=[                              
                                    MessageTemplateAction(
                                        label='建立新的預約',
                                        text='建立新的預約'
                                    ),
                                    MessageTemplateAction(
                                        label='查看現有的預約',
                                        text='查看現有的預約'
                                    ),
                                    MessageTemplateAction(
                                        label='取消預約',
                                        text='取消預約'
                                    )
                                ]
                            )
                        )
                    )
                if event.message.text == '建立新的預約':
                    print('顯示時間表')
                    user.update(operation_status='ChoosingReservationLocation')
                elif event.message.text == '查看現有的預約':
                    print('顯示現有預約, 不須提供button功能')
                elif event.message.text == '取消預約':
                    print('顯示現有預約')
                    user.update(operation_status='ChoosingCancelReservation')
                elif event.message.text == '設定':
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='設定',
                            template=ButtonsTemplate(
                                title='嗨! {}'.format(user[0].real_name),
                                text='您今天想...?',
                                actions=[                              
                                    MessageTemplateAction(
                                        label='修改使用者名稱',
                                        text='修改使用者名稱'
                                    ),
                                    MessageTemplateAction(
                                        label='回報問題',
                                        text='回報問題'
                                    ),
                                    MessageTemplateAction(
                                        label='查看開發團隊',
                                        text='查看開發團隊'
                                    ) 
                                ]
                            )
                        )
                    )
                elif event.message.text == '修改使用者名稱':
                    user.update(operation_status='ChangingUserName')
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='請告訴我您想改成什麼名稱'.format(event.message.text))
                    )
                elif event.message.text == '最新消息':
                    msg = Message.objects.filter().order_by('created_at').reverse().first()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=msg.content)
                    )
                elif event.message.text == '回報問題':
                    user.update(operation_status='ReportProblem')
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='遇到了什麼問題嗎?\n麻煩跟我說')
                    )
                elif event.message.text == '查看開發團隊':
                    msg = Message.objects.filter().order_by('created_at').first()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=msg.content)
                    )
                print(event.message.text)

        return HttpResponse()
    else:
        return HttpResponseBadRequest()
