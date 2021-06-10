from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from LineBot.models import Reservation, Location, User, Message, Report

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *

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
                '''Message Event'''
                user_status = ''
                try: # Found user and get user object
                    user = User.objects.filter(line_user_id=event.source.user_id)[0]
                    user_status = user.operation_status
                    print('{} ({}) : {}'.format(user.real_name, user.operation_status, event.message.text))
                except(IndexError): # User not found, create one and let him/her change name from none to real name.
                    User.objects.create(line_user_id=event.source.user_id, real_name='none', operation_status='ChangingUserName')
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='看來您還沒有申請為使用者, 請告訴我您的本名是 ?')
                    )
                    continue
                
                # Continue unfinished operations (without postback).
                if not user_status == 'Normal':
                    if user_status == 'ChangingUserName':
                        user.line_user_id=event.source.user_id
                        user.real_name=event.message.text
                        user.operation_status='Normal'
                        user.save()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text='新名稱設定完成\nHi, {}!'.format(event.message.text))
                        )
                    elif user_status == 'ReportProblem':
                        Report.objects.create(author=user.real_name, content=event.message.text)
                        user.operation_status='Normal'
                        user.save()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text='感謝，已收到您的回報 !')
                        )

                # Commands on richmenu.

                # 預約
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
                                    )
                                ]
                            )
                        )
                    )
                elif event.message.text == '建立新的預約':
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
                    user.operation_status='CreateNewReservation'
                    user.save()
                elif event.message.text == '查看所有預約':
                    reply_columns = []
                    for reservation in Reservation.objects.filter(line_user_id=user.line_user_id):
                        if len(reply_columns) == 5:
                            break
                        reserv_location = Location.objects.filter(name=reservation.location)[0]
                        reply_columns.append(
                            CarouselColumn(
                                thumbnail_image_url='https://obs.line-scdn.net/0hH5cxhBnQFxpeAQHV8I9oTX9cHHhtYwkRfGdfeHwASS1xN1IiMGQNfy9VSnkjOQdNNTJffxUBQXgjNFZLZyJZKS8EG3ohOQ/f256x256',
                                title='預約資訊',
                                text='地點：{}\n預約時間：{}'.format(reservation.location, reservation.reservation_time.astimezone('Asia/Taipei').strftime('%Y-%m-%d %H:%M')),
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
                                        data='CheckDeleteReservation&{}'.format(reservation.pk)
                                    )
                                ]
                            )
                        )
                    if len(reply_columns):
                        line_bot_api.reply_message(
                            event.reply_token,
                            TemplateSendMessage(
                                alt_text='所有預約',
                                template=CarouselTemplate(
                                    columns=reply_columns
                                )
                            )
                        )
                    else:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text='無預約紀錄')
                        )

                # 查看當日預約清單
                elif event.message.text == '查看當日預約清單':
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='查看當日預約清單',
                            template=ButtonsTemplate(
                                text='選擇想查看的日期',
                                title='查看當日預約清單',
                                actions=[
                                    DatetimePickerTemplateAction(
                                        label='選擇',
                                        data='CheckAllReservationInSomeday',
                                        mode='date'
                                    )
                                ]
                            )
                        )
                    )
    
                # 最新消息
                elif event.message.text == '最新消息':
                    msg = Message.objects.filter().order_by('created_at').reverse().first()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=msg.content)
                    )

                # 設定
                elif event.message.text == '設定':
                    line_bot_api.reply_message(
                        event.reply_token,
                        TemplateSendMessage(
                            alt_text='設定',
                            template=ButtonsTemplate(
                                title='嗨! {}'.format(user.real_name),
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
                    user.operation_status='ChangingUserName'
                    user.save()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='請告訴我您想改成什麼名稱'.format(event.message.text))
                    )
                elif event.message.text == '回報問題':
                    user.operation_status='ReportProblem'
                    user.save()
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
                '''Postback Event'''
                user = User.objects.filter(line_user_id=event.source.user_id)[0]

                postback_data = event.postback.data.split('&')
                print('postback：',postback_data)

                if event.postback.params:
                    print(event.postback.params)
                    if postback_data[0] == 'CheckAllReservationInSomeday':
                        date_text = event.postback.params['date']
                        reservation_people = Reservation.objects.filter(reservation_time__year=date_text[0:4], reservation_time__month=date_text[5:7], reservation_time__day=date_text[8:10]).order_by('reservation_time')
                        reply_text = '預約清單\n-----\n{}\n-----\n'.format(date_text)
                        for location in Location.objects.all():
                            reply_text += '{}：\n'.format(location.name)
                            how_many_people = 0
                            for person in reservation_people:
                                if person.location == location.name:
                                    how_many_people += 1
                                    reply_text += '\t{} - {}\n'.format(User.objects.get(line_user_id=person.line_user_id).real_name, person.reservation_time.astimezone('Asia/Taipei').strftime('%H:%M'))
                            reply_text += '共 {} 人\n\n'.format(how_many_people)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=reply_text)
                        )
                        

                    elif postback_data[0] == 'CreateNewReservation':
                        Reservation.objects.create(location=postback_data[1], line_user_id=user.line_user_id, reservation_time=event.postback.params['datetime'])
                        datetime_text = event.postback.params['datetime']
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
                                            text='地點：{}\n預約時間：{}  {}'.format(postback_data[1], datetime_text[0:10], datetime_text[11::]),
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
                                                    data='CheckDeleteReservation&{}'.format(Reservation.objects.filter(line_user_id=user.line_user_id).order_by('created_at').reverse().first().pk)
                                                )
                                            ]
                                        )
                                    ]
                                )
                            )
                        )
                        user.operation_status='Normal'
                        user.save()

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
                                text='確定要刪除在\n{}\n{}\n的預約嗎？'.format(target_location.location, target_location.reservation_time.astimezone('Asia/Taipei').strftime('%Y-%m-%d %H:%M')),
                                actions=[                              
                                    PostbackTemplateAction(
                                        label='是',
                                        text='是',
                                        data='DeleteReservation&{}'.format(postback_data[1])
                                    ),
                                    MessageTemplateAction(
                                        label='否',
                                        text='否'
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
