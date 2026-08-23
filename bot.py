import os
import asyncio
import io
import aiohttp
import qrcode
from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

BOT_TOKEN = '8965425942:AAHnuuR61iu5B_W31k9yIxllNdPWWt12vIE'
ADMIN_ID = 8384547912

# ព័ត៌មាន ABA KHQR
BAKONG_ACCOUNT = 'chathea_noch@abab'
MERCHANT_NAME = 'CHATHEA NOCH'
MERCHANT_CITY = 'Phnom Penh'

stock = {
    "via_kh": ["100081234567890|Pass123!|2FASECRETKEY1"],
    "via_us": ["100091234567892|PassUs123|2FASECRETKEY3"]
}

user_balances = {}
all_users = set()
admin_state = {}
user_state = {}

async def check_fb_uid_status(uid: str) -> bool:
    clean_uid = uid.strip().split('|')[0].split(':')[0]
    url = f"https://graph.facebook.com/{clean_uid}/picture?type=normal"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=False, timeout=5) as response:
                if response.status == 302:
                    location = response.headers.get('Location', '')
                    if 'static.xx.fbcdn.net' not in location:
                        return True
                elif response.status == 200:
                    return True
                return False
    except Exception:
        return False

def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for byte in data.encode('utf-8'):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def generate_khqr_string(account_id: str, name: str, city: str, amount: float = None, currency: str = "USD") -> str:
    def format_tag(tag: str, val: str) -> str:
        return f"{tag}{len(val):02d}{val}"

    sub_acc = format_tag("00", account_id)
    tag_29 = format_tag("29", sub_acc)
    payload = (
        format_tag("00", "01") +
        format_tag("01", "12" if amount else "11") +
        tag_29 +
        format_tag("52", "0000") +
        format_tag("53", "840" if currency == "USD" else "116")
    )
    if amount:
        payload += format_tag("54", f"{amount:.2f}")
    payload += (
        format_tag("58", "KH") +
        format_tag("59", name[:25]) +
        format_tag("60", city[:15]) +
        "6304"
    )
    return payload + crc16_ccitt(payload)

# Menu សម្រាប់ភ្ញៀវទូទៅ (គ្មានប៊ូតុង Admin Panel ទេ)
def get_user_keyboard():
    buttons = [
        [KeyboardButton("🛒 ទិញអាខោន FB"), KeyboardButton("💳 បញ្ចូលលុយ (ស្កេន QR)")],
        [KeyboardButton("🔍 ឆែក Live/Die FB"), KeyboardButton("👤 គណនីខ្ញុំ")],
        [KeyboardButton("📞 ជំនួយ / Support")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_users.add(user.id)
    if user.id not in user_balances:
        user_balances[user.id] = 0.0
    await update.message.reply_text(
        f"👋 សួស្តី **{user.first_name}**!\n\nសូមស្វាគមន៍មកកាន់ប្រព័ន្ធទិញ-លក់ និង Check អាខោន Facebook ស្វ័យប្រវត្តិ។",
        parse_mode='Markdown',
        reply_markup=get_user_keyboard()
    )

# បើក Admin Panel តាមរយៈការវាយពាក្យសម្ងាត់ /admin (សម្រាប់តែ Admin ID)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("👥 ចំនួនភ្ញៀវប្រើប្រាស់", callback_data='adm_users'), InlineKeyboardButton("📦 ឆែកមើលស្តុក", callback_data='adm_stock')],
        [InlineKeyboardButton("➕ ដាក់ស្តុក FB KH", callback_data='adm_add_kh'), InlineKeyboardButton("➕ ដាក់ស្តុក FB US", callback_data='adm_add_us')],
        [InlineKeyboardButton("💵 បញ្ចូលលុយឱ្យ User", callback_data='adm_manual_deposit'), InlineKeyboardButton("🔍 ឆែកសម្អាតស្តុក (Auto Filter)", callback_data='adm_clean_stock')]
    ]
    await update.message.reply_text("👑 **ផ្ទាំងគ្រប់គ្រង ADMIN (Control Panel)**", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        return await query.answer("❌ អ្នកមិនមែនជា Admin ទេ!", show_alert=True)
    await query.answer()

    data = query.data
    if data == 'adm_users':
        total = len(all_users)
        msg = f"👥 **ស្ថិតិអ្នកប្រើប្រាស់:**\n\nចំនួនភ្ញៀវសរុប: **{total} នាក់**\n"
        for uid in list(all_users)[:10]:
            msg += f"• ID `{uid}` : ${user_balances.get(uid, 0.0):.2f}\n"
        await query.edit_message_text(msg, parse_mode='Markdown')
    elif data == 'adm_stock':
        msg = (
            f"📦 **ទិន្នន័យស្តុកបច្ចុប្បន្ន:**\n\n"
            f"🇰🇭 FB Via Cambodia: **{len(stock['via_kh'])}** អាខោន\n"
            f"🇺🇸 FB Via USA: **{len(stock['via_us'])}** អាខោន"
        )
        await query.edit_message_text(msg, parse_mode='Markdown')
    elif data == 'adm_clean_stock':
        await query.edit_message_text("⏳ កំពុងដំណើរការ Check និង Filter អាខោន Die ចេញពីស្តុក...")
        live_kh = [acc for acc in stock['via_kh'] if await check_fb_uid_status(acc)]
        live_us = [acc for acc in stock['via_us'] if await check_fb_uid_status(acc)]
        stock['via_kh'] = live_kh
        stock['via_us'] = live_us
        await query.message.reply_text(f"✅ **សម្អាតស្តុករួចរាល់!**\n\n🇰🇭 KH Live សល់: {len(live_kh)}\n🇺🇸 US Live សល់: {len(live_us)}")
    elif data == 'adm_add_kh':
        admin_state[ADMIN_ID] = 'WAIT_STOCK_KH'
        await query.edit_message_text("✍️ សូមផ្ញើទិន្នន័យអាខោន **FB KH** ចូល Chat នេះ (ទម្រង់ UID|Pass|2FA):")
    elif data == 'adm_add_us':
        admin_state[ADMIN_ID] = 'WAIT_STOCK_US'
        await query.edit_message_text("✍️ សូមផ្ញើទិន្នន័យអាខោន **FB US** ចូល Chat នេះ (ទម្រង់ UID|Pass|2FA):")
    elif data == 'adm_manual_deposit':
        admin_state[ADMIN_ID] = 'WAIT_DEPOSIT_FORMAT'
        await query.edit_message_text("✍️ សូមវាយតាមទម្រង់:\n`ID ចំនួនលុយ`\n\nឧទាហរណ៍៖ `8276069267 5`", parse_mode='Markdown')

async def show_buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"🇰🇭 FB Via Cambodia ($1.50) [សល់: {len(stock['via_kh'])}]", callback_data='buy_via_kh')],
        [InlineKeyboardButton(f"🇺🇸 FB Via USA ($2.00) [សល់: {len(stock['via_us'])}]", callback_data='buy_via_us')]
    ]
    await update.message.reply_text("📦 **សូមជ្រើសរើសប្រភេទអាខោន FB ដែលចង់ទិញ:**", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def show_deposit_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    khqr_data = generate_khqr_string(BAKONG_ACCOUNT, MERCHANT_NAME, MERCHANT_CITY)
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(khqr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    caption = (
        "📲 **ស្កេន KHQR ដើម្បីបង់ប្រាក់តាម ABA Mobile**\n\n"
        f"👤 ឈ្មោះ: `{MERCHANT_NAME}`\n"
        f"🏦 គណនី: `019 088 273 / 019 088 270`\n\n"
        "⚠️ **ចំណាំ:** សូមផ្ទេរទឹកប្រាក់តាមតម្លៃដែលចង់បញ្ចូល រួច **Screenshot វិក្កយបត្រ** ផ្ញើចូល Chat នេះដើម្បី Admin បញ្ចូលលុយជូន។"
    )
    await update.message.reply_photo(photo=InputFile(bio, filename="khqr.png"), caption=caption, parse_mode='Markdown')

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"👤 **ព័ត៌មានគណនី**\n\n🆔 Telegram ID: `{user_id}`\n💰 សមតុល្យ: **${user_balances.get(user_id, 0.0):.2f}**", parse_mode='Markdown')

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 **ផ្នែកបម្រើអតិថិជន:**\nសូមទាក់ទង Admin ផ្ទាល់ សម្រាប់ការសាកសួរព័ត៌មានបន្ថែម។")

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

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    all_users.add(user_id)

    if text == "🛒 ទិញអាខោន FB":
        return await show_buy_menu(update, context)
    elif text == "💳 បញ្ចូលលុយ (ស្កេន QR)":
        return await show_deposit_qr(update, context)
    elif text == "👤 គណនីខ្ញុំ":
        return await show_profile(update, context)
    elif text == "📞 ជំនួយ / Support":
        return await show_support(update, context)
    elif text == "🔍 ឆែក Live/Die FB":
        user_state[user_id] = 'WAIT_CHECK_UID'
        return await update.message.reply_text("✍️ សូមផ្ញើ **UID** ឬបញ្ជីអាខោន FB ដែលចង់ Check ចូល Chat នេះ (អាចដាក់ម្ដងច្រើនបន្ទាត់):")

    # មុខងារ Check Live / Die UID
    if user_id in user_state and user_state[user_id] == 'WAIT_CHECK_UID':
        del user_state[user_id]
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        await update.message.reply_text(f"⏳ កំពុងដំណើរការ Check UID ចំនួន {len(lines)}...")
        
        live_list, die_list = [], []
        for line in lines:
            clean_uid = line.split('|')[0].split(':')[0].strip()
            if await check_fb_uid_status(clean_uid):
                live_list.append(clean_uid)
            else:
                die_list.append(clean_uid)
                
        result_msg = (
            f"📊 **លទ្ធផលពិនិត្យ UID:**\n\n"
            f"🟢 **LIVE ({len(live_list)}):**\n" + ("\n".join([f"`{u}`" for u in live_list[:15]]) if live_list else "គ្មាន") + "\n\n"
            f"🔴 **DIE ({len(die_list)}):**\n" + ("\n".join([f"`{u}`" for u in die_list[:15]]) if die_list else "គ្មាន")
        )
        return await update.message.reply_text(result_msg, parse_mode='Markdown')

    # Admin State (Add stock, Deposit)
    if user_id == ADMIN_ID and ADMIN_ID in admin_state:
        state = admin_state.pop(ADMIN_ID)
        if state == 'WAIT_STOCK_KH':
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            stock['via_kh'].extend(lines)
            await update.message.reply_text(f"✅ បានបន្ថែមអាខោន FB KH ចំនួន **{len(lines)}** ចូលស្តុកជោគជ័យ! (សល់សរុប: {len(stock['via_kh'])})")
        elif state == 'WAIT_STOCK_US':
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            stock['via_us'].extend(lines)
            await update.message.reply_text(f"✅ បានបន្ថែមអាខោន FB US ចំនួន **{len(lines)}** ចូលស្តុកជោគជ័យ! (សល់សរុប: {len(stock['via_us'])})")
        elif state == 'WAIT_DEPOSIT_FORMAT':
            try:
                parts = text.split()
                target_uid = int(parts[0])
                amount = float(parts[1])
                user_balances[target_uid] = user_balances.get(target_uid, 0.0) + amount
                await update.message.reply_text(f"✅ បានបញ្ចូលលុយ **+${amount:.2f}** ជូន User ID `{target_uid}` ជោគជ័យ!\nសមតុល្យបច្ចុប្បន្ន: **${user_balances[target_uid]:.2f}**", parse_mode='Markdown')
                await context.bot.send_message(chat_id=target_uid, text=f"🎉 Admin បានបញ្ចូលលុយជូនអ្នកចំនួន **+${amount:.2f}**!", parse_mode='Markdown')
            except Exception:
                await update.message.reply_text("❌ ទម្រង់មិនត្រឹមត្រូវ! សូមវាយឧទាហរណ៍៖ `8276069267 5`", parse_mode='Markdown')

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
    bot_app.add_handler(CommandHandler("admin", admin_command))  # បញ្ជាសម្ងាត់ /admin
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    bot_app.add_handler(CallbackQueryHandler(handle_admin_callbacks, pattern='^adm_'))
    bot_app.add_handler(CallbackQueryHandler(buy_via_kh, pattern='^buy_via_kh$'))
    bot_app.add_handler(CallbackQueryHandler(buy_via_us, pattern='^buy_via_us$'))
    bot_app.add_handler(CallbackQueryHandler(admin_actions, pattern='^(app|rej)_'))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    await run_web_server()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    
    print("🚀 Bot is running with Hidden Admin Panel...")
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
