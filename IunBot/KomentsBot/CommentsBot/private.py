import json
from pprint import pprint
import time


from telegram import error
from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup as Markup

from tgphEditor import tgph_editor
from type_s import Post
from buffer import buffer

from data_base import db
from view import view


class PrivateHandler(object):
    def __init__(self):
        self.map = {
            'write_comment'  : self.write_comment,
            'write_answer'   : self.write_answer
        }

    def write_answer(self, msg, comment_id):
        count_answers, post_id = db.new_answer(
            user_id = msg.chat.id,
            text = msg.text,
            user_name = msg.chat.first_name,
            root_comnt_id = comment_id
        )

        tgph_editor.update_comments(post_id)
        
        if count_answers > 1:
            tgph_editor.update_answers(comment_id)

    def write_comment(self, msg, post_id):
        post = db.get_post(post_id)

        db.new_comment(
            text = msg.text,
            channel_id = post.channel_id,
            user_id = msg.chat.id,
            user_name = msg.chat.first_name,
            post_id = post_id
        )
        
        tgph_editor.update_comments(post_id)

        bts = parse_buttons(post.buttons)
    
        print('>>>> ', bts)
        print('COUNT: ', post.all_comments)
        
        post_bts = []
    
        for inx, line in enumerate(json.loads(post.buttons)):
            post_bts.append([])
            
            for btn in line:
                if btn['type'] == 'url':  
                    post_bts[inx].append(Button(btn['text'], url = btn['url']))

                elif btn['type'] == 'reaction':
                    btn_id = btn['id']
                    post_bts[inx].append(Button(
                        btn['text'].format(count = btn['count']),
                        callback_data = btn['data']
                    ))

                elif btn['type'] == 'comments':
                    print('BUTTON >>> ', btn['text'])
                    post_bts[inx].append(Button(
                        btn['text'].format(count = post.all_comments + 1),
                        url = 'telegra.ph/' + post.telegraph_path_top
                    ))

        self.bot.edit_message_reply_markup(
            chat_id = int(post.channel_id),
            message_id = int(post.msg_id),
            reply_markup = Markup(post_bts)
        )
        view.comments_sended(msg)
    


    def main(self, bot, msg):
        self.bot = bot
        msg = msg.message
        user_id = msg.chat.id

        user = db.check_user(user_id = user_id)
        method, action, args = get_method_args(user.mode_write)
        print('PRIVATE: ', method, action, args)
        

        if method == 'open':
            self.map[action](msg = msg, **args)
        else:
            view.main_menu(msg, edit_msg=False)


    def command(self, bot, msg):
        msg = msg.message
        print(msg.text)
        msg_txt = msg.text.split()
        if len(msg_txt) == 2 and msg_txt[0] == '/start':
            code = msg_txt[1]
            print(msg_txt, code)
            if code[0] == '0': # for new comments
                print(111111111111)
                view.write_comment(msg, post_id = code[1:])
            elif code[0] == '1': # for open comment
                print(222222222222)
                view.comment(msg, comment_id = code[1:])
            
        elif msg.text == '/start':
           

            if db.get_all_ch(msg.chat.id):
                view.main_menu(msg, edit_msg=False)
            else:
                view.welkom(msg, edit_msg=False)



private_handler = PrivateHandler()