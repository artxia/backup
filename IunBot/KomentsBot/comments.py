from telegram.ext import Updater, Filters, MessageHandler, CommandHandler, CallbackQueryHandler
from data_base import db
from telegram import InlineKeyboardButton as Button
from telegram import InlineKeyboardMarkup as Markup



def open_comment(bot, comment_id):

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


def comments(bot, msg):
    code = msg.text.split()[1]
     
    if code[0] == '0': # for new comments
    
        view.write_comment(msg, post_id = code[1:])
    elif code[0] == '1': # for open comment
        
        open_comment(msg, comment_id = code[1:])

def start_command(bot, msg):
        msg = msg.message
    
        
        if len(msg.text.split()) == 2 and msg_txt[0] == '/start':
            comments(bot, msg)
            
        elif msg.text == '/start':
            bot.send_message(msg.chat.id, 'Welkom!')





def main():
    updater = Updater(config.COMNT_TOKEN)
        
    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        MessageHandler(Filters.text, private_handler.main, channel_post_updates = False)
    )
    dispatcher.add_handler(CommandHandler('start', private_handler.command))



if __name__ == "__main__":
    main()