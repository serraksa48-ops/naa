import os
import asyncio
import io
import qrcode
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

BOT_TOKEN = '8965425942:AAHnuuR61iu5B_W31k9yIxllNdPWWt12vIE'
ADMIN_ID = 8276069267

# ℹ️ ដាក់លេខគណនី ABA របស់អ្នកនៅទីនេះ (ផ្អែកលើរូប Profile របស់អ្នកគឺ 10517445)
ABA_ACCOUNT_NUMBER = '10517445'
MERCHANT_NAME = 'CHATHEA NOCH'

stock = {
    "via_kh": ["100081234567890|Pass123!|2FASECRETKEY1"],
    "via_us": ["100091234567892|PassUs123|2FASECRETKEY3"]
}

user_balances = {}

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 ទិញអាខោន FB", callback_data='buy_menu')],
        [InlineKeyboardButton("💳 បញ្ចូលលុយ (ស្កេន QR)", callback_data='deposit'), InlineKeyboardButton("👤 គណនីខ្ញុំ", callback_data='my_profile')],
        [InlineKeyboardButton("📞 ជំនួយ / Support", callback_data='support')]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in user_balances:
        user_balances[user.id] = 0.0
    await update.message.reply_text(f"👋 សួស្តី **{user.first_name}**!\n\nសូមស្វាគមន៍មកកាន់ប្រព័ន្ធទិញ-លក់អាខោន Facebook ស្វ័យប្រវត្តិ។", parse_mode='Markdown', reply_markup=get_main_menu())

async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(f"🇰🇭 FB Via Cambodia ($1.50) [សល់: {len(stock['via_kh'])}]", callback_data='buy_via_kh')],
        [InlineKeyboardButton(f"🇺🇸 FB Via USA ($2.00) [សល់: {len(stock['via_us'])}]", callback_data='buy_via_us')],
        [InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]
    ]
    await query.edit_message_text("📦 **សូមជ្រើសរើសប្រភេទអាខោន FB ដែលចង់ទិញ:**", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

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

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.edit_message_text(f"👤 **ព័ត៌មានគណនី**\n\n🆔 Telegram ID: `{user_id}`\n💰 សមតុល្យ: **${user_balances.get(user_id, 0.0):.2f}**", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]]))

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "💳 **សូមជ្រើសរើសចំនួនទឹកប្រាក់ដែលចង់បញ្ចូល:**"
    keyboard = [
        [InlineKeyboardButton("💵 $1.00", callback_data='qr_1'), InlineKeyboardButton("💵 $2.00", callback_data='qr_2')],
        [InlineKeyboardButton("💵 $5.00", callback_data='qr_5'), InlineKeyboardButton("💵 $10.00", callback_data='qr_10')],
        [InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]
    ]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def generate_qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    amount = query.data.split('_')[1]
    
    # បង្កើត Link សម្រាប់ទូទាត់ผ่าน ABA
    pay_data = f"https://pay.ababank.com/pay?to={ABA_ACCOUNT_NUMBER}&amount={amount}&currency=USD"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(pay_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    caption = (
        f"📲 **ស្កេន QR Code ដើម្បីបង់ប្រាក់**\n\n"
        f"💰 ចំនួនទឹកប្រាក់: **${amount}.00 USD**\n"
        f"🏦 ឈ្មោះ: `{MERCHANT_NAME}`\n"
        f"🔢 លេខគណនី: `{ABA_ACCOUNT_NUMBER}`\n\n"
        f"⚠️ បន្ទាប់ពីទូទាត់រួច សូម **Screenshot វិក្កយបត្រ** រួចផ្ញើរូបភាពចូល Chat នេះដើម្បី Admin ពិនិត្យបញ្ជីលុយជូន។"
    )
    
    await query.message.delete()
    await context.bot.send_photo(
        chat_id=query.from_user.id,
        photo=InputFile(bio, filename="qr.png"),
        caption=caption,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='deposit')]])
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    await update.message.reply_text("⏳ វិក្កយបត្រត្រូវបានបញ្ជូនទៅ Admin ហើយ!")
    user_name = f"@{user.username}" if user.username else user.first_name
    keyboard = [
        [InlineKeyboardButton("✅ +$1", callback_data=f"app_{user.id}_1"), InlineKeyboardButton("✅ +$2", callback_data=f"app_{user.id}_2"), InlineKeyboardButton("✅ +$5", callback_data=f"app_{user.id}_5")],
        [InlineKeyboardButton("✅ +$10", callback_data=f"app_{user.id}_10"), InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")]
    ]
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id, caption=f"📥 សំណើបញ្ចូលលុយពី {user_name} (`{user.id}`)", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

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

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📞 សូមទាក់ទង Admin ផ្ទាល់។", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]]))

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🏠 សូមជ្រើសរើសមុខងារ:", reply_markup=get_main_menu())

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
    bot_app.add_handler(CallbackQueryHandler(buy_menu, pattern='^buy_menu$'))
    bot_app.add_handler(CallbackQueryHandler(buy_via_kh, pattern='^buy_via_kh$'))
    bot_app.add_handler(CallbackQueryHandler(buy_via_us, pattern='^buy_via_us$'))
    bot_app.add_handler(CallbackQueryHandler(my_profile, pattern='^my_profile$'))
    bot_app.add_handler(CallbackQueryHandler(deposit, pattern='^deposit$'))
    bot_app.add_handler(CallbackQueryHandler(generate_qr_code, pattern='^qr_'))
    bot_app.add_handler(CallbackQueryHandler(support, pattern='^support$'))
    bot_app.add_handler(CallbackQueryHandler(back_home, pattern='^back_home$'))
    bot_app.add_handler(CallbackQueryHandler(admin_actions, pattern='^(app|rej)_'))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    await run_web_server()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    
    print("🚀 Bot is running with QR Generator...")
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
