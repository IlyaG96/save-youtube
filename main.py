from enum import Enum, auto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from environs import Env
from pytube import Playlist
from textwrap import dedent
import os
from telegram.error import BadRequest

class BotStates(Enum):
    START = auto()
    CHOSE_RES = auto()
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
        stream = video.streams.filter(res='720p').first()  # .download()
        try:
            if stream.filesize_approx > 50000000:
                context.bot.send_message(
                    text=f"Видео {stream.title} имеет размер более 50 мегабайт, вот ссылка на скачивание: \n"
                         f"{stream.url}",
                    chat_id=update.message.chat_id,
                )

                continue

            context.bot.send_video(
                chat_id=update.message.chat_id,
                caption=f'{stream.title}',
                video=stream.url
            )
        except BadRequest:
            context.bot.send_message(
                text=f"Какая-то ошибка с видео {stream.title}. Не могу загрузить :(",
                chat_id=update.message.chat_id,
            )
            continue


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
