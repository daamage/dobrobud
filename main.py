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

BOT_TOKEN = "8390533970:AAH7dcxqGqryY7F7UxQYlit_2z1fdcc0mAk"
CHAT_ID = -4887312460
PORT = int(os.getenv('PORT', 8000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://dobrobud.onrender.com')

user_responses = {}

class DobrobudBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("webhook_info", self.webhook_info_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_responses[user_id] = {
            'stage': 'ask_service',
            'data': {},
            'timestamp': datetime.now()
        }
        
        welcome_message = (
            "🏗️ Вітаємо в компанії ДОБРОБУД!\n\n"
            "🔨 Ми надаємо якісні будівельні послуги\n"
            "👷‍♂️ Досвідчені спеціалісти та сучасне обладнання\n"
            "⚡ Швидко, якісно, надійно!\n\n"
            "📋 Що вас цікавить?"
        )
        
        keyboard = [
            [InlineKeyboardButton("🧱 Будівельні матеріали", callback_data="service_materials")],
            [InlineKeyboardButton("👷‍♂️ Найм робітників", callback_data="service_workers")],
            [InlineKeyboardButton("🔧 Інструменти та обладнання", callback_data="service_tools")],
            [InlineKeyboardButton("🏠 Будівельні роботи", callback_data="service_construction")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def webhook_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            webhook_info = await context.bot.get_webhook_info()
            info_text = (
                f"🔗 **Webhook Info:**\n"
                f"URL: `{webhook_info.url}`\n"
                f"Has Custom Certificate: {webhook_info.has_custom_certificate}\n"
                f"Pending Update Count: {webhook_info.pending_update_count}\n"
                f"Last Error Date: {webhook_info.last_error_date}\n"
                f"Last Error Message: {webhook_info.last_error_message}\n"
                f"Max Connections: {webhook_info.max_connections}"
            )
            await update.message.reply_text(info_text, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"Error getting webhook info: {e}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📋 Для оформлення заявки надішліть /start\n"
            "🏗️ Просто відповідайте на запитання та обирайте варіанти.\n"
            "📞 По кнопках обирайте потрібні послуги."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        logger.info(f"Processing message from user {user_id}: {text}")

        if user_id not in user_responses:
            await update.message.reply_text("Будь ласка, надішліть /start щоб почати оформлення заявки.")
            return

        stage = user_responses[user_id]['stage']
        data = user_responses[user_id]['data']

        if stage == 'ask_name':
            data['name'] = text
            user_responses[user_id]['stage'] = 'ask_phone'
            await update.message.reply_text("📞 Вкажіть ваш контактний номер телефону:")

        elif stage == 'ask_phone':
            data['phone'] = text
            user_responses[user_id]['stage'] = 'ask_address'
            await update.message.reply_text("📍 Вкажіть адресу об'єкта:")

        elif stage == 'ask_address':
            data['address'] = text
            user_responses[user_id]['stage'] = 'ask_timing'
            
            timing_message = "⏰ На коли потрібно?"
            keyboard = [
                [InlineKeyboardButton("🔥 Терміново (сьогодні)", callback_data="timing_urgent")],
                [InlineKeyboardButton("⚡ Завтра", callback_data="timing_tomorrow")],
                [InlineKeyboardButton("📅 На цьому тижні", callback_data="timing_week")],
                [InlineKeyboardButton("📆 На наступному тижні", callback_data="timing_next_week")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(timing_message, reply_markup=reply_markup)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        logger.info(f"CALLBACK QUERY - Button clicked by user {user_id}: {data}")
        
        try:
            await query.answer()
            logger.info(f"CALLBACK QUERY - Successfully answered callback for user {user_id}")
        except Exception as e:
            logger.error(f"CALLBACK QUERY - Error answering callback: {e}")
            return

        if user_id not in user_responses:
            logger.warning(f"CALLBACK QUERY - User {user_id} not found in user_responses")
            try:
                await query.edit_message_text("Сесія втрачена. Почніть заново /start.")
            except Exception as e:
                logger.error(f"CALLBACK QUERY - Error editing message: {e}")
            return

        if data.startswith("service_"):
            await self.handle_service_selection(query, user_id, data)
        elif data.startswith("subservice_"):
            await self.handle_subservice_selection(query, user_id, data)
        elif data.startswith("count_"):
            await self.handle_count_selection(query, user_id, data)
        elif data.startswith("timing_"):
            await self.handle_timing_selection(query, user_id, data)
        elif data == "confirm_order":
            await self.confirm_final_order(query, context, user_id)

    async def handle_service_selection(self, query, user_id, service_data):
        user_responses[user_id]['data']['service'] = service_data
        
        if service_data == "service_materials":
            user_responses[user_id]['stage'] = 'ask_subservice'
            keyboard = [
                [InlineKeyboardButton("🧱 Цемент та розчини", callback_data="subservice_cement")],
                [InlineKeyboardButton("🏠 Цегла та блоки", callback_data="subservice_bricks")],
                [InlineKeyboardButton("🪨 Пісок, щебінь", callback_data="subservice_sand")],
                [InlineKeyboardButton("🔩 Арматура, метал", callback_data="subservice_metal")],
                [InlineKeyboardButton("🪵 Дерево, пиломатеріали", callback_data="subservice_wood")],
                [InlineKeyboardButton("📋 Інше", callback_data="subservice_other_materials")]
            ]
            message = "🧱 Які матеріали потрібні?"
            
        elif service_data == "service_workers":
            user_responses[user_id]['stage'] = 'ask_subservice'
            keyboard = [
                [InlineKeyboardButton("🧱 Муляри", callback_data="subservice_masons")],
                [InlineKeyboardButton("🔨 Будівельники-універсали", callback_data="subservice_builders")],
                [InlineKeyboardButton("⚡ Електрики", callback_data="subservice_electricians")],
                [InlineKeyboardButton("🚿 Сантехніки", callback_data="subservice_plumbers")],
                [InlineKeyboardButton("🎨 Маляри", callback_data="subservice_painters")],
                [InlineKeyboardButton("📋 Інші спеціалісти", callback_data="subservice_other_workers")]
            ]
            message = "👷‍♂️ Які спеціалісти потрібні?"
            
        elif service_data == "service_tools":
            user_responses[user_id]['stage'] = 'ask_subservice'
            keyboard = [
                [InlineKeyboardButton("💪 Електроінструмент", callback_data="subservice_power_tools")],
                [InlineKeyboardButton("🔨 Ручний інструмент", callback_data="subservice_hand_tools")],
                [InlineKeyboardButton("🏗️ Будівельна техніка", callback_data="subservice_machinery")],
                [InlineKeyboardButton("🚧 Риштування", callback_data="subservice_scaffolding")],
                [InlineKeyboardButton("📋 Інше обладнання", callback_data="subservice_other_tools")]
            ]
            message = "🔧 Яке обладнання потрібно?"
            
        elif service_data == "service_construction":
            user_responses[user_id]['stage'] = 'ask_subservice'
            keyboard = [
                [InlineKeyboardButton("🏗️ Фундаментні роботи", callback_data="subservice_foundation")],
                [InlineKeyboardButton("🧱 Кладка стін", callback_data="subservice_walls")],
                [InlineKeyboardButton("🏠 Покрівельні роботи", callback_data="subservice_roofing")],
                [InlineKeyboardButton("🎨 Оздоблювальні роботи", callback_data="subservice_finishing")],
                [InlineKeyboardButton("⚡ Електромонтаж", callback_data="subservice_electrical")],
                [InlineKeyboardButton("📋 Комплексні роботи", callback_data="subservice_complex")]
            ]
            message = "🏠 Які роботи потрібно виконати?"
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    async def handle_subservice_selection(self, query, user_id, subservice_data):
        user_responses[user_id]['data']['subservice'] = subservice_data
        
        # Если выбрали рабочих, спрашиваем количество
        if user_responses[user_id]['data']['service'] == "service_workers":
            user_responses[user_id]['stage'] = 'ask_count'
            message = "👥 Скільки спеціалістів потрібно?"
            keyboard = [
                [InlineKeyboardButton("1️⃣ 1 спеціаліст", callback_data="count_1")],
                [InlineKeyboardButton("2️⃣ 2 спеціалісти", callback_data="count_2")],
                [InlineKeyboardButton("3️⃣ 3 спеціалісти", callback_data="count_3")],
                [InlineKeyboardButton("👥 4-6 спеціалістів", callback_data="count_4-6")],
                [InlineKeyboardButton("👷‍♂️ Більше 6", callback_data="count_6+")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            # Переходим к запросу имени
            user_responses[user_id]['stage'] = 'ask_name'
            await query.edit_message_text("👤 Напишіть, будь ласка, ваше ім'я:")

    async def handle_count_selection(self, query, user_id, count_data):
        user_responses[user_id]['data']['count'] = count_data
        user_responses[user_id]['stage'] = 'ask_name'
        await query.edit_message_text("👤 Напишіть, будь ласка, ваше ім'я:")

    async def handle_timing_selection(self, query, user_id, timing_data):
        user_responses[user_id]['data']['timing'] = timing_data
        await self.show_confirmation(query, user_id)

    async def show_confirmation(self, query, user_id):
        data = user_responses[user_id]['data']
        
        # Названия сервисов
        service_names = {
            'service_materials': 'Будівельні матеріали',
            'service_workers': 'Найм робітників', 
            'service_tools': 'Інструменти та обладнання',
            'service_construction': 'Будівельні роботи'
        }
        
        # Названия сроков
        timing_names = {
            'timing_urgent': 'Терміново (сьогодні)',
            'timing_tomorrow': 'Завтра',
            'timing_week': 'На цьому тижні',
            'timing_next_week': 'На наступному тижні'
        }
        
        confirmation_message = (
            "✅ **ПІДТВЕРДЖЕННЯ ЗАЯВКИ**\n\n"
            f"🔧 **Послуга:** {service_names.get(data.get('service'), 'Не вказано')}\n"
            f"👤 **Ім'я:** {data.get('name', '-')}\n"
            f"📞 **Телефон:** {data.get('phone', '-')}\n"
            f"📍 **Адреса об'єкта:** {data.get('address', '-')}\n"
            f"⏰ **Термін:** {timing_names.get(data.get('timing'), 'Не вказано')}\n"
        )
        
        if 'count' in data:
            count_names = {
                'count_1': '1 спеціаліст',
                'count_2': '2 спеціалісти',
                'count_3': '3 спеціалісти',
                'count_4-6': '4-6 спеціалістів',
                'count_6+': 'Більше 6 спеціалістів'
            }
            confirmation_message += f"👥 **Кількість:** {count_names.get(data['count'], 'Не вказано')}\n"
        
        confirmation_message += "\nПідтвердіть вашу заявку:"
        
        keyboard = [
            [InlineKeyboardButton("✅ Підтверджую заявку", callback_data="confirm_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            confirmation_message, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def confirm_final_order(self, query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        logger.info(f"CALLBACK QUERY - User {user_id} confirming order")
        
        try:
            await self.send_order_to_chat(query, context, user_id)
            await self.show_success_message(query, context)
            del user_responses[user_id]
            logger.info(f"CALLBACK QUERY - Successfully processed order for user {user_id}")
            
        except Exception as e:
            logger.error(f"CALLBACK QUERY - Error processing order: {e}")
            await query.edit_message_text("❌ Помилка оформлення заявки. Спробуйте пізніше.")

    async def send_order_to_chat(self, query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        data = user_responses[user_id]['data']
        
        service_names = {
            'service_materials': 'Будівельні матеріали',
            'service_workers': 'Найм робітників',
            'service_tools': 'Інструменти та обладнання', 
            'service_construction': 'Будівельні роботи'
        }
        
        timing_names = {
            'timing_urgent': 'Терміново (сьогодні)',
            'timing_tomorrow': 'Завтра',
            'timing_week': 'На цьому тижні',
            'timing_next_week': 'На наступному тижні'
        }
        
        message = (
            "🏗️ **НОВА ЗАЯВКА - ДОБРОБУД**\n\n"
            f"🔧 **Послуга:** {service_names.get(data.get('service'), 'Не вказано')}\n"
            f"👤 **Клієнт:** {data.get('name', '-')}\n"
            f"📞 **Телефон:** {data.get('phone', '-')}\n"
            f"📍 **Адреса:** {data.get('address', '-')}\n"
            f"⏰ **Термін:** {timing_names.get(data.get('timing'), 'Не вказано')}\n"
        )
        
        if 'count' in data:
            count_names = {
                'count_1': '1 спеціаліст',
                'count_2': '2 спеціалісти', 
                'count_3': '3 спеціалісти',
                'count_4-6': '4-6 спеціалістів',
                'count_6+': 'Більше 6 спеціалістів'
            }
            message += f"👥 **Кількість:** {count_names.get(data['count'], 'Не вказано')}\n"
            
        message += (
            f"\n📅 **Дата заявки:** {datetime.now().strftime('%d.%m.%Y о %H:%M')}\n"
            f"🆔 **User ID:** {user_id}\n"
            "────────────────────────\n"
            "🏗️ **Компанія ДОБРОБУД**"
        )

        await context.bot.send_message(CHAT_ID, message, parse_mode='Markdown')

    async def show_success_message(self, query, context):
        success_message = (
            "🎉 **ДЯКУЄМО ЗА ЗАЯВКУ!**\n\n"
            "✅ **Компанія ДОБРОБУД прийняла вашу заявку**\n\n"
            "⏰ **Що далі?**\n"
            "📞 Наш менеджер зв'яжеться з вами протягом 15-30 хвилин\n"
            "📋 Обговоримо всі деталі та узгодимо умови\n"
            "💰 Розрахуємо вартість та строки виконання\n\n"
            "🏗️ **Компанія ДОБРОБУД**\n"
            "🔥 Будуємо якісно, швидко, надійно!\n\n"
            "📱 **Контакти:**\n"
            "☎️ +38 (067) 123-45-67\n"
            "📧 info@dobrobud.ua\n\n"
            "💬 Щоб залишити нову заявку - /start"
        )
        
        await query.edit_message_text(success_message, parse_mode='Markdown')

    async def run_webhook(self):
        await self.application.initialize()
        await self.application.start()
        
        app = web.Application()

        async def handle_post(request):
            try:
                data = await request.json()
                logger.info(f"Received webhook data: {data}")
                
                if 'callback_query' in data:
                    logger.info(f"WEBHOOK - Callback query detected: {data['callback_query']}")
                elif 'message' in data:
                    logger.info(f"WEBHOOK - Regular message detected: {data['message']}")
                else:
                    logger.warning(f"WEBHOOK - Unknown update type: {list(data.keys())}")
                
                update = Update.de_json(data, self.application.bot)
                
                if update is None:
                    logger.error("WEBHOOK - Failed to parse update from JSON")
                    return web.Response(text="ERROR: Failed to parse update", status=400)
                
                logger.info(f"WEBHOOK - Successfully parsed update: {update.update_id}")
                
                await self.application.process_update(update)
                logger.info(f"WEBHOOK - Successfully processed update: {update.update_id}")
                
                return web.Response(text="OK")
            except Exception as e:
                logger.error(f"WEBHOOK - Error processing webhook: {e}", exc_info=True)
                return web.Response(text="ERROR", status=500)

        async def handle_get(request):
            return web.Response(text="Dobrobud Bot працює")

        async def handle_health(request):
            return web.Response(text="OK")

        async def handle_uptime(request):
            uptime_data = {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "service": "Dobrobud Construction Bot"
            }
            return web.json_response(uptime_data)

        app.router.add_post('/webhook', handle_post)
        app.router.add_get('/webhook', handle_get)
        app.router.add_get('/health', handle_health)
        app.router.add_get('/uptime', handle_uptime)
        app.router.add_get('/', handle_health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()

        webhook_url = f"{WEBHOOK_URL}/webhook"
        
        try:
            await self.application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Deleted existing webhook")
            
            await asyncio.sleep(2)
            
            result = await self.application.bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                max_connections=40,
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"Webhook встановлено: {webhook_url}, result: {result}")
            
            webhook_info = await self.application.bot.get_webhook_info()
            logger.info(f"Webhook verification: {webhook_info}")
            
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            raise
        
        logger.info("Dobrobud Bot запущено на webhook")

        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Bot stopped")
        finally:
            await self.application.stop()
            await self.application.shutdown()

async def main():
    bot = DobrobudBot()
    await bot.run_webhook()

if __name__ == '__main__':
    asyncio.run(main())
