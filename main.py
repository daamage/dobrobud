import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
import asyncio
from datetime import datetime
from aiohttp import web

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройки для Render
BOT_TOKEN = "8390533970:AAH7dcxqGqryY7F7UxQYlit_2z1fdcc0mAk"
CHAT_ID = -4887312460  # Чат для заявок
PORT = int(os.getenv('PORT', 8000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-dobrobud-bot.onrender.com')

user_responses = {}

class DobrobudBot:
    def __init__(self):
        # Оптимизированные настройки для Render
        self.application = Application.builder().token(BOT_TOKEN)\
            .connect_timeout(60.0)\
            .read_timeout(60.0)\
            .write_timeout(60.0)\
            .pool_timeout(60.0)\
            .build()
        self.setup_handlers()
        self.setup_error_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def setup_error_handlers(self):
        """Обработка ошибок"""
        self.application.add_error_handler(self.error_handler)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Глобальная обработка ошибок"""
        logger.error(f"Exception while handling update {update}: {context.error}")
        
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ Виникла технічна помилка. Спробуйте ще раз через хвилину або натисніть /start"
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            user_responses[user_id] = {
                'stage': 'choose_service',
                'data': {},
                'timestamp': datetime.now()
            }
            
            welcome_message = (
                "🏗️ **Вітаємо в компанії ДОБРОБУД!** 🏠\n\n"
                "🔨 Ми надаємо якісні будівельні послуги та матеріали\n"
                "👷‍♂️ Досвідчені спеціалісти та сучасне обладнання\n"
                "⚡ Швидко, якісно, надійно!\n\n"
                "📋 **Що вас цікавить?**"
            )
            
            keyboard = [
                [InlineKeyboardButton("🧱 Будівельні матеріали", callback_data="service_materials")],
                [InlineKeyboardButton("👷‍♂️ Найм робітників", callback_data="service_workers")],
                [InlineKeyboardButton("🔧 Інструменти та обладнання", callback_data="service_tools")],
                [InlineKeyboardButton("🏠 Будівельні роботи", callback_data="service_construction")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
            logger.info(f"User {user_id} started using Dobrobud bot")
        except Exception as e:
            logger.error(f"Error in start_command: {e}")

    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            info_message = (
                "🏗️ **Компанія ДОБРОБУД** 🏠\n\n"
                "📍 **Наші послуги:**\n"
                "• 🧱 Постачання будівельних матеріалів\n"
                "• 👷‍♂️ Надання кваліфікованих робітників\n"
                "• 🔧 Оренда інструментів та обладнання\n"
                "• 🏠 Виконання будівельних робіт\n\n"
                "⭐ **Чому обирають нас:**\n"
                "✅ Якісні матеріали від перевірених постачальників\n"
                "✅ Досвідчені спеціалісти з документами\n"
                "✅ Сучасне обладнання в ідеальному стані\n"
                "✅ Конкурентні ціни та гнучкі умови\n"
                "✅ Гарантія на всі види робіт\n\n"
                "📞 **Контакти:**\n"
                "📱 Телефон: +38 (067) 123-45-67\n"
                "📧 Email: info@dobrobud.ua\n"
                "🌐 Сайт: www.dobrobud.ua\n\n"
                "👆 Натисніть /start щоб залишити заявку!"
            )
            
            await update.message.reply_text(info_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in info_command: {e}")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для проверки статуса бота"""
        try:
            status_message = (
                f"🤖 **Статус бота ДОБРОБУД**\n\n"
                f"✅ Бот працює на Render\n"
                f"🕐 Час: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}\n"
                f"👥 Активних заявок: {len(user_responses)}\n"
                f"🌐 URL: `{WEBHOOK_URL}`"
            )
            await update.message.reply_text(status_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in status_command: {e}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            help_text = (
                "📋 **Команди бота ДОБРОБУД:**\n\n"
                "/start - 🚀 Почати оформлення заявки\n"
                "/info - ℹ️ Інформація про компанію\n"
                "/help - ❓ Допомога\n"
                "/status - 📊 Статус бота\n\n"
                "🏗️ **Як це працює:**\n"
                "1️⃣ Оберіть потрібну послугу\n"
                "2️⃣ Вкажіть деталі замовлення\n"
                "3️⃣ Залиште контактні дані\n"
                "4️⃣ Наш менеджер зв'яжеться з вами!\n\n"
                "💬 Просто відповідайте на питання та обирайте варіанти!"
            )
            await update.message.reply_text(help_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in help_command: {e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            text = update.message.text.strip()
            
            logger.info(f"Processing message from user {user_id}: {text}")

            if user_id not in user_responses:
                await update.message.reply_text(
                    "🔄 Будь ласка, натисніть /start щоб почати оформлення заявки.\n"
                    "ℹ️ Або /info для інформації про компанію."
                )
                return

            stage = user_responses[user_id]['stage']
            data = user_responses[user_id]['data']

            if stage == 'ask_contact_name':
                data['contact_name'] = text
                user_responses[user_id]['stage'] = 'ask_phone'
                await update.message.reply_text(
                    "📞 **Вкажіть ваш номер телефону:**\n"
                    "📱 Наприклад: +38 067 123 45 67"
                )

            elif stage == 'ask_phone':
                data['phone'] = text
                user_responses[user_id]['stage'] = 'ask_object_address'
                await update.message.reply_text(
                    "📍 **Вкажіть адресу об'єкта:**\n"
                    "🏠 Місто, вулиця, номер будинку\n"
                    "📝 Наприклад: м. Київ, вул. Хрещатик, 1"
                )

            elif stage == 'ask_object_address':
                data['object_address'] = text
                user_responses[user_id]['stage'] = 'ask_timeline'
                
                timeline_message = "⏰ **На коли потрібно?**"
                keyboard = [
                    [InlineKeyboardButton("🔥 Терміново (сьогодні)", callback_data="timeline_urgent")],
                    [InlineKeyboardButton("⚡ Завтра", callback_data="timeline_tomorrow")],
                    [InlineKeyboardButton("📅 На цьому тижні", callback_data="timeline_week")],
                    [InlineKeyboardButton("📆 На наступному тижні", callback_data="timeline_next_week")],
                    [InlineKeyboardButton("🗓️ Інший термін", callback_data="timeline_other")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(timeline_message, reply_markup=reply_markup)

            elif stage == 'ask_timeline_custom':
                data['timeline'] = text
                await self.show_final_confirmation(update, context, user_id)

            elif stage == 'ask_additional_info':
                data['additional_info'] = text
                await self.show_final_confirmation(update, context, user_id)

        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
            await update.message.reply_text("⚠️ Помилка обробки. Спробуйте ще раз або /start для перезапуску.")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        logger.info(f"CALLBACK - User {user_id} clicked: {data}")
        
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Error answering callback: {e}")
            return

        if user_id not in user_responses:
            try:
                await query.edit_message_text("🔄 Сесія втрачена. Натисніть /start щоб почати заново.")
            except Exception as e:
                logger.error(f"Error editing message: {e}")
            return

        try:
            if data.startswith("service_"):
                await self.handle_service_selection(query, context, user_id, data)
            elif data.startswith("materials_"):
                await self.handle_materials_selection(query, context, user_id, data)
            elif data.startswith("workers_"):
                await self.handle_workers_selection(query, context, user_id, data)
            elif data.startswith("tools_"):
                await self.handle_tools_selection(query, context, user_id, data)
            elif data.startswith("construction_"):
                await self.handle_construction_selection(query, context, user_id, data)
            elif data.startswith("timeline_"):
                await self.handle_timeline_selection(query, context, user_id, data)
            elif data == "confirm_order":
                await self.process_final_order(query, context, user_id)
            elif data == "edit_order":
                await self.restart_order(query, context, user_id)
            elif data == "add_info":
                await self.ask_additional_info(query, context, user_id)

        except Exception as e:
            logger.error(f"Error processing callback: {e}")
            try:
                await query.edit_message_text("❌ Помилка обробки. Спробуйте пізніше або /start")
            except:
                pass

    async def handle_service_selection(self, query, context, user_id, data):
        user_data = user_responses[user_id]['data']
        
        if data == "service_materials":
            user_data['service_type'] = "Будівельні матеріали"
            user_responses[user_id]['stage'] = 'ask_materials_type'
            
            message = "🧱 **Які матеріали потрібні?**"
            keyboard = [
                [InlineKeyboardButton("🏠 Цемент та розчини", callback_data="materials_cement")],
                [InlineKeyboardButton("🧱 Цегла та блоки", callback_data="materials_bricks")],
                [InlineKeyboardButton("🪨 Пісок, щебінь, відсів", callback_data="materials_bulk")],
                [InlineKeyboardButton("🏗️ Арматура та метал", callback_data="materials_metal")],
                [InlineKeyboardButton("🪵 Дерево та пиломатеріали", callback_data="materials_wood")],
                [InlineKeyboardButton("🏠 Покрівельні матеріали", callback_data="materials_roofing")],
                [InlineKeyboardButton("🎨 Фарби та обробка", callback_data="materials_paint")],
                [InlineKeyboardButton("📋 Інше", callback_data="materials_other")]
            ]
            
        elif data == "service_workers":
            user_data['service_type'] = "Найм робітників"
            user_responses[user_id]['stage'] = 'ask_workers_type'
            
            message = "👷‍♂️ **Які спеціалісти потрібні?**"
            keyboard = [
                [InlineKeyboardButton("🧱 Муляри", callback_data="workers_masons")],
                [InlineKeyboardButton("🔨 Будівельники-універсали", callback_data="workers_general")],
                [InlineKeyboardButton("⚡ Електрики", callback_data="workers_electricians")],
                [InlineKeyboardButton("🚿 Сантехніки", callback_data="workers_plumbers")],
                [InlineKeyboardButton("🎨 Маляри", callback_data="workers_painters")],
                [InlineKeyboardButton("🏠 Покрівельники", callback_data="workers_roofers")],
                [InlineKeyboardButton("🪟 Монтажники вікон", callback_data="workers_windows")],
                [InlineKeyboardButton("📋 Інші спеціалісти", callback_data="workers_other")]
            ]
            
        elif data == "service_tools":
            user_data['service_type'] = "Інструменти та обладнання"
            user_responses[user_id]['stage'] = 'ask_tools_type'
            
            message = "🔧 **Яке обладнання потрібно?**"
            keyboard = [
                [InlineKeyboardButton("💪 Електроінструмент", callback_data="tools_power")],
                [InlineKeyboardButton("🔨 Ручний інструмент", callback_data="tools_hand")],
                [InlineKeyboardButton("🏗️ Будівельна техніка", callback_data="tools_machinery")],
                [InlineKeyboardButton("📏 Вимірювальні прилади", callback_data="tools_measuring")],
                [InlineKeyboardButton("🚧 Риштування", callback_data="tools_scaffolding")],
                [InlineKeyboardButton("⚡ Генератори", callback_data="tools_generators")],
                [InlineKeyboardButton("💧 Насоси", callback_data="tools_pumps")],
                [InlineKeyboardButton("📋 Інше обладнання", callback_data="tools_other")]
            ]
            
        elif data == "service_construction":
            user_data['service_type'] = "Будівельні роботи"
            user_responses[user_id]['stage'] = 'ask_construction_type'
            
            message = "🏠 **Які роботи потрібно виконати?**"
            keyboard = [
                [InlineKeyboardButton("🏗️ Фундаментні роботи", callback_data="construction_foundation")],
                [InlineKeyboardButton("🧱 Кладка стін", callback_data="construction_walls")],
                [InlineKeyboardButton("🏠 Покрівельні роботи", callback_data="construction_roofing")],
                [InlineKeyboardButton("🎨 Оздоблювальні роботи", callback_data="construction_finishing")],
                [InlineKeyboardButton("⚡ Електромонтаж", callback_data="construction_electrical")],
                [InlineKeyboardButton("🚿 Сантехнічні роботи", callback_data="construction_plumbing")],
                [InlineKeyboardButton("🪟 Установка вікон/дверей", callback_data="construction_windows")],
                [InlineKeyboardButton("📋 Комплексні роботи", callback_data="construction_complex")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_materials_selection(self, query, context, user_id, data):
        user_data = user_responses[user_id]['data']
        
        material_types = {
            "materials_cement": "Цемент та розчини",
            "materials_bricks": "Цегла та блоки", 
            "materials_bulk": "Пісок, щебінь, відсів",
            "materials_metal": "Арматура та метал",
            "materials_wood": "Дерево та пиломатеріали",
            "materials_roofing": "Покрівельні матеріали",
            "materials_paint": "Фарби та обробка",
            "materials_other": "Інші матеріали"
        }
        
        user_data['specific_service'] = material_types.get(data, "Не вказано")
        user_responses[user_id]['stage'] = 'ask_contact_name'
        
        await query.edit_message_text(
            f"✅ Обрано: **{user_data['specific_service']}**\n\n"
            "👤 **Як до вас звертатися?**\n"
            "📝 Напишіть ваше ім'я:",
            parse_mode='Markdown'
        )

    async def handle_workers_selection(self, query, context, user_id, data):
        user_data = user_responses[user_id]['data']
        
        worker_types = {
            "workers_masons": "Муляри",
            "workers_general": "Будівельники-универсали",
            "workers_electricians": "Електрики",
            "workers_plumbers": "Сантехніки", 
            "workers_painters": "Маляри",
            "workers_roofers": "Покрівельники",
            "workers_windows": "Монтажники вікон",
            "workers_other": "Інші спеціалісти"
        }
        
        user_data['specific_service'] = worker_types.get(data, "Не вказано")
        
        # Додаткове питання про кількість
        user_responses[user_id]['stage'] = 'ask_workers_count'
        
        message = f"✅ Обрано: **{user_data['specific_service']}**\n\n👥 **Скільки спеціалістів потрібно?**"
        keyboard = [
            [InlineKeyboardButton("1️⃣ 1 спеціаліст", callback_data="count_1")],
            [InlineKeyboardButton("2️⃣ 2 спеціалісти", callback_data="count_2")],
            [InlineKeyboardButton("3️⃣ 3 спеціалісти", callback_data="count_3")],
            [InlineKeyboardButton("👥 4-6 спеціалістів", callback_data="count_4-6")],
            [InlineKeyboardButton("👷‍♂️ Більше 6 спеціалістів", callback_data="count_6+")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_tools_selection(self, query, context, user_id, data):
        user_data = user_responses[user_id]['data']
        
        tool_types = {
            "tools_power": "Електроінструмент",
            "tools_hand": "Ручний інструмент",
            "tools_machinery": "Будівельна техніка",
            "tools_measuring": "Вимірювальні прилади",
            "tools_scaffolding": "Риштування",
            "tools_generators": "Генератори",
            "tools_pumps": "Насоси",
            "tools_other": "Інше обладнання"
        }
        
        user_data['specific_service'] = tool_types.get(data, "Не вказано")
        user_responses[user_id]['stage'] = 'ask_contact_name'
        
        await query.edit_message_text(
            f"✅ Обрано: **{user_data['specific_service']}**\n\n"
            "👤 **Як до вас звертатися?**\n"
            "📝 Напишіть ваше ім'я:",
            parse_mode='Markdown'
        )

    async def handle_construction_selection(self, query, context, user_id, data):
        user_data = user_responses[user_id]['data']
        
        construction_types = {
            "construction_foundation": "Фундаментні роботи",
            "construction_walls": "Кладка стін",
            "construction_roofing": "Покрівельні роботи", 
            "construction_finishing": "Оздоблювальні роботи",
            "construction_electrical": "Електромонтаж",
            "construction_plumbing": "Сантехнічні роботи",
            "construction_windows": "Установка вікон/дверей",
            "construction_complex": "Комплексні роботи"
        }
        
        user_data['specific_service'] = construction_types.get(data, "Не вказано")
        user_responses[user_id]['stage'] = 'ask_contact_name'
        
        await query.edit_message_text(
            f"✅ Обрано: **{user_data['specific_service']}**\n\n"
            "👤 **Як до вас звертатися?**\n"
            "📝 Напишіть ваше ім'я:",
            parse_mode='Markdown'
        )

    async def handle_timeline_selection(self, query, context, user_id, data):
        user_data = user_responses[user_id]['data']
        
        timeline_options = {
            "timeline_urgent": "Терміново (сьогодні)",
            "timeline_tomorrow": "Завтра",
            "timeline_week": "На цьому тижні",
            "timeline_next_week": "На наступному тижні"
        }
        
        if data in timeline_options:
            user_data['timeline'] = timeline_options[data]
            await self.show_final_confirmation(query, context, user_id)
        elif data == "timeline_other":
            user_responses[user_id]['stage'] = 'ask_timeline_custom'
            await query.edit_message_text(
                "📅 **Вкажіть бажану дату:**\n"
                "📝 Наприклад: 25.09.2025 або через 2 тижні"
            )

    async def handle_workers_count(self, query, context, user_id, data):
        if data.startswith("count_"):
            user_data = user_responses[user_id]['data']
            count_mapping = {
                "count_1": "1 спеціаліст",
                "count_2": "2 спеціалісти", 
                "count_3": "3 спеціалісти",
                "count_4-6": "4-6 спеціалістів",
                "count_6+": "Більше 6 спеціалістів"
            }
            
            user_data['workers_count'] = count_mapping.get(data, "Не вказано")
            user_responses[user_id]['stage'] = 'ask_contact_name'
            
            await query.edit_message_text(
                f"✅ Обрано: **{user_data['specific_service']}**\n"
                f"👥 Кількість: **{user_data['workers_count']}**\n\n"
                "👤 **Як до вас звертатися?**\n"
                "📝 Напишіть ваше ім'я:",
                parse_mode='Markdown'
            )

    async def show_final_confirmation(self, update_or_query, context, user_id):
        user_data = user_responses[user_id]['data']
        
        confirmation_message = (
            "📋 **ПІДТВЕРДЖЕННЯ ЗАЯВКИ**\n\n"
            f"🏗️ **Послуга:** {user_data.get('service_type', '-')}\n"
            f"📦 **Деталі:** {user_data.get('specific_service', '-')}\n"
        )
        
        if 'workers_count' in user_data:
            confirmation_message += f"👥 **Кількість:** {user_data['workers_count']}\n"
            
        confirmation_message += (
            f"👤 **Контактна особа:** {user_data.get('contact_name', '-')}\n"
            f"📞 **Телефон:** {user_data.get('phone', '-')}\n"
            f"📍 **Адреса об'єкта:** {user_data.get('object_address', '-')}\n"
            f"⏰ **Термін:** {user_data.get('timeline', '-')}\n\n"
            "✅ **Підтвердіть заявку:**"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Підтвердити заявку", callback_data="confirm_order")],
            [InlineKeyboardButton("📝 Додати примітки", callback_data="add_info")],
            [InlineKeyboardButton("✏️ Редагувати", callback_data="edit_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update_or_query, 'edit_message_text'):
            await update_or_query.edit_message_text(
                confirmation_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update_or_query.message.reply_text(
                confirmation_message,
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )

    async def ask_additional_info(self, query, context, user_id):
        user_responses[user_id]['stage'] = 'ask_additional_info'
        await query.edit_message_text(
            "📝 **Додаткова інформація:**\n\n"
            "Опишіть детальніше ваші потреби:\n"
            "• Обсяги робіт\n"
            "• Особливі вимоги\n"
            "• Бюджет\n"
            "• Інші побажання"
        )

    async def restart_order(self, query, context, user_id):
        user_responses[user_id] = {
            'stage': 'choose_service',
            'data': {},
            'timestamp': datetime.now()
        }
        
        message = (
            "🔄 **Почнемо спочатку**\n\n"
            "🏗️ **Що вас цікавить?**"
        )
        
        keyboard = [
            [InlineKeyboardButton("🧱 Будівельні матеріали", callback_data="service_materials")],
            [InlineKeyboardButton("👷‍♂️ Найм робітників", callback_data="service_workers")],
            [InlineKeyboardButton("🔧 Інструменти та обладнання", callback_data="service_tools")],
            [InlineKeyboardButton("🏠 Будівельні роботи", callback_data="service_construction")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def process_final_order(self, query, context, user_id):
        """Обработка финального подтверждения заявки"""
        try:
            user_data = user_responses[user_id]['data']
            
            # Отправляем заявку в чат менеджеров
            await self.send_order_to_managers(query, context, user_id, user_data)
            
            # Показываем сообщение об успешной отправке
            await self.show_success_message(query, context)
            
            # Удаляем пользователя из активных заявок
            del user_responses[user_id]
            
            logger.info(f"Successfully processed order for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error processing final order: {e}")
            await query.edit_message_text("❌ Помилка відправки заявки. Спробуйте пізніше або зв'яжіться з нами за телефоном.")

    async def send_order_to_managers(self, query, context, user_id, user_data):
        """Отправка заявки менеджерам"""
        try:
            message = (
                "🏗️ **НОВА ЗАЯВКА - ДОБРОБУД**\n\n"
                f"📦 **Послуга:** {user_data.get('service_type', '-')}\n"
                f"🔧 **Деталі:** {user_data.get('specific_service', '-')}\n"
            )
            
            if 'workers_count' in user_data:
                message += f"👥 **Кількість:** {user_data['workers_count']}\n"
                
            message += (
                f"👤 **Клієнт:** {user_data.get('contact_name', '-')}\n"
                f"📞 **Телефон:** {user_data.get('phone', '-')}\n"
                f"📍 **Адреса:** {user_data.get('object_address', '-')}\n"
                f"⏰ **Термін:** {user_data.get('timeline', '-')}\n"
            )
            
            if 'additional_info' in user_data:
                message += f"📝 **Додаткова інформація:** {user_data['additional_info']}\n"
                
            message += (
                f"\n📅 **Дата заявки:** {datetime.now().strftime('%d.%m.%Y о %H:%M')}\n"
                f"🆔 **User ID:** {user_id}\n"
                "────────────────────────\n"
                "🏗️ **Компанія ДОБРОБУД**"
            )

            await context.bot.send_message(CHAT_ID, message, parse_mode='Markdown')
            logger.info(f"Order sent to managers for user {user_id}")
        except Exception as e:
            logger.error(f"Error sending order to managers: {e}")
            raise

    async def show_success_message(self, query, context):
        """Показ сообщения об успешной отправке заявки"""
        try:
            success_message = (
                "🎉 **ДЯКУЄМО ЗА ЗАЯВКУ!**\n\n"
                "✅ **Ваша заявка успішно відправлена**\n\n"
                "⏰ **Що далі?**\n"
                "📞 Наш менеджер зв'яжеться з вами протягом 15-30 хвилин\n"
                "📋 Обговоримо всі деталі та узгодимо умови\n"
                "💰 Розрахуємо вартість та строки виконання\n\n"
                "🏗️ **Компанія ДОБРОБУД**\n"
                "🔥 Будуємо якісно, швидко, надійно!\n\n"
                "📱 **Контакти для зв'язку:**\n"
                "☎️ +38 (067) 123-45-67\n"
                "📧 info@dobrobud.ua\n\n"
                "💬 Щоб залишити нову заявку - /start"
            )
            
            await query.edit_message_text(success_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error showing success message: {e}")
            raise

    # Обработка случая когда нужно обработать кнопки выбора количества
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        logger.info(f"CALLBACK - User {user_id} clicked: {data}")
        
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Error answering callback: {e}")
            return

        if user_id not in user_responses:
            try:
                await query.edit_message_text("🔄 Сесія втрачена. Натисніть /start щоб почати заново.")
            except Exception as e:
                logger.error(f"Error editing message: {e}")
            return

        try:
            if data.startswith("service_"):
                await self.handle_service_selection(query, context, user_id, data)
            elif data.startswith("materials_"):
                await self.handle_materials_selection(query, context, user_id, data)
            elif data.startswith("workers_"):
                await self.handle_workers_selection(query, context, user_id, data)
            elif data.startswith("tools_"):
                await self.handle_tools_selection(query, context, user_id, data)
            elif data.startswith("construction_"):
                await self.handle_construction_selection(query, context, user_id, data)
            elif data.startswith("count_"):
                await self.handle_workers_count(query, context, user_id, data)
            elif data.startswith("timeline_"):
                await self.handle_timeline_selection(query, context, user_id, data)
            elif data == "confirm_order":
                await self.process_final_order(query, context, user_id)
            elif data == "edit_order":
                await self.restart_order(query, context, user_id)
            elif data == "add_info":
                await self.ask_additional_info(query, context, user_id)

        except Exception as e:
            logger.error(f"Error processing callback: {e}")
            try:
                await query.edit_message_text("❌ Помилка обробки. Спробуйте пізніше або /start")
            except:
                pass

    async def run_webhook(self):
        """Запуск webhook сервера для Render"""
        try:
            # Инициализируем приложение
            await self.application.initialize()
            await self.application.start()
            
            # Создаем веб-приложение
            app = web.Application()

            async def handle_post(request):
                try:
                    data = await request.json()
                    logger.info(f"Webhook received update: {data.get('update_id', 'unknown')}")
                    
                    update = Update.de_json(data, self.application.bot)
                    if update is None:
                        logger.error("Failed to parse update from JSON")
                        return web.Response(text="ERROR", status=400)
                    
                    # Обрабатываем обновление
                    await self.application.process_update(update)
                    return web.Response(text="OK")
                    
                except Exception as e:
                    logger.error(f"Webhook processing error: {e}")
                    return web.Response(text="ERROR", status=500)

            async def handle_get(request):
                return web.Response(text="Dobrobud Bot працює на Render")

            async def handle_health(request):
                return web.Response(text="OK", status=200)

            async def handle_status(request):
                status_data = {
                    "status": "running",
                    "timestamp": datetime.now().isoformat(),
                    "service": "Dobrobud Construction Bot",
                    "platform": "Render",
                    "active_orders": len(user_responses)
                }
                return web.json_response(status_data)

            # Настраиваем маршруты
            app.router.add_post('/webhook', handle_post)
            app.router.add_get('/webhook', handle_get)
            app.router.add_get('/health', handle_health)
            app.router.add_get('/status', handle_status)
            app.router.add_get('/', handle_health)

            # Запускаем сервер
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', PORT)
            await site.start()
            logger.info(f"Web server started on port {PORT}")

            # Настраиваем webhook
            webhook_url = f"{WEBHOOK_URL}/webhook"
            
            try:
                # Удаляем старый webhook
                await self.application.bot.delete_webhook(drop_pending_updates=True)
                logger.info("Previous webhook deleted")
                
                # Ждем немного
                await asyncio.sleep(2)
                
                # Устанавливаем новый webhook
                webhook_set = await self.application.bot.set_webhook(
                    url=webhook_url,
                    drop_pending_updates=True,
                    max_connections=20,
                    allowed_updates=["message", "callback_query"]
                )
                
                if webhook_set:
                    logger.info(f"✅ Webhook успешно установлен: {webhook_url}")
                else:
                    logger.error("❌ Ошибка установки webhook")
                
                # Проверяем webhook
                webhook_info = await self.application.bot.get_webhook_info()
                logger.info(f"Webhook info: URL={webhook_info.url}, Pending={webhook_info.pending_update_count}")
                
            except Exception as e:
                logger.error(f"Webhook setup error: {e}")
                raise
            
            logger.info("🚀 Dobrobud Bot успешно запущен на Render")
            
            # Основной цикл
            try:
                while True:
                    await asyncio.sleep(300)  # 5 минут
                    logger.info("Bot heartbeat - Dobrobud on Render")
            except KeyboardInterrupt:
                logger.info("Bot stopping by user...")
            except Exception as e:
                logger.error(f"Bot runtime error: {e}")
            finally:
                logger.info("Stopping bot...")
                await self.application.stop()
                await self.application.shutdown()

        except Exception as e:
            logger.error(f"Critical startup error: {e}")
            raise

async def main():
    logger.info("🚀 Starting Dobrobud Construction Bot on Render...")
    try:
        bot = DobrobudBot()
        await bot.run_webhook()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        # Попробуем еще раз через 10 секунд
        await asyncio.sleep(10)
        try:
            bot = DobrobudBot()
            await bot.run_webhook()
        except Exception as retry_error:
            logger.error(f"Retry failed: {retry_error}")
            raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        exit(1)
