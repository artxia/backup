from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup as Markup
from pprint import pprint

from utils import get_method_args, parse_buttons
from buffer import buffer
from tgphEditor import tgph_editor
from data_base import db
from view import view

class CallbackHandler(object):
    def __init__(self):
        self.methods = {
            'main_menu'   : view.main_menu,
            'ch_list'     : view.ch_list,
            'add_ch'      : view.add_ch,
            'del_btn'     : view.del_btn,
            'add_post'    : view.add_post,
            'ch_setting'  : view.ch_setting,
            'confirm_del' : view.confirm_del,
            'comment'     : view.comment,
            'bild_post'   : view.bild_post,
            'config_btn'  : view.config_btn,
            'add_btn_url' : view.add_btn_url,
            'edit_comment': view.edit_comment,
            'write_comment': view.write_comment,
            'complete_post': view.complete_post,
            'select_type_btn': view.select_type_btn,
            'add_btn_name'   : view.add_btn_name,
            'write_answer': view.write_answer,
        }

    def main(self, bot, update):
        msg  = update.callback_query.message
        print(update.callback_query)
        
        method, action, kwargs = get_method_args(update.callback_query.data)
     
        
        print('CALLBACK: ', method, action, kwargs)

        if method == 'open':
            self.methods[action](msg, **kwargs)

        elif method == 'reopen':
            bot.delete_message(msg.chat.id, msg.message_id)
            self.methods[action](msg, **kwargs)


        elif method == 'comment':

            if action =='delete':

                bot.delete_message(msg.chat.id, msg.message_id)
                post_id = db.delete_comment(**kwargs)
                tgph_editor.update_comments(post_id) 
                return

            elif action == 'like':
                db.like_comment(user_id = msg.chat.id, **kwargs)

            elif action == 'dislike':
                db.dislike_comment(user_id = msg.chat.id, **kwargs)

            view.comment(msg, **kwargs)
            tgph_editor.update_comments(post_id) 
            

     
        elif method == 'remove_yourself':
            bot.delete_message(msg.chat.id, msg.message_id)
        elif method == 'show':
            if action == 'you_creator':
                bot.answer_callback_query(update.callback_query.id, 'Ти не можешь лайкать свой коментарий')

  

                



        
    


callback = CallbackHandler()