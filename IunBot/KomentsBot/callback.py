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

        elif method == 'send':
            if action == 'send_post':
                self.send_post(bot, msg, kwargs['ch_id'])

        elif method == 'delete':
            if action == 'button':
                print(kwargs)
                self.delete_button(bot, msg, **kwargs)

        elif method == 'ch_enable':

            ch_ids = buffer.get_arg_post(msg.chat.id, 'publish_in')

            if action == 'add':
                ch_ids.append(kwargs['ch_id'])

            elif action == 'del':
                ch_ids.remove(kwargs['ch_id'])

            buffer.set_arg_post(msg.chat.id, 'publish_in', ch_ids)
            
            view.complete_post(msg)


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

    def delete_button(self, bot, msg, btn_id, ch_id):
        buttons, comments_on = db.get_buttons_channel(ch_id)
        print('DELTE BUTTON')

        count_ids = 0
        for x, line in enumerate(buttons):
            for y, btn in enumerate(line):
                
                if btn['id'] == int(btn_id):
                    print('DEEEL')
                    del buttons[x][y]
                else:
                    buttons[x][y]['id'] = count_ids
                    count_ids += 1

        for x, line in enumerate(buttons):
            if not line:                    # delete empty lines
                del buttons[x]

        
        db.set_buttons_channel(ch_id, buttons, comments_on)
        view.config_btn(msg, ch_id = ch_id)

    def button_handler(self, bot, msg, from_user,  btn_id):
        buttons = db.get_post_buttons(ch_id = msg.chat.id, msg_id = msg.message_id)
        pprint(buttons)

        post_btn = []
        for i, line in enumerate(buttons):
            post_btn.append([])
            for btn in line:
                if btn['type'] == 'url':
                    post_btn[i].append(Button(btn['text'], url = btn['url']))

                elif btn['type'] == 'reaction':

                    if int(btn_id) == btn['id']:

                        if from_user in btn['users_liked']:
                            btn['users_liked'].remove(from_user)
                            btn['count'] -= 1
                            
                        else:
                            btn['users_liked'].append(from_user)
                            btn['count'] += 1
                            

                    
                    post_btn[i].append(Button(
                        btn['text'].format(count = btn['count']), callback_data = btn['data']
                    ))

                elif btn['type'] == 'comments':
                    post_btn[i].append(Button(
                        btn['text'].format(count = btn['count']), url = btn.url
                    ))
        

        bot.editMessageReplyMarkup(
            chat_id = msg.chat.id,
            message_id = msg.message_id,
            reply_markup = Markup(post_btn)
        )
        db.set_buttons_post(msg.chat.id, msg.message_id, buttons)


    def send_post(self, bot, msg, ch_id):
        post = buffer.get_bildpost(msg.chat.id)
        
        if post.comments_on:
            path_new, path_top = tgph_editor.new_comments()
        else:
            path_top = path_new = None

        post_id = db.new_post(
            channel_id = ch_id,
            user_creator_id = msg.chat.id,
            buttons = parse_buttons(post.buttons),
            comments_on = post.comments_on,
            telegraph_path_top = path_new,
            telegraph_path_new = path_top
        )


        post_btn = []
        for btn in post.buttons:
            if btn['type'] == 'url':
                post_btn.append(Button(btn['text'],
                url = btn['url']))

            elif btn['type'] == 'reaction':
                post_btn.append(Button(btn['text'],
                callback_data = btn['data']))

            elif btn['type'] == 'comments':
                post_btn.append(Button(btn['text'],
                        url = 't.me/KomentsBot?start=0' + str(post_id)
                ))        # 0 - new comments  > > ^
                



        
        if post.type == 'text':
            msg_send = bot.send_message(ch_id, post.text, 
            reply_markup = Markup([post_btn]))
        elif post.type == 'photo':
            pass
        
            
        db.set_msg_id_post(post_id, msg_send.message_id)

        view.send_post_complete(msg)



callback = CallbackHandler()