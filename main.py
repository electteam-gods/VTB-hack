import asyncio
import os
import whisper

from concurrent.futures import ProcessPoolExecutor
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

REPLY_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=['Рассмотреть доступные вакансии'],
    resize_keyboard=True,
    one_time_keyboard=False
)

USER_STATE = {}
USER_QUESTION = {}
USER_JOB = {}

executor = ProcessPoolExecutor()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Этот бот был создан компанией \"Сыны Миража\".\n\n"
        "Он может:\n"
        "🔹 Выделить всё самое важное из ваших документов\n"
        "🔹 Ответить на любой вопрос по теме занятий\n"
        "🔹 Провести проверку знаний.",
        reply_markup=REPLY_KEYBOARD
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    cur_data = query.data
    user_id = query.from_user.id

    if USER_STATE[user_id] == 'job_selection':
        await query.edit_message_text(text='На какую вакансию ты хочешь пройти собеседование?', reply_markup=None)
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text='Теперь пришли мне pdf файл своего резюме, чтобы я смог оценить его на соответствие вакансии.',
            reply_markup=ReplyKeyboardMarkup([['Назад к выбору вакансий']], resize_keyboard=True,
                                             one_time_keyboard=True)
        )
        USER_STATE[user_id] = 'awaiting_resume'


def generate_question(context, user_question, user_job):
    return 'Ты кто?'


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == 'Рассмотреть доступные вакансии' or text == 'Назад к выбору вакансий':
        USER_STATE[user_id] = 'job_selection'

        job_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('Вакансия1', callback_data='job_1')],
            [InlineKeyboardButton('Вакансия2', callback_data='job_2')],
            [InlineKeyboardButton('Вакансия3', callback_data='job_3')]
        ])
        await update.message.reply_text('На какую вакансию ты хочешь пройти собеседование?',
                                        reply_markup=job_keyboard)
    elif text == 'Начать собеседование' and USER_STATE.get(user_id) == 'awaiting_interview_starting':
        USER_STATE[user_id] = 'interview_in_process'

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, generate_question, '', USER_QUESTION.get(user_id),
                                            USER_JOB.get(user_id))
        await update.message.reply_text(result)
    else:
        if USER_STATE.get(user_id) == 'interview_in_process':
            await update.message.reply_text('На вопросы собеседования ты должен отвечать только аудиосообщениями.')
        else:
            await start(update, context)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    user_id = update.message.from_user.id
    if USER_STATE.get(user_id) == 'interview_in_process':
        file = await voice.get_file()
        file_path = f'downloads/{voice.file_unique_id}.ogg'
        await file.download_to_drive(file_path)
        


def is_correct_resume(file_path):
    return True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    document = update.message.document
    user_state = USER_STATE.get(user_id)

    if user_state == 'awaiting_resume':
        if document.mime_type == 'application/pdf':
            file = await context.bot.get_file(document.file_id)
            file_path = f"./downloads/{document.file_name}"
            await file.download_to_drive(file_path)
            # далее должен идти парсинг pdf, затем определяется, допускается ли пользователь до собеседования

            await update.message.reply_text("⏳ Проверяю резюме...")

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, is_correct_resume, file_path)

            if result:
                USER_STATE[user_id] = 'awaiting_interview_starting'

                await update.message.reply_text('Вы допущены до собеседования. '
                                                'Оно будет включать в себя '
                                                'некоторое количество вопросов по технической теме, '
                                                'а также некоторое количество вопросов по софт скиллам. '
                                                'Ответы на вопросы осуществляются посредством голосовых сообщений. '
                                                'По итогам собеседования будет сформирован отчёт.',
                                                reply_markup=ReplyKeyboardMarkup([['Назад к выбору вакансий'],
                                                                                  ['Начать собеседование']],
                                                                                 resize_keyboard=True,
                                                                                 one_time_keyboard=True
                                                                                 )
                                                )
            else:
                await update.message.reply_text('К сожалению, вы не допущены до собеседования, '
                                                'так как ваше резюме не соответствует требованиям вакансии.',
                                                reply_markup=ReplyKeyboardMarkup([['Назад к выбору вакансий']],
                                                                                 resize_keyboard=True,
                                                                                 one_time_keyboard=True
                                                                                 )
                                                )
        else:
            await update.message.reply_text('Файл резюме должен быть формата .PDF')
    else:
        await start(update, context)

if __name__ == '__main__':
    if not os.path.exists('./downloads'):
        os.mkdir('./downloads')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(button_handler))

    print('Бот запущен...')
    app.run_polling()
