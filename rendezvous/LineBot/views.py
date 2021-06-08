from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
    
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
from LineBot.models import Reservation, Location, User, Message, Report

import time

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
            user = User.objects.filter(line_user_id=event.source.user_id)
            user_status = user[0].operation_status.split(',')

            if isinstance(event, MessageEvent):
                if not user.count(): # Confirm whether the user exists.
                    User.objects.create(line_user_id=event.source.user_id, real_name='none', operation_status='ChangingUserName')
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='看來您還沒有申請為使用者, 請告訴我您的本名是 ?')
                    )
                    continue
                
                # Continue unfinished operations.
                if not user_status[0] == 'Normal':
                    print(user_status[0])
                    if user_status[0] == 'ChangingUserName':
                        user.update(line_user_id=event.source.user_id, real_name=event.message.text, operation_status='Normal')
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text='新名稱設定完成\nHi, {}!'.format(event.message.text))
                        )
                    elif user_status[0] == 'ReportProblem':
                        Report.objects.create(author=user[0].real_name, content=event.message.text)
                        user.update(operation_status='Normal')
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
                                text='選擇一個功能',
                                actions=[                              
                                    MessageTemplateAction(
                                        label='建立新的預約',
                                        text='建立新的預約'
                                    ),
                                    MessageTemplateAction(
                                        label='查看所有預約',
                                        text='查看所有預約'
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
                    locations_button_list = []
                    for location in  Location.objects.all():
                        locations_button_list.append(
                            PostbackTemplateAction(
                                label=location.name,
                                text=location.name,
                                data='CreateNewReservation&'+location.name
                            ))
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='選擇想預約的地點',
                            template=ButtonsTemplate(
                                title='建立新的預約',
                                text='選擇一個地點',
                                actions=locations_button_list
                            )
                        )
                    )
                    user.update(operation_status='CreateNewReservation')
                elif event.message.text == '查看現有的預約':
                    print('顯示現有預約, 不須提供button功能')
                elif event.message.text == '查看所有預約':
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='選擇想查看的日期',
                            template=ButtonsTemplate(
                                text='選擇想查看日期',
                                title=postback_data[1],
                                actions=[
                                    DatetimePickerTemplateAction(
                                        label='選擇',
                                        data='CheckAllReservationInSomeday&',
                                        mode='date',
                                    )
                                ]
                            )
                        )
                    )
                    user.update(operation_status='CheckAllReservationInSomeday')
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

            elif isinstance(event, PostbackEvent):
                print('postback:', event.postback)

                postback_data = event.postback.data.split('&')
                print(postback_data)

                if event.postback.params:
                    if postback_data[0] == 'CheckAllReservationInSomeday':
                        pass
                    elif postback_data[0] == 'CreateNewReservation':
                        Reservation.objects.create(location=postback_data[1], line_user_id=user[0].line_user_id, reservation_time=event.postback.params['datetime'])
                        reserv_location = Location.objects.filter(name=postback_data[1])[0]
                        line_bot_api.reply_message(
                            event.reply_token,
                            TemplateSendMessage(
                                alt_text='預約成功！',
                                template=CarouselTemplate(
                                    columns=[
                                        CarouselColumn(
                                            thumbnail_image_url='https://obs.line-scdn.net/0hH5cxhBnQFxpeAQHV8I9oTX9cHHhtYwkRfGdfeHwASS1xN1IiMGQNfy9VSnkjOQdNNTJffxUBQXgjNFZLZyJZKS8EG3ohOQ/f256x256',
                                            title='預約成功！',
                                            text='地點：{}\n預約時間：{}  {}'.format(postback_data[1], event.postback.params['datetime'][0:10], event.postback.params['datetime'][11::]),
                                            actions=[
                                                URITemplateAction(
                                                    label='官方網站',
                                                    uri=reserv_location.official_website_link
                                                ),
                                                URITemplateAction(
                                                    label='路線規劃',
                                                    uri=reserv_location.maps_link
                                                ),
                                                PostbackTemplateAction(
                                                    label='刪除此預約',
                                                    text='刪除預約',
                                                    data='CheckDeleteReservation&{}'.format(Reservation.objects.filter(line_user_id=user[0].line_user_id).order_by('created_at').reverse().first().pk)
                                                )
                                            ]
                                        )
                                    ]
                                )
                            )
                        )
                        user.update(operation_status='Normal')

                elif postback_data[0] == 'CreateNewReservation':
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='選擇想預約的時間',
                            template=ButtonsTemplate(
                                text='選擇想預約的時間',
                                title='{} 的預約'.format(postback_data[1]),
                                actions=[
                                    DatetimePickerTemplateAction(
                                        label='選擇',
                                        data=event.postback.data,
                                        mode='datetime',
                                    )
                                ]
                            )
                        )
                    )

                elif postback_data[0] == 'CheckDeleteReservation':
                    target_location = Reservation.objects.filter(pk=postback_data[1])[0]
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='確認是否刪除',
                            template=ConfirmTemplate(
                                title='確認是否刪除',
                                text='確定要刪除在\n{}\n{}\n的預約嗎？'.format(target_location.location, target_location.reservation_time.strftime('%Y-%m-%d %H:%M')),
                                actions=[                              
                                    PostbackTemplateAction(
                                        label='是',
                                        text='是',
                                        data='DeleteReservation&{}'.format(postback_data[1])
                                    ),
                                    MessageTemplateAction(
                                        label='否',
                                        text='是'
                                    )
                                ]
                            )
                    )
                    )
                elif postback_data[0] == 'DeleteReservation':
                    Reservation.objects.filter(pk=postback_data[1]).delete()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='刪除預約成功！')
                    )

        return HttpResponse()
    else:
        return HttpResponseBadRequest()
