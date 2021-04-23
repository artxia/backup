import time
import json

from data_base import db
from telegram import Bot
from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup as Markup


from buffer import buffer
import config


bot = Bot(config.TOKEN)


class View(object):

    def send_msg(func):
        def wraper(self, msg, edit_msg = True, *args, **kwargs):
            print(func.__name__, 'KWARGS docor: ',kwargs)

            db.check_user(user_id = msg.chat.id) # TODO 
            self.user_id = msg.chat.id
            self.msg = msg

            text, buttons = func(self, *args, **kwargs)
            
            print('BUTTONS: ', buttons)
            if text is False:
                return
            if buttons is None:
                bts = None
            else:
                bts = Markup(buttons)
            
            if edit_msg:
                try:
                    bot.edit_message_text(text, chat_id = msg.chat.id, message_id = msg.message_id,
                                               parse_mode = 'html', reply_markup = bts)
                except Exception as e:
                    print('Error send message: ', e)
                    bot.send_message(msg.chat.id, text, parse_mode = 'html', reply_markup = bts)
            else:
                bot.send_message(msg.chat.id, text, parse_mode = 'html', reply_markup = bts)
        return wraper

    @send_msg
    def ch_setting(self, ch_id):
        bts = [
            [
                Button('Назад', callback_data='open ch_list'),
            ],
            [
                Button('Водяной знак', callback_data='f f ff '),
            ],
            [
                Button('Set buttons',callback_data = f'open config_btn ?ch_id={ch_id}')
            ]
            
        ]
        return 'Setting', bts

    @send_msg
    def comments_sended(self):
        return 'Коментарий отправлен', None

    @send_msg
    def write_comment(self, post_id):
        db.set_user_param(self.user_id,
            'mode_write', 'open write_comment ?post_id='+ str(post_id))
        bts = [[Button('Отмена', callback_data = 'remove_yourself')]]
        bot.send_message(
            self.user_id,
            'Отправь мне текст комментария:',
            reply_markup = Markup(bts)
             )

        return False, None

    @send_msg
    def write_answer(self, comment_id):
        db.set_user_param(self.user_id, 'mode_write', 'open write_answer ?comment_id='+ str(comment_id))
        bts = [[Button('Отмена', callback_data = 'remove_yourself')]]
        bot.send_message(
            self.user_id,
            'Отправь мне текст ответа на етот коментарий:',
            reply_markup = Markup(bts)
        )
        return False, None

    @send_msg
    def comment(self, comment_id):
        comnt = db.get_comment(comment_id)
        

        bts = []
        if self.user_id == comnt.user_creator_id: # btn for creator
            bts.append( Button(f'❤️ {comnt.liked_count}',   callback_data='THIS YOUR like'))
            bts.append( Button('edit', callback_data='open edit_comment ?comment_id=' + str(comnt.id)))
            bts.append( Button('🗑',    callback_data='open confirm_del ?comment_id=' + str(comnt.id)))
            bts.append( Button('Answer',callback_data='open write_answer ?comment_id=' + str(comnt.id)))
            
            
            return f'<b>{comnt.user_name}</b>     {comnt.date_add}\n<i>{comnt.text_main}</i>', [bts]


        # if not none
        if comnt.users_liked and self.user_id in comnt.users_liked:
            is_liked  = '💖'
            call_data = 'comment dislike ?comment_id=' + str(comnt.id)
        else:
            is_liked  = '❤️'
            call_data = 'comment like ?comment_id=' + str(comnt.id)

        if comnt.channel_id in db.get_all_ch(self.user_id): # btn for admin channel
            bts.append(Button(is_liked, callback_data = call_data))
            bts.append(Button('Answer',callback_data='open write_answer ?comment_id=' + str(comnt.id)))
            bts.append(Button('🗑', callback_data='open confirm_del ?comment_id=' + str(comnt.id)))
            
        else: # for normal user
            
            bts.append(Button(is_liked, callback_data = call_data))
            bts.append(Button('Answer',callback_data='open write_answer ?comment_id=' + str(comnt.id)))
            


        text = f'<b>{comnt.user_name}</b>     {comnt.date_add}\n<i>{comnt.text_main}</i>'
        return text, [bts]


    @send_msg
    def confirm_del(self, comment_id):
        data_yes = f'comment delete ?comment_id={comment_id}'

        bts = [[
            Button('Yes', callback_data = data_yes),
            Button('No',  callback_data = "open comment ?comment_id=" + comment_id)
            ]]
        return 'Delete this comment?', bts


    @send_msg
    def edit_comment(self, comment_id):
        comment = db.get_comment(comment_id)
        btn = [[Button('Cancel', callback_data = "remove_yourself")]]
        bot.send_message(self.user_id, 'ok send me new text for', reply_markup = btn)
        return False, None


    @send_msg
    def welkom(self):
        return 'Привет, этот бот поможет тебе с управлением твоих каналов.\nДля начала добавь канал', [[Button("Добавить канал", callback_data='open add_ch'),]]
        
    @send_msg
    def main_menu(self):
        bts = [
            [Button('Создать пост', callback_data='open add_post'),],
            [Button("Список каналов", callback_data='open ch_list'),]
        ]
        return 'Main menu', bts

    @send_msg
    def add_post(self):
        db.set_user_param(self.user_id, 'mode_write', 'open add_post ')
        btn = [[Button('Отмена', callback_data='open main_menu')]]
        return 'ОТправь мне текст или изображение', btn

    @send_msg
    def bild_post(self, type_post = None):
        db.set_user_param(self.user_id, 'mode_write', 'open add_addition')

        bild_post = buffer.get_bildpost(self.user_id)

        if type_post is None:
            type_post = bild_post.type
        if type_post == 'text':
            set_type = 'photo'
        elif type_post == 'photo':
            set_type = 'text'
        
        post_btn = []
        for btn in bild_post.buttons:
            if btn['type'] == 'url':
                post_btn.append(Button(btn['text'], url = btn['url']))
            elif btn['type'] == 'reaction':
                post_btn.append(Button(btn['text'], callback_data = btn['data']))
            elif btn['type'] == 'comments':
                post_btn.append(Button(btn['text'], url = 'google.com'))

        print('===========================================')
        print(post_btn)
        



        if type_post == 'text':
            bot.send_message(
                self.user_id,
                bild_post.photo_url + bild_post.text,
                reply_markup = Markup([post_btn]),
                parse_mode = 'html'
            )
        elif type_post == 'photo':
            bot.send_photo(
                self.user_id,
                photo = bild_post.photo.file_id,
                caption = bild_post.text,
                reply_markup = Markup([post_btn]),
                parse_mode = 'html'
            )
        
        bts = [
            [Button('Готово', callback_data='open complete_post')],
            [Button('Добавить кнопку', callback_data = 'open select_type_btn')]
            ]
        if bild_post.text and bild_post.photo:
            bts.append([Button('revers', callback_data = 'reopen bild_post ?type_post=' + set_type)])
            
        bot.send_message(self.user_id, '=================', reply_markup = Markup(bts))
        

        return False, None

    @send_msg
    def add_btn_name(self, type_btn, ch_id = ''):
        if ch_id:
            ch_id = '&ch_id='+ch_id

        if type_btn == 'url':
            text = 'Пришли мне натпись на кнопке'
            url = f'&url={self.msg.text}'
        elif type_btn == 'reaction':
            text = 'Пришли мне натпись на кнопке с {count} где будет количество'
            url = ''
        elif type_btn == 'comments':
            text = 'Пришли мне натпись на кнопке с {count} где будет количество комментариев'
            url = ''
            
        db.set_user_param(self.user_id,
         'mode_write', f'open create_button ?type_btn={type_btn}' + url + ch_id)
        bts = [[Button('Отмена', callback_data='remove_yourself None')]]
        

        return text, bts

    @send_msg
    def select_type_btn(self, ch_id = ''):
        if ch_id:
            ch_id_ = '&ch_id='+ch_id
            ch_id_url = '?ch_id='+ch_id
        
        bts = [
            [Button('Отмена', callback_data='remove_yourself None')],
            [
                Button('Url', callback_data = f'open add_btn_url ' + ch_id_url),
                Button('Reaction', callback_data = 'open add_btn_name ?type_btn=reaction' + ch_id_)
            ],
            [
                Button('Komments', callback_data = 'open add_btn_name ?type_btn=comments' + ch_id_)
             ]]
        bot.send_message(self.user_id, 'Виберите тип кнопки', reply_markup =  Markup(bts))
        return False, None

    @send_msg
    def add_btn_url(self, ch_id = ''):
        if ch_id:
            ch_id = '&ch_id='+ch_id
        db.set_user_param(self.user_id, 'mode_write', f'open add_btn_name ?type_btn=url'+ch_id)
        bts = [[Button('Отмена', callback_data='remove_yourself None')]]
        return 'Пришли мне ссилку', bts


    @send_msg
    def config_btn(self, ch_id):
        buttons, comments_on = db.get_buttons_channel(ch_id = ch_id)
        db.set_user_param(self.user_id, 'mode_write', f'open sort_buttons ?ch_id={ch_id}')

        bts = buttons.get_tg_bts(markup = False, config = True, ch_id = ch_id)
        
        bts.append(
            [Button('Назад', callback_data = f'open ch_setting ?ch_id={ch_id}'),
             Button('Добавить', callback_data=f'open select_type_btn ?ch_id={ch_id}')
        ])
        print(bts)
        return 'Config buttons', bts


    @send_msg
    def del_btn(self, btn_id, ch_id):
        print(btn_id, ch_id)
        bts = [
            [
                Button('del', callback_data = f'delete button ?btn_id={btn_id}&ch_id={ch_id}'),




                Button('cancel', callback_data='remove_yourself')
            ]
        ]
        return 'Delete button?', bts


    @send_msg
    def complete_post(self):
        ch_ids = db.get_all_ch(self.user_id)
        bts = []
        
        for ch in ch_ids:
            try:
                ch_name = bot.get_chat(ch).title
            except:
                ch_name = ' | No admin'
            
            bts.append([Button(ch_name,
                callback_data = f'send send_post ?ch_id={ch}')]
            )

        text = 'Виберите канали в которих нужно виложить пост'
    
        bts.append([Button('Отмена', callback_data='remove_yourself')])

        return text, bts

    @send_msg
    def send_post_complete(self):
        return 'Пост отправлен!', [[Button('В меню', callback_data = 'open main_menu')]]

    @send_msg
    def ch_list(self):
        db.set_user_param(self.user_id, 'mode_write', 'off')
        
        channels = db.get_all_ch(self.user_id)
        bts = [[Button(' Назад', callback_data='open main_menu')]]

        if channels:
            bts[0].append(Button(' Добавить', callback_data='open add_ch'))
            for ch in channels:
                try:
                    ch_name = bot.get_chat(ch).title
                except:
                    ch_name = ' | No admin'
                bts.append([Button(ch_name, callback_data='open ch_setting ?ch_id=' + str(ch)),])
        else:
            bts.append([Button(' Добавить', callback_data='open add_ch')])
        return 'List channel: ', bts

    @send_msg
    def add_ch(self):
        db.set_user_param(self.user_id, 'mode_write', 'open add_channel')
        return 'Видай мне права администратора и пришли силку или username канала', [[Button('Назад', callback_data='open ch_list')]]

    @send_msg
    def add_ch_final(self, result, ch_id):
        if result == 'NotFound':
            text = 'Такого канала не существует :/\nПовтори еще раз'
        elif result == 'NoAdmin':
            text = 'Я не администратор канала :/\nВидай мне права и повтори еще раз'
        elif result == 'ChannelExists':
            text = 'Этот канал уже добавлен'
        elif result == 'Added':
            db.set_user_param(self.user_id, 'mode_write', 'off')
            bot.send_message(self.user_id, 'Добавляю канал...')
            time.sleep(2)
            self.config_btn(self.msg, ch_id)
        
        return text, [[Button('Назад', callback_data='open ch_list')]]

    
    


        # def build_comment(self, comnt, is_admin):
    #     if comnt.user_creator == self.user_id:
    #         is_liked  = '♥️'
    #         call_data = 'show you_creator'
    #     elif comnt.users_liked and self.user_id in comnt.users_liked:
    #         is_liked  = '💖'
    #         call_data = 'comment dislike ?comment_id=' + str(comnt.id)
    #     else:
    #         is_liked  = '❤️'
    #         call_data = 'comment like ?comment_id=' + str(comnt.id)
    #     print('CALLDATA BTN: ', call_data)
    #     bts = [Button(is_liked + str(comnt.liked_count), callback_data=call_data)]
        
    #     if comnt.user_creator == self.user_id:
    #         bts.append(Button('🗑', 
    #          callback_data='open confirm_del ?comment_id=' + str(comnt.id) + '&post_id=' + str(comnt.post_id)))
    #         bts.append(Button('edit',callback_data='open edit_comment ?comment_id=' + str(comnt.id)))
    #     elif is_admin:
    #         bts.append(Button('🗑', callback_data='open confirm_del ?comment_id=' + str(comnt.id)))

    #     text = f'<b>{comnt.user_name}</b>     {comnt.date_add}\n<i>{comnt.text}</i>'
    #     return text, [bts]


    # @send_msg
    # def comments(self, post_id, sort = 'top', offset = 0):
        
        
    #     post = db.get_post(post_id, sort_comnts = sort, limit_comnts = config.COMMENTS_OF_PARTY + 1, offset = offset)
    #     offset = str(int(offset) + config.COMMENTS_OF_PARTY)
    #     is_admin = post.channel_id in db.get_all_ch(self.user_id) 
    #     bts = []

    #     if post.comments:
    #         for comment in post.comments[:-1]:
    #             text_comment, bts_comment = self.build_comment(comment, is_admin)
    #             bot.send_message(self.user_id, text_comment, reply_markup = Markup(bts_comment), parse_mode = 'html')

    #         if len(post.comments) > config.COMMENTS_OF_PARTY:
    #             data_new = 'reopen comments ?post_id=' + post_id + '&sort=new&offset=' + offset
    #             data_top = 'reopen comments ?post_id=' + post_id + '&sort=top&offset=' + offset
    #             bts.append([
    #                 Button('Еще лучих',     callback_data = data_top ),
    #                 Button('Еще последних', callback_data = data_new ),
    #             ])
    #             tx = 'лучшие' if sort == 'top' else 'последние'
    #             text = f'Вот {tx} коментарии'
    #         else:
    #             text = 'Это все коментарии'

    #     else:
    #         text = 'Нету комментариев'
        
            
        # bts.append([Button('Написать комментарий', callback_data='open write_comment ?post_id=' + str(post_id)), ])

        # bot.send_message(self.user_id, text, reply_markup =  Markup(bts))
        # return False, None








view = View()



        










