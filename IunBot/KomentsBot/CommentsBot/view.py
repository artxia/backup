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
          
            [Button("Пусто", callback_data='open ch_list'),]
        ]
        return 'Main menu', bts

   


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



        










