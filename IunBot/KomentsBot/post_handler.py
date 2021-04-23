import json
from pprint import pprint
import telegram
from telegram.ext import Filters, MessageHandler, CallbackQueryHandler

from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup as Markup

from tgphEditor import tgph_editor
from data_base import db
from type_s import BTN, BTS

class PostHandler(object):

    def set_handler(self, dispatcher):

        dispatcher.add_handler(
            MessageHandler(
                Filters.text | Filters.photo | Filters.audio, self.new_post, message_updates = False
            )
        )

        dispatcher.add_handler(
            CallbackQueryHandler(self.new_reaction, pattern = r'^upcount')
        )


    def new_reaction(self, bot, update):
        from_user = update.callback_query.from_user.id
        msg = update.callback_query.message
        
        print('+ ' , msg)

        bts = db.get_post_buttons(
            ch_id = msg.chat.id, msg_id = msg.message_id
        )

        pprint(bts)

        
        print(update.callback_query.data.split()[-1])
        
        bts.upcount(int(update.callback_query.data.split()[-1]), from_user)
        pprint(bts)
        

        bot.editMessageReplyMarkup(
            chat_id = msg.chat.id,
            message_id = msg.message_id,
            reply_markup = bts.get_tg_bts()
        )
        db.set_buttons_post(msg.chat.id, msg.message_id, bts)


    def new_post(self, bot, msg): # new post
        msg = msg.channel_post

        channel = db.get_ch_setting(msg.chat.id)

        # if channel.status == 'off':
        #     print('Channel status OFF')
        #     return

        print(channel.comments_on)

        if channel.comments_on:
            page_top, page_new = tgph_editor.new_comments()
        else:
            page_top = page_new = None

        print('PAGE TOP: ', page_top)

        post_id = db.new_post(
            channel_id = msg.chat.id,
            comments_on = channel.comments_on,
            buttons = channel.default_btn_markup,
            telegraph_path_new = page_new,
            telegraph_path_top = page_top
        )
        db.set_msg_id_post(post_id, msg.message_id)

        
      
       
        bts = BTS(channel.default_btn_markup)
        
       
        
        bot.edit_message_text(msg.text,
            chat_id = msg.chat.id, message_id = msg.message_id,
            parse_mode = 'html', reply_markup = bts.get_tg_bts())

            
      
        




post_handler = PostHandler()