from enum import Enum, auto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from environs import Env
from pytube import Playlist
from textwrap import dedent
import os


class BotStates(Enum):
    START = auto()
    AWAIT_LINK = auto()


def start(update, context):
    update.message.reply_text(
        dedent(f'''
        Привет! Ссылку на плейлист нужно отправить мне.
        Ничего, кроме ссылок на плейлисты, я обрабатывать пока не умею,
        потому что меня написали вечером на скорую руку :)'
        Кстати, видео больше 50мб будут отправлены в виде ссылок на скачивание.
        Отправлять видео-файлы более 50 мб ботам пока нельзя. Это ограничение телеграма.
    '''))

    return BotStates.AWAIT_LINK


def process_playlist(update, context):
    playlist_link = update.message.text
    playlist = Playlist(playlist_link)
    if 'youtube.com' not in playlist_link:
        context.bot.send_message(
            text=f"Только ссылки на плей-листы.",
            chat_id=update.message.chat_id,
        )
        return BotStates.AWAIT_LINK

    for video in playlist.videos:
        stream = video.streams.filter(res='720p').first() # .download()
        context.bot.send_message(
            text=f"Скачиваю видео {stream.title}",
            chat_id=update.message.chat_id,
        )
        stream.download()
        if os.path.getsize(stream.default_filename) > 50000000:
            context.bot.send_message(
                text=f"Видео {stream.title} имеет размер более 50 мегабайт, вот ссылка на скачивание:"
                     f"{stream.url}",
                chat_id=update.message.chat_id,
            )

        with open(file=f'{stream.default_filename}', mode='rb') as tg_video:
            context.bot.send_video(
                chat_id=update.message.chat_id,
                caption=f'{stream.title}',
                video=tg_video
            )

        os.unlink(stream.default_filename)


def main():
    env = Env()
    env.read_env()
    telegram_token = env.str('TG_TOKEN')

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    voice_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
        ],
        states={
            BotStates.START: [
                CommandHandler('start', start)
            ],
            BotStates.AWAIT_LINK: [
                MessageHandler(Filters.text, process_playlist),
            ],
        },

        per_user=True,
        per_chat=True,
        fallbacks=[],
    )

    dispatcher.add_handler(voice_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()