from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup as Markup
from config import TGPH_TOKEN
from telegraph import Telegraph


from utils import add_entities
from data_base import db


class PostEditor(object):

    def __init__(self):
        self.tgph = Telegraph(TGPH_TOKEN)
        
        
    def new_post(self,bot, msg):
        post = msg.channel_post

        
        post_id = db.new_post(
            chennel_id = post.chat.id,
            msg_id = post.message_id,
            telegraph_path_new = page_new['path'],
            telegraph_path_top = page_top['path']
        )

        standart_bts = [[Button('Написать коментарий', url='t.me/KomentsBot?start=0' + str(post_id)),]]

        if post.photo:
            type_msg = 'photo' 
            text_msg = post.caption
        else:
            type_msg = 'text'
            text_msg = post.text
    
        

        text_post = add_entities(text_msg, post.entities)

        page_url = page_top['url']
        new_text = f'{text_post}\n<a href="">&#65524;</a>'

        self.edit_msg(bot, post.chat.id, post.message_id, new_text, standart_bts)


    def edit_msg(self, bot, chat_id, msg_id, text, bts):
        try:
            bot.edit_message_text(
                chat_id = chat_id,
                message_id = msg_id,
                text = text,
                reply_markup = Markup(bts),
                parse_mode = 'html'
            )
            
        except Exception as e:
            print('Error edit msg  in channel: ', e)
            bot.edit_message_caption(
                chat_id = chat_id,
                message_id = msg_id,
                caption = text,
                reply_markup = Markup(bts),
                parse_mode = 'html'

            )

    def new_comment(self, bot, user_id, text, user_name, post_id = None, comment_id = None):
        if comment_id:
            post_id = db.new_subcomment(user_id, text, user_name, comment_id)
        else:
            post_id = db.new_comment(user_id, text, user_name, post_id)

        self.update_post(bot, post_id)
        bot.send_message(user_id, 'You comments sended!\nThank you!')   

    


    def update_post(self, bot, post_id = None, comment_id = None):
        post = db.get_post(post_id = post_id, comment_id = comment_id)
   
        #============= EDIT PAGE IN TELEGRAPH =================
        print('POST ID ', post_id)
        comments_new = db.get_comments(post_id = post.id, sort_comnts = 'new', limit_comnts = 25) 
        comments_top = db.get_comments(post_id = post.id, sort_comnts = 'top', limit_comnts = 25) 


        base = ' <a href="http://t.me/KomentsBot?start=0' + str(post.id) + '"> Add comments</a><br/>'

        body_new = f'Sort <b>New</b> <a href="https://telegra.ph/{post.telegraph_path_top}">Top</a> ' + base
        body_top = f'Sort <a href="https://telegra.ph/{post.telegraph_path_new}">New</a> <b>Top</b> ' + base




        b_com = '<h4>{}</h4>{}<br><a href="http://t.me/KomentsBot?start=1{}"> ✉️ {}  |  ❤️ {}  |  {}</a><br/>'

        print()


        for com in comments_new:

            body_new += b_com.format(com.user_name, com.text, com.id, com.count_subcomnt, com.liked_count, com.date_add)
            print(com.count_subcomnt)
            if com.count_subcomnt > 0:
                subcomnts = db.get_subcomments(com.id)
                print(subcomnts)

                for subcomnt in subcomnts:
                    body_new += f' |    <a href="/"><u><b>{subcomnt.user_name}</b>  |  ❤️ {subcomnt.liked_count}  |  {subcomnt.date_add}</u></a><br/> |     <aside>{subcomnt.text}</aside>  <br/>'
        

        for com in comments_top:
            body_top += b_com.format(com.user_name, com.text, com.id, com.count_subcomnt, com.liked_count, com.date_add)

        print(body_new)
        title = 'Komments | ' + str(post.all_comments)
        
        print(self.tgph.edit_page(
            path = post.telegraph_path_new,
            title = title,
            html_content = body_new
        ))
        print(self.tgph.edit_page(
            path = post.telegraph_path_top,
            title = title,
            html_content = body_top
        ))
        #=======================================================


      

        msg = bot.forward_message(chat_id = '@gpalik', from_chat_id = post.channel_id, message_id = post.msg_id)

        

        text_post = msg.text.split('\ufff4')[0]
        text_post = add_entities(text_post, msg.entities)
        
        text = f'<a href="Bot">&#65524;</a><b>Коментарии  {post.all_comments}</b>'


        print(post.telegraph_path_top, post.telegraph_path_new)

        for comm in comments_new[:-3]:

            text += f'\n <b>{comm.user_name}</b>\n  <i>{comm.text}</i>\n ❤️ {comm.liked_count}  |  {comm.date_add}'

        
        standart_bts = [[Button('Открить коментарии', url="https://telegra.ph/" + post.telegraph_path_top)]]

        self.edit_msg(bot, post.channel_id, post.msg_id, text_post + text , standart_bts)
        
post_editor = PostEditor()