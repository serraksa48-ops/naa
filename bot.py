import os
import asyncio
from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

BOT_TOKEN = '8965425942:AAHnuuR61iu5B_W31k9yIxllNdPWWt12vIE'
ADMIN_ID = 8276069267

# ឈ្មោះរូបភាព QR ដែល Upload លើ GitHub
QR_IMAGE_FILENAME = 'aba_qr.jpg'

stock = {
    "via_kh": ["100081234567890|Pass123!|2FASECRETKEY1"],
    "via_us": ["100091234567892|PassUs123|2FASECRETKEY3"]
}

user_balances = {}

# Menu ប៊ូតុងចុចធំៗនៅខាងក្រោមអេក្រង់
def get_bottom_keyboard():
    keyboard = [
        [KeyboardButton("🛒 ទិញអាខោន FB"), KeyboardButton("💳 បញ្ចូលលុយ (ស្កេន QR)")],
        [KeyboardButton("👤 គណនីខ្ញុំ"), KeyboardButton("📞 ជំនួយ / Support")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in user_balances:
        user_balances[user.id] = 0.0
    await update.message.reply_text(
        f"👋 សួស្តី **{user.first_name}**!\n\nសូមស្វាគមន៍មកកាន់ប្រព័ន្ធទិញ-លក់អាខោន Facebook ស្វ័យប្រវត្តិ។\nសូមជ្រើសរើសមុខងារពីប៊ូតុងខាងក្រោម៖",
        parse_mode='Markdown',
        reply_markup=get_bottom_keyboard()
    )

async def show_buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"🇰🇭 FB Via Cambodia ($1.50) [សល់: {len(stock['via_kh'])}]", callback_data='buy_via_kh')],
        [InlineKeyboardButton(f"🇺🇸 FB Via USA ($2.00) [សល់: {len(stock['via_us'])}]", callback_data='buy_via_us')]
    ]
    await update.message.reply_text(
        "📦 **សូមជ្រើសរើសប្រភេទអាខោន FB ដែលចង់ទិញ:**",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_deposit_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "📲 **ស្កេន KHQR ដើម្បីបង់ប្រាក់តាម ABA App**\n\n"
        "👤 ឈ្មោះ: `CHATHEA NOCH`\n"
        "🏦 លេខគណនី: `019 088 273` / `019 088 270`\n\n"
        "⚠️ **ចំណាំ:** សូមផ្ទេរទឹកប្រាក់តាមតម្លៃដែលចង់បញ្ចូល រួច **Screenshot វិក្កយបត្រ** ផ្ញើចូល Chat នេះដើម្បី Admin បញ្ចូលលុយជូន។"
    )
    try:
        with open(QR_IMAGE_FILENAME, 'rb') as photo_file:
            await update.message.reply_photo(photo=photo_file, caption=caption, parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("⚠️ រូបភាព QR Code កំពុងរៀបចំ សូមព្យាយាមម្តងទៀត ឬទាក់ទង Admin។")

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"👤 **ព័ត៌មានគណនី**\n\n🆔 Telegram ID: `{user_id}`\n💰 សមតុល្យ: **${user_balances.get(user_id, 0.0):.2f}**",
        parse_mode='Markdown'
    )

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 **ផ្នែកបម្រើអតិថិជន:**\nសូមទាក់ទងមកកាន់ Admin ផ្ទាល់ សម្រាប់ការសាកសួរព័ត៌មានបន្ថែម។")

# Handler សម្រាប់ទិញអាខោន (Inline Callbacks)
async def buy_via_kh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    price = 1.50
    balance = user_balances.get(user_id, 0.0)

    if not stock["via_kh"]:
        return await query.answer("❌ ស្តុក FB Via KH អស់ហើយ!", show_alert=True)
    if balance < price:
        return await query.answer(f"❌ សមតុល្យមិនគ្រប់គ្រាន់! (${balance:.2f} / ${price})", show_alert=True)

    user_balances[user_id] -= price
    account = stock["via_kh"].pop()
    await query.answer()
    await context.bot.send_message(chat_id=user_id, text=f"🎉 **ការទិញបានជោគជ័យ!**\n\n📦 FB Via Cambodia\n📋 ទិន្នន័យ:\n`{account}`", parse_mode='Markdown')

async def buy_via_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    price = 2.00
    balance = user_balances.get(user_id, 0.0)

    if not stock["via_us"]:
        return await query.answer("❌ ស្តុក FB Via US អស់ហើយ!", show_alert=True)
    if balance < price:
        return await query.answer(f"❌ សមតុល្យមិនគ្រប់គ្រាន់! (${balance:.2f} / ${price})", show_alert=True)

    user_balances[user_id] -= price
    account = stock["via_us"].pop()
    await query.answer()
    await context.bot.send_message(chat_id=user_id, text=f"🎉 **ការទិញបានជោគជ័យ!**\n\n📦 FB Via USA\n📋 ទិន្នន័យ:\n`{account}`", parse_mode='Markdown')

# ទទួលរូបភាពវិក្កយបត្រពីភ្ញៀវ
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    await update.message.reply_text("⏳ វិក្កយបត្រត្រូវបានបញ្ជូនទៅ Admin ហើយ! សូមរង់ចាំការត្រួតពិនិត្យ។")
    user_name = f"@{user.username}" if user.username else user.first_name
    keyboard = [
        [InlineKeyboardButton("✅ +$1", callback_data=f"app_{user.id}_1"), InlineKeyboardButton("✅ +$2", callback_data=f"app_{user.id}_2"), InlineKeyboardButton("✅ +$5", callback_data=f"app_{user.id}_5")],
        [InlineKeyboardButton("✅ +$10", callback_data=f"app_{user.id}_10"), InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")]
    ]
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=f"📥 សំណើបញ្ចូលលុយពី {user_name} (`{user.id}`)", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# Admin ចុច Approve / Reject
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    action = data[0]
    target_user_id = int(data[1])

    if action == 'app':
        amount = float(data[2])
        user_balances[target_user_id] = user_balances.get(target_user_id, 0.0) + amount
        await query.answer("ជោគជ័យ!")
        await query.edit_message_caption(f"✅ បានអនុម័ត +${amount:.2f} ជូន User: `{target_user_id}`")
        await context.bot.send_message(chat_id=target_user_id, text=f"🎉 បានបញ្ចូលលុយ **+${amount:.2f}** ជោគជ័យ!", parse_mode='Markdown')
    elif action == 'rej':
        await query.answer("បដិសេធ!")
        await query.edit_message_caption(f"❌ បានបដិសេធសំណើ User: `{target_user_id}`")
        await context.bot.send_message(chat_id=target_user_id, text="❌ វិក្កយបត្រមិនត្រឹមត្រូវ។")

# Handler ចាប់យកការចុចប៊ូតុងខាងក្រោមអេក្រង់
async def handle_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🛒 ទិញអាខោន FB":
        await show_buy_menu(update, context)
    elif text == "💳 បញ្ចូលលុយ (ស្កេន QR)":
        await show_deposit_qr(update, context)
    elif text == "👤 គណនីខ្ញុំ":
        await show_profile(update, context)
    elif text == "📞 ជំនួយ / Support":
        await show_support(update, context)

# Web Server សម្រាប់ Render
async def handle_ping(request):
    return web.Response(text="Bot is running active 24/7!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    # ចាប់យកអត្ថបទប៊ូតុងចុចខាងក្រោម
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_buttons))
    
    # Callbacks សម្រាប់ទិញ និង Admin Approve
    bot_app.add_handler(CallbackQueryHandler(buy_via_kh, pattern='^buy_via_kh$'))
    bot_app.add_handler(CallbackQueryHandler(buy_via_us, pattern='^buy_via_us$'))
    bot_app.add_handler(CallbackQueryHandler(admin_actions, pattern='^(app|rej)_'))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    await run_web_server()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    
    print("🚀 Bot is running with Bottom Menu Keyboard...")
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
