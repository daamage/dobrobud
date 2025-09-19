import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from datetime import datetime
import asyncio

# Простое логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8390533970:AAH7dcxqGqryY7F7UxQYlit_2z1fdcc0mAk"
CHAT_ID = -4887312460
PORT = int(os.getenv('PORT', 8000))

# Хранилище заявок
user_data = {}

class DobrobudBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CallbackQueryHandler(self.button_click))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data[user_id] = {'stage': 'start', 'data': {}}
        
        text = (
            "🏗️ **ДОБРОБУД** - Ваш надійний партнер!\n\n"
            "Оберіть послугу:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🧱 Матеріали", callback_data="materials")],
            [InlineKeyboardButton("👷‍♂️ Робітники", callback_data="workers")],
            [InlineKeyboardButton("🔧 Інструменти", callback_data="tools")],
            [InlineKeyboardButton("🏠 Будівельні роботи", callback_data="construction")]
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "📋 **Команди:**\n"
            "/start - Почати заявку\n"
            "/help - Допомога\n\n"
            "🏗️ Компанія ДОБРОБУД\n"
            "📞 +38 (067) 123-45-67"
        )
        await update.message.reply_text(text, parse_mode='Markdown')

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if user_id not in user_data:
            await query.edit_message_text("Натисніть /start")
            return

        try:
            if data in ['materials', 'workers', 'tools', 'construction']:
                await self.handle_service_choice(query, user_id, data)
            elif data.startswith('sub_'):
                await self.handle_sub_choice(query, user_id, data)
            elif data.startswith('count_'):
                await self.handle_count_choice(query, user_id, data)
            elif data.startswith('time_'):
                await self.handle_time_choice(query, user_id, data)
            elif data == 'confirm':
                await self.confirm_order(query, user_id, context)
        except Exception as e:
            logger.error(f"Button error: {e}")
            await query.edit_message_text("❌ Помилка. Спробуйте /start")

    async def handle_service_choice(self, query, user_id, service):
        user_data[user_id]['data']['service'] = service
        user_data[user_id]['stage'] = 'sub_service'
        
        services = {
            'materials': {
                'title': '🧱 Матеріали',
                'options': [
                    ('sub_cement', 'Цемент, розчини'),
                    ('sub_brick', 'Цегла, блоки'),
                    ('sub_sand', 'Пісок, щебінь'),
                    ('sub_metal', 'Арматура, метал'),
                    ('sub_wood', 'Дерево'),
                    ('sub_other_mat', 'Інше')
                ]
            },
            'workers': {
                'title': '👷‍♂️ Робітники',
                'options': [
                    ('sub_mason', 'Муляри'),
                    ('sub_builder', 'Будівельники'),
                    ('sub_electric', 'Електрики'),
                    ('sub_plumber', 'Сантехніки'),
                    ('sub_painter', 'Маляри'),
                    ('sub_other_work', 'Інші спеціалісти')
                ]
            },
            'tools': {
                'title': '🔧 Інструменти',
                'options': [
                    ('sub_power', 'Електроінструмент'),
                    ('sub_hand', 'Ручний інструмент'),
                    ('sub_machine', 'Техніка'),
                    ('sub_scaffold', 'Риштування'),
                    ('sub_other_tool', 'Інше обладнання')
                ]
            },
            'construction': {
                'title': '🏠 Будівельні роботи',
                'options': [
                    ('sub_foundation', 'Фундамент'),
                    ('sub_walls', 'Стіни'),
                    ('sub_roof', 'Покрівля'),
                    ('sub_finish', 'Оздоблення'),
                    ('sub_electric_work', 'Електромонтаж'),
                    ('sub_other_constr', 'Інші роботи')
                ]
            }
        }
        
        service_info = services[service]
        text = f"Обрано: {service_info['title']}\n\nОберіть деталі:"
        
        keyboard = [[InlineKeyboardButton(name, callback_data=code)] for code, name in service_info['options']]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_sub_choice(self, query, user_id, sub_service):
        user_data[user_id]['data']['sub_service'] = sub_service
        
        # Если выбрали рабочих, спрашиваем количество
        if user_data[user_id]['data']['service'] == 'workers':
            user_data[user_id]['stage'] = 'count'
            text = "Скільки спеціалістів потрібно?"
            keyboard = [
                [InlineKeyboardButton("1 спеціаліст", callback_data="count_1")],
                [InlineKeyboardButton("2-3 спеціалісти", callback_data="count_2-3")],
                [InlineKeyboardButton("4-6 спеціалістів", callback_data="count_4-6")],
                [InlineKeyboardButton("Більше 6", callback_data="count_6+")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await self.ask_contact_info(query, user_id)

    async def handle_count_choice(self, query, user_id, count):
        user_data[user_id]['data']['count'] = count.replace('count_', '')
        await self.ask_contact_info(query, user_id)

    async def ask_contact_info(self, query, user_id):
        user_data[user_id]['stage'] = 'name'
        await query.edit_message_text("👤 Напишіть ваше ім'я:")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        if user_id not in user_data:
            await update.message.reply_text("Натисніть /start")
            return

        stage = user_data[user_id]['stage']
        
        try:
            if stage == 'name':
                user_data[user_id]['data']['name'] = text
                user_data[user_id]['stage'] = 'phone'
                await update.message.reply_text("📞 Ваш телефон:")
                
            elif stage == 'phone':
                user_data[user_id]['data']['phone'] = text
                user_data[user_id]['stage'] = 'address'
                await update.message.reply_text("📍 Адреса об'єкта:")
                
            elif stage == 'address':
                user_data[user_id]['data']['address'] = text
                user_data[user_id]['stage'] = 'time'
                
                text = "⏰ Коли потрібно?"
                keyboard = [
                    [InlineKeyboardButton("🔥 Сьогодні", callback_data="time_today")],
                    [InlineKeyboardButton("⚡ Завтра", callback_data="time_tomorrow")],
                    [InlineKeyboardButton("📅 Цей тиждень", callback_data="time_week")],
                    [InlineKeyboardButton("📆 Наступний тиждень", callback_data="time_next")]
                ]
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                
        except Exception as e:
            logger.error(f"Text handling error: {e}")
            await update.message.reply_text("❌ Помилка. Спробуйте /start")

    async def handle_time_choice(self, query, user_id, time_choice):
        user_data[user_id]['data']['time'] = time_choice.replace('time_', '')
        await self.show_confirmation(query, user_id)

    async def show_confirmation(self, query, user_id):
        data = user_data[user_id]['data']
        
        # Названия услуг
        service_names = {
            'materials': 'Матеріали', 'workers': 'Робітники', 
            'tools': 'Інструменти', 'construction': 'Будівельні роботи'
        }
        
        time_names = {
            'today': 'Сьогодні', 'tomorrow': 'Завтра',
            'week': 'Цей тиждень', 'next': 'Наступний тиждень'
        }
        
        text = (
            "📋 **ПІДТВЕРДЖЕННЯ ЗАЯВКИ**\n\n"
            f"🔧 Послуга: {service_names.get(data['service'], data['service'])}\n"
            f"👤 Ім'я: {data['name']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"📍 Адреса: {data['address']}\n"
            f"⏰ Термін: {time_names.get(data['time'], data['time'])}\n"
        )
        
        if 'count' in data:
            text += f"👥 Кількість: {data['count']}\n"
        
        text += "\n✅ Підтвердити заявку?"
        
        keyboard = [[InlineKeyboardButton("✅ Підтвердити", callback_data="confirm")]]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def confirm_order(self, query, user_id, context):
        data = user_data[user_id]['data']
        
        # Отправляем в чат менеджеров
        service_names = {
            'materials': 'Матеріали', 'workers': 'Робітники',
            'tools': 'Інструменти', 'construction': 'Будівельні роботи'
        }
        
        message = (
            "🏗️ **НОВА ЗАЯВКА ДОБРОБУД**\n\n"
            f"🔧 **Послуга:** {service_names.get(data['service'], data['service'])}\n"
            f"👤 **Клієнт:** {data['name']}\n"
            f"📞 **Телефон:** {data['phone']}\n"
            f"📍 **Адреса:** {data['address']}\n"
            f"⏰ **Термін:** {data['time']}\n"
        )
        
        if 'count' in data:
            message += f"👥 **Кількість:** {data['count']}\n"
            
        message += f"\n📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n🏗️ **ДОБРОБУД**"
        
        try:
            await context.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            
            success_text = (
                "🎉 **ДЯКУЄМО!**\n\n"
                "✅ Заявку прийнято!\n"
                "📞 Менеджер зв'яжеться протягом 15 хвилин\n\n"
                "🏗️ **ДОБРОБУД**\n"
                "☎️ +38 (067) 123-45-67"
            )
            
            await query.edit_message_text(success_text, parse_mode='Markdown')
            
            # Очищаем данные
            del user_data[user_id]
            
        except Exception as e:
            logger.error(f"Send order error: {e}")
            await query.edit_message_text("❌ Помилка відправки. Зв'яжіться за телефоном: +38 (067) 123-45-67")

    async def run(self):
        """Простой запуск на Render"""
        logger.info("🚀 Запуск Dobrobud Bot...")
        
        try:
            # Запуск webhook
            await self.app.initialize()
            await self.app.start()
            
            # Webhook URL
            webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')}.onrender.com/webhook"
            
            # Устанавливаем webhook
            await self.app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"]
            )
            
            logger.info(f"✅ Webhook set: {webhook_url}")
            
            # Запуск Render webhook
            from telegram.ext import Updater
            updater = Updater(bot=self.app.bot, update_queue=self.app.update_queue)
            
            # Простой webhook сервер
            import json
            from http.server import HTTPServer, BaseHTTPRequestHandler
            
            class WebhookHandler(BaseHTTPRequestHandler):
                def do_POST(self_handler):
                    if self_handler.path == '/webhook':
                        content_length = int(self_handler.headers['Content-Length'])
                        post_data = self_handler.rfile.read(content_length)
                        
                        try:
                            update_data = json.loads(post_data.decode('utf-8'))
                            update = Update.de_json(update_data, self.app.bot)
                            
                            # Обрабатываем асинхронно
                            asyncio.create_task(self.app.process_update(update))
                            
                            self_handler.send_response(200)
                            self_handler.end_headers()
                            self_handler.wfile.write(b'OK')
                        except Exception as e:
                            logger.error(f"Webhook error: {e}")
                            self_handler.send_response(500)
                            self_handler.end_headers()
                    else:
                        self_handler.send_response(404)
                        self_handler.end_headers()
                
                def do_GET(self_handler):
                    self_handler.send_response(200)
                    self_handler.send_header('Content-type', 'text/plain')
                    self_handler.end_headers()
                    self_handler.wfile.write(b'Dobrobud Bot OK')
            
            # Запуск сервера
            server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
            logger.info(f"🌐 Server running on port {PORT}")
            server.serve_forever()
            
        except Exception as e:
            logger.error(f"❌ Start error: {e}")
            raise

def main():
    bot = DobrobudBot()
    asyncio.run(bot.run())

if __name__ == '__main__':
    main()import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from datetime import datetime
import asyncio

# Простое логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8390533970:AAH7dcxqGqryY7F7UxQYlit_2z1fdcc0mAk"
CHAT_ID = -4887312460
PORT = int(os.getenv('PORT', 8000))

# Хранилище заявок
user_data = {}

class DobrobudBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CallbackQueryHandler(self.button_click))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data[user_id] = {'stage': 'start', 'data': {}}
        
        text = (
            "🏗️ **ДОБРОБУД** - Ваш надійний партнер!\n\n"
            "Оберіть послугу:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🧱 Матеріали", callback_data="materials")],
            [InlineKeyboardButton("👷‍♂️ Робітники", callback_data="workers")],
            [InlineKeyboardButton("🔧 Інструменти", callback_data="tools")],
            [InlineKeyboardButton("🏠 Будівельні роботи", callback_data="construction")]
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "📋 **Команди:**\n"
            "/start - Почати заявку\n"
            "/help - Допомога\n\n"
            "🏗️ Компанія ДОБРОБУД\n"
            "📞 +38 (067) 123-45-67"
        )
        await update.message.reply_text(text, parse_mode='Markdown')

    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if user_id not in user_data:
            await query.edit_message_text("Натисніть /start")
            return

        try:
            if data in ['materials', 'workers', 'tools', 'construction']:
                await self.handle_service_choice(query, user_id, data)
            elif data.startswith('sub_'):
                await self.handle_sub_choice(query, user_id, data)
            elif data.startswith('count_'):
                await self.handle_count_choice(query, user_id, data)
            elif data.startswith('time_'):
                await self.handle_time_choice(query, user_id, data)
            elif data == 'confirm':
                await self.confirm_order(query, user_id, context)
        except Exception as e:
            logger.error(f"Button error: {e}")
            await query.edit_message_text("❌ Помилка. Спробуйте /start")

    async def handle_service_choice(self, query, user_id, service):
        user_data[user_id]['data']['service'] = service
        user_data[user_id]['stage'] = 'sub_service'
        
        services = {
            'materials': {
                'title': '🧱 Матеріали',
                'options': [
                    ('sub_cement', 'Цемент, розчини'),
                    ('sub_brick', 'Цегла, блоки'),
                    ('sub_sand', 'Пісок, щебінь'),
                    ('sub_metal', 'Арматура, метал'),
                    ('sub_wood', 'Дерево'),
                    ('sub_other_mat', 'Інше')
                ]
            },
            'workers': {
                'title': '👷‍♂️ Робітники',
                'options': [
                    ('sub_mason', 'Муляри'),
                    ('sub_builder', 'Будівельники'),
                    ('sub_electric', 'Електрики'),
                    ('sub_plumber', 'Сантехніки'),
                    ('sub_painter', 'Маляри'),
                    ('sub_other_work', 'Інші спеціалісти')
                ]
            },
            'tools': {
                'title': '🔧 Інструменти',
                'options': [
                    ('sub_power', 'Електроінструмент'),
                    ('sub_hand', 'Ручний інструмент'),
                    ('sub_machine', 'Техніка'),
                    ('sub_scaffold', 'Риштування'),
                    ('sub_other_tool', 'Інше обладнання')
                ]
            },
            'construction': {
                'title': '🏠 Будівельні роботи',
                'options': [
                    ('sub_foundation', 'Фундамент'),
                    ('sub_walls', 'Стіни'),
                    ('sub_roof', 'Покрівля'),
                    ('sub_finish', 'Оздоблення'),
                    ('sub_electric_work', 'Електромонтаж'),
                    ('sub_other_constr', 'Інші роботи')
                ]
            }
        }
        
        service_info = services[service]
        text = f"Обрано: {service_info['title']}\n\nОберіть деталі:"
        
        keyboard = [[InlineKeyboardButton(name, callback_data=code)] for code, name in service_info['options']]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_sub_choice(self, query, user_id, sub_service):
        user_data[user_id]['data']['sub_service'] = sub_service
        
        # Если выбрали рабочих, спрашиваем количество
        if user_data[user_id]['data']['service'] == 'workers':
            user_data[user_id]['stage'] = 'count'
            text = "Скільки спеціалістів потрібно?"
            keyboard = [
                [InlineKeyboardButton("1 спеціаліст", callback_data="count_1")],
                [InlineKeyboardButton("2-3 спеціалісти", callback_data="count_2-3")],
                [InlineKeyboardButton("4-6 спеціалістів", callback_data="count_4-6")],
                [InlineKeyboardButton("Більше 6", callback_data="count_6+")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await self.ask_contact_info(query, user_id)

    async def handle_count_choice(self, query, user_id, count):
        user_data[user_id]['data']['count'] = count.replace('count_', '')
        await self.ask_contact_info(query, user_id)

    async def ask_contact_info(self, query, user_id):
        user_data[user_id]['stage'] = 'name'
        await query.edit_message_text("👤 Напишіть ваше ім'я:")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        if user_id not in user_data:
            await update.message.reply_text("Натисніть /start")
            return

        stage = user_data[user_id]['stage']
        
        try:
            if stage == 'name':
                user_data[user_id]['data']['name'] = text
                user_data[user_id]['stage'] = 'phone'
                await update.message.reply_text("📞 Ваш телефон:")
                
            elif stage == 'phone':
                user_data[user_id]['data']['phone'] = text
                user_data[user_id]['stage'] = 'address'
                await update.message.reply_text("📍 Адреса об'єкта:")
                
            elif stage == 'address':
                user_data[user_id]['data']['address'] = text
                user_data[user_id]['stage'] = 'time'
                
                text = "⏰ Коли потрібно?"
                keyboard = [
                    [InlineKeyboardButton("🔥 Сьогодні", callback_data="time_today")],
                    [InlineKeyboardButton("⚡ Завтра", callback_data="time_tomorrow")],
                    [InlineKeyboardButton("📅 Цей тиждень", callback_data="time_week")],
                    [InlineKeyboardButton("📆 Наступний тиждень", callback_data="time_next")]
                ]
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                
        except Exception as e:
            logger.error(f"Text handling error: {e}")
            await update.message.reply_text("❌ Помилка. Спробуйте /start")

    async def handle_time_choice(self, query, user_id, time_choice):
        user_data[user_id]['data']['time'] = time_choice.replace('time_', '')
        await self.show_confirmation(query, user_id)

    async def show_confirmation(self, query, user_id):
        data = user_data[user_id]['data']
        
        # Названия услуг
        service_names = {
            'materials': 'Матеріали', 'workers': 'Робітники', 
            'tools': 'Інструменти', 'construction': 'Будівельні роботи'
        }
        
        time_names = {
            'today': 'Сьогодні', 'tomorrow': 'Завтра',
            'week': 'Цей тиждень', 'next': 'Наступний тиждень'
        }
        
        text = (
            "📋 **ПІДТВЕРДЖЕННЯ ЗАЯВКИ**\n\n"
            f"🔧 Послуга: {service_names.get(data['service'], data['service'])}\n"
            f"👤 Ім'я: {data['name']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"📍 Адреса: {data['address']}\n"
            f"⏰ Термін: {time_names.get(data['time'], data['time'])}\n"
        )
        
        if 'count' in data:
            text += f"👥 Кількість: {data['count']}\n"
        
        text += "\n✅ Підтвердити заявку?"
        
        keyboard = [[InlineKeyboardButton("✅ Підтвердити", callback_data="confirm")]]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def confirm_order(self, query, user_id, context):
        data = user_data[user_id]['data']
        
        # Отправляем в чат менеджеров
        service_names = {
            'materials': 'Матеріали', 'workers': 'Робітники',
            'tools': 'Інструменти', 'construction': 'Будівельні роботи'
        }
        
        message = (
            "🏗️ **НОВА ЗАЯВКА ДОБРОБУД**\n\n"
            f"🔧 **Послуга:** {service_names.get(data['service'], data['service'])}\n"
            f"👤 **Клієнт:** {data['name']}\n"
            f"📞 **Телефон:** {data['phone']}\n"
            f"📍 **Адреса:** {data['address']}\n"
            f"⏰ **Термін:** {data['time']}\n"
        )
        
        if 'count' in data:
            message += f"👥 **Кількість:** {data['count']}\n"
            
        message += f"\n📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n🏗️ **ДОБРОБУД**"
        
        try:
            await context.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            
            success_text = (
                "🎉 **ДЯКУЄМО!**\n\n"
                "✅ Заявку прийнято!\n"
                "📞 Менеджер зв'яжеться протягом 15 хвилин\n\n"
                "🏗️ **ДОБРОБУД**\n"
                "☎️ +38 (067) 123-45-67"
            )
            
            await query.edit_message_text(success_text, parse_mode='Markdown')
            
            # Очищаем данные
            del user_data[user_id]
            
        except Exception as e:
            logger.error(f"Send order error: {e}")
            await query.edit_message_text("❌ Помилка відправки. Зв'яжіться за телефоном: +38 (067) 123-45-67")

    async def run(self):
        """Простой запуск на Render"""
        logger.info("🚀 Запуск Dobrobud Bot...")
        
        try:
            # Запуск webhook
            await self.app.initialize()
            await self.app.start()
            
            # Webhook URL
            webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')}.onrender.com/webhook"
            
            # Устанавливаем webhook
            await self.app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"]
            )
            
            logger.info(f"✅ Webhook set: {webhook_url}")
            
            # Запуск Render webhook
            from telegram.ext import Updater
            updater = Updater(bot=self.app.bot, update_queue=self.app.update_queue)
            
            # Простой webhook сервер
            import json
            from http.server import HTTPServer, BaseHTTPRequestHandler
            
            class WebhookHandler(BaseHTTPRequestHandler):
                def do_POST(self_handler):
                    if self_handler.path == '/webhook':
                        content_length = int(self_handler.headers['Content-Length'])
                        post_data = self_handler.rfile.read(content_length)
                        
                        try:
                            update_data = json.loads(post_data.decode('utf-8'))
                            update = Update.de_json(update_data, self.app.bot)
                            
                            # Обрабатываем асинхронно
                            asyncio.create_task(self.app.process_update(update))
                            
                            self_handler.send_response(200)
                            self_handler.end_headers()
                            self_handler.wfile.write(b'OK')
                        except Exception as e:
                            logger.error(f"Webhook error: {e}")
                            self_handler.send_response(500)
                            self_handler.end_headers()
                    else:
                        self_handler.send_response(404)
                        self_handler.end_headers()
                
                def do_GET(self_handler):
                    self_handler.send_response(200)
                    self_handler.send_header('Content-type', 'text/plain')
                    self_handler.end_headers()
                    self_handler.wfile.write(b'Dobrobud Bot OK')
            
            # Запуск сервера
            server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
            logger.info(f"🌐 Server running on port {PORT}")
            server.serve_forever()
            
        except Exception as e:
            logger.error(f"❌ Start error: {e}")
            raise

def main():
    bot = DobrobudBot()
    asyncio.run(bot.run())

if __name__ == '__main__':
    main()
