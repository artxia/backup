import logging


import telegram
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler, CallbackQueryHandler


import config
from private import private_handler
from callback import callback



logging.basicConfig(level=logging.DEBUG,
                    format='с - %(message)s ')

updater = Updater(config.TOKEN)

dispatcher = updater.dispatcher



dispatcher.add_handler(
    MessageHandler(Filters.text, private_handler.main, channel_post_updates = False)
)
dispatcher.add_handler(CommandHandler('start', private_handler.command))
dispatcher.add_handler(CallbackQueryHandler(callback.main))


updater.start_polling()
updater.idle()



