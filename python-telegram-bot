import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ដាក់ Bot Token និង Admin ID របស់អ្នក
BOT_TOKEN = '8965425942:AAHnuuR61iu5B_W31k9yIxllNdPWWt12vIE'
ADMIN_ID = 8276069267  # Telegram ID របស់អ្នក

# ABA PayWay Link
ABA_PAY_LINK = 'https://link.payway.com.kh/ABAPAYQk505904o'

# ស្តុកអាខោន Facebook (គំរូ)
stock = {
    "via_kh": [
        "100081234567890|Pass123!|2FASECRETKEY1",
        "100081234567891|Pass456!|2FASECRETKEY2"
    ],
    "via_us": [
        "100091234567892|PassUs123|2FASECRETKEY3"
    ]
}

# រក្សាទុកសមតុល្យអ្នកប្រើប្រាស់ (In-memory database)
user_balances = {}

# មុខងារបង្ហាញ Menu មេ
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 ទិញអាខោន FB", callback_data='buy_menu')],
        [InlineKeyboardButton("💳 បញ្ចូលលុយ (ABA)", callback_data='deposit'), InlineKeyboardButton("👤 គណនីខ្ញុំ", callback_data='my_profile')],
        [InlineKeyboardButton("📞 ជំនួយ / Support", callback_data='support')]
    ]
    return InlineKeyboardMarkup(keyboard)

# 1. Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in user_balances:
        user_balances[user.id] = 0.0

    welcome_text = f"👋 សួស្តី **{user.first_name}**!\n\nសូមស្វាគមន៍មកកាន់ប្រព័ន្ធទិញ-លក់អាខោន Facebook ស្វ័យប្រវត្តិ។"
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_menu())

# 2. Buy Menu
async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    kh_count = len(stock["via_kh"])
    us_count = len(stock["via_us"])

    keyboard = [
        [InlineKeyboardButton(f"🇰🇭 FB Via Cambodia ($1.50) [សល់: {kh_count}]", callback_data='buy_via_kh')],
        [InlineKeyboardButton(f"🇺🇸 FB Via USA ($2.00) [សល់: {us_count}]", callback_data='buy_via_us')],
        [InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]
    ]
    await query.edit_message_text("📦 **សូមជ្រើសរើសប្រភេទអាខោន FB ដែលចង់ទិញ:**", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# Handle Buy Action (Cambodia)
async def buy_via_kh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    price = 1.50
    balance = user_balances.get(user_id, 0.0)

    if len(stock["via_kh"]) == 0:
        await query.answer("❌ ស្តុក FB Via KH អស់ហើយ!", show_alert=True)
        return

    if balance < price:
        await query.answer(f"❌ សមតុល្យមិនគ្រប់គ្រាន់! អ្នកមាន ${balance:.2f} (តម្លៃ ${price})", show_alert=True)
        return

    user_balances[user_id] -= price
    account = stock["via_kh"].pop()

    await query.answer()
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 **ការទិញបានជោគជ័យ!**\n\n📦 ប្រភេទ: FB Via Cambodia\n📋 ទិន្នន័យ (UID|Pass|2FA):\n`{account}`\n\n⚠️ សូមប្តូរពាក្យសម្ងាត់ ឬរក្សាទុកឱ្យបានត្រឹមត្រូវ!",
        parse_mode='Markdown'
    )

# Handle Buy Action (USA)
async def buy_via_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    price = 2.00
    balance = user_balances.get(user_id, 0.0)

    if len(stock["via_us"]) == 0:
        await query.answer("❌ ស្តុក FB Via US អស់ហើយ!", show_alert=True)
        return

    if balance < price:
        await query.answer(f"❌ សមតុល្យមិនគ្រប់គ្រាន់! អ្នកមាន ${balance:.2f} (តម្លៃ ${price})", show_alert=True)
        return

    user_balances[user_id] -= price
    account = stock["via_us"].pop()

    await query.answer()
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 **ការទិញបានជោគជ័យ!**\n\n📦 ប្រភេទ: FB Via USA\n📋 ទិន្នន័យ (UID|Pass|2FA):\n`{account}`\n\n⚠️ សូមប្តូរពាក្យសម្ងាត់ ឬរក្សាទុកឱ្យបានត្រឹមត្រូវ!",
        parse_mode='Markdown'
    )

# 3. User Profile
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    balance = user_balances.get(user_id, 0.0)

    keyboard = [[InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]]
    text = f"👤 **ព័ត៌មានគណនីរបស់អ្នក**\n\n🆔 Telegram ID: `{user_id}`\n💰 សមតុល្យបច្ចុប្បន្ន: **${balance:.2f}**"
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# 4. Deposit Menu
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "💳 **ការបញ្ចូលលុយតាម ABA Bank**\n\n"
        "១. ចុចប៊ូតុង **\"📲 បើក ABA Mobile\"** ខាងក្រោមដើម្បីផ្ទេរប្រាក់\n"
        "២. វាយបញ្ចូលចំនួនទឹកប្រាក់ដែលអ្នកចង់បញ្ចូល ($1, $2, $5...)\n"
        "៣. បន្ទាប់ពីផ្ទេររួច សូម **Screenshot វិក្កយបត្រ** រួចផ្ញើរូបភាពចូល Chat នេះ។"
    )
    keyboard = [
        [InlineKeyboardButton("📲 បើក ABA Mobile / PayWay", url=ABA_PAY_LINK)],
        [InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]
    ]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# 5. Handle Screenshot from User
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1] # យករូបភាពច្បាស់បំផុត

    await update.message.reply_text("⏳ វិក្កយបត្រត្រូវបានបញ្ជូនទៅ Admin ហើយ! សូមរង់ចាំការផ្ទៀងផ្ទាត់បន្តិច...")

    user_name = f"@{user.username}" if user.username else user.first_name
    
    keyboard = [
        [
            InlineKeyboardButton("✅ +$1.00", callback_data=f"app_{user.id}_1"),
            InlineKeyboardButton("✅ +$2.00", callback_data=f"app_{user.id}_2"),
            InlineKeyboardButton("✅ +$5.00", callback_data=f"app_{user.id}_5")
        ],
        [
            InlineKeyboardButton("✅ +$10.00", callback_data=f"app_{user.id}_10"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")
        ]
    ]
    
    caption = f"📥 **សំណើបញ្ចូលលុយថ្មី!**\n\n👤 អ្នកផ្ញើ: {user_name}\n🆔 User ID: `{user.id}`"
    
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=caption,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Error sending to admin: {e}")

# 6. Admin Actions (Approve / Reject)
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    parts = data.split('_')
    action = parts[0]
    target_user_id = int(parts[1])

    if action == 'app':
        amount = float(parts[2])
        user_balances[target_user_id] = user_balances.get(target_user_id, 0.0) + amount
        
        await query.answer("បានអនុម័តជោគជ័យ!")
        await query.edit_message_caption(
            caption=f"✅ **បានអនុម័តជោគជ័យ!**\n👤 User: `{target_user_id}`\n💰 បញ្ចូល: +${amount:.2f}\n💰 Balance សរុប: ${user_balances[target_user_id]:.2f}",
            parse_mode='Markdown'
        )
        
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 **ការបញ្ចូលលុយជោគជ័យ!**\n\n✅ បានបញ្ចូល: **+${amount:.2f}**\n💰 សមតុល្យសរុប: **${user_balances[target_user_id]:.2f}**",
            parse_mode='Markdown'
        )
        
    elif action == 'rej':
        await query.answer("បានបដិសេធ!")
        await query.edit_message_caption(caption=f"❌ បានបដិសេធសំណើរបស់ User: `{target_user_id}`", parse_mode='Markdown')
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ វិក្កយបត្រមិនត្រឹមត្រូវ។ សូមទាក់ទងមក Admin ប្រសិនបើមានបញ្ហា។"
        )

# Support & Back Home
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data='back_home')]]
    await query.edit_message_text("📞 **ផ្នែកជំនួយ**\n\nសូមទាក់ទងមកកាន់ Admin ផ្ទាល់.", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🏠 សូមជ្រើសរើសមុខងារ:", reply_markup=get_main_menu())

# Main Function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_menu, pattern='^buy_menu$'))
    app.add_handler(CallbackQueryHandler(buy_via_kh, pattern='^buy_via_kh$'))
    app.add_handler(CallbackQueryHandler(buy_via_us, pattern='^buy_via_us$'))
    app.add_handler(CallbackQueryHandler(my_profile, pattern='^my_profile$'))
    app.add_handler(CallbackQueryHandler(deposit, pattern='^deposit$'))
    app.add_handler(CallbackQueryHandler(support, pattern='^support$'))
    app.add_handler(CallbackQueryHandler(back_home, pattern='^back_home$'))
    
    # Handle Admin Approve / Reject Callback
    app.add_handler(CallbackQueryHandler(admin_actions, pattern='^(app|rej)_'))
    
    # Handle Photo (User sending payment slip)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 Python Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
