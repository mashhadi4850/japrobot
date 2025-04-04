from enum import Enum
import json
import random
import string
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, Account
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ApplicationBuilder
from database import user_list, load_user_list, save_user_list, print_user_list, get_top_users, get_user, add_user, init_db
# متغیرهای محیطی
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
ROBOT_WALLET_ADDRESS = os.getenv("ROBOT_WALLET_ADDRESS")
ROBOT_SECRET_KEY = os.getenv("ROBOT_SECRET_KEY")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
TRANSLATIONS_DIR = "C:/Users/parsinr/pyproject/jap_project/translations"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TESTMOCK_PATH = os.path.join(BASE_DIR, "testmock.json")
STELLAR_SERVER = "https://horizon.stellar.org"

# متغیرهای جهانی
user_data = {}
user_list = []
translations = {}
admin_id = "7214394954"

# تابع برای بارگذاری فایل‌های ترجمه


def load_translations():
    languages = ["en", "fa"]
    for lang in languages:
        try:
            file_path = os.path.join(TRANSLATIONS_DIR, f"{lang}.txt")
            with open(file_path, "r", encoding="utf-8") as f:
                translations[lang] = {}
                for line in f:
                    key, value = line.strip().split("=", 1)
                    value = value.replace("\\n", "\n")
                    translations[lang][key] = value
        except FileNotFoundError:
            print(
                f"[ERROR] Translation file '{lang}.txt' not found in {TRANSLATIONS_DIR}. Please create it.")
            translations[lang] = {}
        except Exception as e:
            print(f"[ERROR] Failed to load translation file '{lang}.txt': {e}")
            translations[lang] = {}
# تابع برای دریافت ترجمه‌ها


def get_translation(user_id, key):
    lang = user_data.get(user_id, {}).get("language", "en")
    lang_prefix = lang.split("_")[-1] if lang.startswith("lang_") else lang
    if lang_prefix not in translations:
        lang_prefix = "en"
    return translations[lang_prefix].get(key, key)

# تابع برای تولید کد رفرال


def generate_referral_code(length=8):
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if not any(user["referral_code"] == code for user in user_list):
            return code
# تابع برای تولید کاربران شبیه‌سازی‌شده


def generate_simulated_users(count):
    import random
    import string
    # اول داده‌های فعلی رو از دیتابیس بارگذاری کن
    load_user_list()  # این خط رو اضافه کن
    current_count = len(user_list)
    for i in range(count):
        user_id = random.randint(100000000, 999999999)
        # مطمئن شو user_id تکراری نیست
        while any(user["user_id"] == user_id for user in user_list):
            user_id = random.randint(100000000, 999999999)
        referral_code = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=8))
        # مطمئن شو referral_code تکراری نیست
        while any(user["referral_code"] == referral_code for user in user_list):
            referral_code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=8))
        user = {
            "user_id": user_id,
            "referral_code": referral_code,
            "friends_count": random.randint(0, 200),
            "stars": 0,
            "pending_rewards": 0.0,
            "payment_id": str(random.randint(1000000000, 9999999999)),
            "stellar_address": None
        }
        user["stars"] = user["friends_count"] // 50
        user_list.append(user)
        print(f"[DEBUG] Added simulated user: {user}")
    save_user_list()
# تابع برای دریافت قیمت لحظه‌ای استلار


async def get_xlm_price_in_usd():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=stellar&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            print(f"[DEBUG] Coingecko API response: {data}")
            return data["stellar"]["usd"]

# تابع برای دریافت جدول کاربران برتر


def get_top_users_table():
    top_users = get_top_users()
    table = "🏆 Top Users 🏆\n\n"
    for rank, user in enumerate(top_users, 1):
        user_id = user["user_id"]
        friends = user["friends_count"]
        stars = user["stars"]
        table += f"{rank}. User {user_id} - Friends: {friends} 👥, Stars: {stars} ⭐\n"
    return table

#def get_top_users_table():
#    table = "Rank|Ref Code|Friends|Stars|Recv\n"
#    table += "----|--------|-------|-----|----\n"
#    top_users = get_top_users(100)
#    if not top_users:
#        table += "No users available.\n"
#        return table
#    for rank, user in enumerate(top_users, start=1):
#        stars = user[3]
#        star_display = f"{stars}*" if stars > 0 else ""
#        referral_code_display = f"{user[1]}"
#        base_reward = user[2] * 0.5
#        star_bonus = 1 + (stars * 0.1)
#        total_reward = base_reward * star_bonus
#        table += f"{rank:<4}|{referral_code_display:<8}|{user[2]:<7}|{star_display:<5}|{total_reward:<4.1f}\n"
#    return table

# تابع برای دریافت ارزهای پشتیبانی‌شده


async def get_supported_currencies():
    url = "https://api.nowpayments.io/v1/currencies"
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(
                f"[DEBUG] Sending request to URL: {url} with headers: {headers}")
            response_json = await response.json()
            print(f"[DEBUG] Supported currencies response: {response_json}")
            return response_json.get("currencies", [])

# تابع برای دریافت حداقل مقدار پرداخت


async def get_minimum_amount(currency_from, currency_to="usd"):
    url = "https://api.nowpayments.io/v1/min-amount"
    params = {"currency_from": currency_from.lower(
    ), "currency_to": currency_to.lower()}
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            print(
                f"[DEBUG] Sending request to URL: {url} with params: {params} and headers: {headers}")
            response_json = await response.json()
            print(f"[DEBUG] Minimum amount response: {response_json}")
            if "min_amount" in response_json:
                return float(response_json["min_amount"])
            return None

# تابع برای تولید فاکتور پرداخت


async def create_nowpayments_invoice(user_id, price_currency, pay_currency):
    min_amount = await get_minimum_amount(pay_currency, price_currency)
    if min_amount is None:
        return {"error": "Could not fetch minimum amount for this currency."}
    amount = 2.0  # همیشه 2 دلار

    url = "https://api.nowpayments.io/v1/invoice"
    payload = {
        "price_amount": amount,
        "price_currency": price_currency,
        "pay_currency": pay_currency,
        "order_id": str(user_id),
        "order_description": f"Payment for user {user_id}",
        "ipn_callback_url": "https://your-server.com/callback",
        "success_url": "https://your-server.com/success",
        "cancel_url": "https://your-server.com/cancel"
    }
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            print(
                f"[DEBUG] Sending request to URL: {url} with payload: {payload} and headers: {headers}")
            response_json = await response.json()
            print(f"[DEBUG] NowPayments invoice response: {response_json}")
            if "invoice_url" in response_json:
                user_data[user_id]["order_id"] = str(user_id)
                user_data[user_id]["initial_payment_id"] = response_json["id"]
                return {
                    "id": response_json["id"],
                    "invoice_url": response_json["invoice_url"],
                    "min_amount": amount
                }
            return {"error": response_json.get("error", "Unknown error")}

# تابع برای تأیید پرداخت


async def verify_payment(payment_id, user_id):
    lang = user_data.get(user_id, {}).get("language", "en")
    lang_prefix = lang.split("_")[-1] if lang.startswith("lang_") else lang
    if lang_prefix not in translations:
        lang_prefix = "en"

    if TEST_MODE:
        return True, translations[lang_prefix]["payment_confirmed"]

    url = f"https://api.nowpayments.io/v1/payment/{payment_id}"
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(
                f"[DEBUG] Sending request to URL: {url} with headers: {headers}")
            response_json = await response.json()
            print(f"[DEBUG] Payment status response: {response_json}")
            if response.status == 200 and "payment_status" in response_json:
                if response_json["payment_status"] in ["finished", "confirmed"]:
                    print(
                        f"[DEBUG] Payment status for {payment_id} is {response_json['payment_status']}")
                    return True, translations[lang_prefix]["payment_confirmed"]
                elif response_json["payment_status"] == "failed" and "reason" in response_json and "insufficient" in response_json["reason"].lower():
                    print(
                        f"[DEBUG] Payment failed due to insufficient amount: {response_json}")
                    return False, translations[lang_prefix]["payment_insufficient"]
                else:
                    print(
                        f"[DEBUG] Payment status for {payment_id} is {response_json['payment_status']}")
                    return False, translations[lang_prefix]["payment_not_confirmed_yet"]
            else:
                print(f"[DEBUG] Failed to verify payment: {response_json}")
                return False, translations[lang_prefix]["payment_not_confirmed_yet"]

# تابع برای ارسال XLM


async def send_xlm(to_address, amount):
    try:
        server = Server(STELLAR_SERVER)
        source_keypair = Keypair.from_secret(ROBOT_SECRET_KEY)
        source_account = server.load_account(source_keypair.public_key)

        base_fee = await server.fetch_base_fee()
        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
                base_fee=base_fee,
            )
            .append_payment_op(
                destination=to_address,
                asset=Asset.native(),
                amount=str(amount)
            )
            .set_timeout(30)
            .build()
        )

        transaction.sign(source_keypair)
        response = await server.submit_transaction(transaction)
        print(f"[DEBUG] XLM sent to {to_address}: {response}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send XLM to {to_address}: {e}")
        return False

# تابع برای چک کردن و پرداخت پاداش‌ها


async def check_rewards(context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] Checking rewards...")
    for user in user_list:
        pending_rewards = user.get("pending_rewards", 0.0)
        if pending_rewards > 0 and user.get("stellar_address"):
            success = await send_xlm(user["stellar_address"], pending_rewards)
            if success:
                user["pending_rewards"] = 0.0
                print(
                    f"[DEBUG] Paid {pending_rewards} XLM to user {user['user_id']}")
                await context.bot.send_message(
                    user["user_id"],
                    f"You have received {pending_rewards} XLM as your referral reward!"
                )
    save_user_list()

# تابع شروع ربات


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id] = {"state": "selecting_language"}
    keyboard = [
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("Español", callback_data="lang_es")],
        [InlineKeyboardButton("العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("Deutsch", callback_data="lang_de")],
        [InlineKeyboardButton("Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("中文", callback_data="lang_zh")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose your language:", reply_markup=reply_markup)

# تابع انتخاب زبان


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data.startswith("lang_"):
        lang = query.data
        user_data[user_id]["language"] = lang
        user_data[user_id]["state"] = "accepting_terms"

        keyboard = [[InlineKeyboardButton(get_translation(
            user_id, "accept_terms"), callback_data="accept_terms")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(get_translation(user_id, "intro"), reply_markup=reply_markup)

# تابع پذیرش شرایط


async def handle_terms_acceptance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id] = {"state": UserState.WAITING_FOR_CODE.value}
    print(f"[DEBUG] Set user_data for user {user_id}: {user_data[user_id]}")
    leaderboard = get_top_users_table()
    await query.edit_message_text(
        "Terms accepted! Please enter your referral code to proceed.\n\n"
        f"{leaderboard}"
    )
# تابع ثبت‌نام بدون کد


async def register_without_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    print(
        f"[DEBUG] Handle menu selection - register_without_code for user {user_id}")
    user_data[user_id]["state"] = "selecting_currency"
    user_data[user_id]["registration_type"] = "without_code"
    popular_currencies = ["BTC", "ETH", "XLM",
                          "USDT", "TRX", "ADA", "SOL", "DOT", "LTC"]
    keyboard = [
        [InlineKeyboardButton(
            currency, callback_data=f"currency_{currency}") for currency in popular_currencies[i:i+5]]
        for i in range(0, len(popular_currencies), 5)
    ]
    keyboard.append([InlineKeyboardButton(
        "Other Currencies", callback_data="currency_other")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please select the currency for payment:", reply_markup=reply_markup)

# تابع ثبت‌نام با کد


async def register_with_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data[user_id]["state"] = "waiting_for_code"
    await query.edit_message_text("Please enter your referral code:")

# تابع انتخاب منو


async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "register_without_code":
        await register_without_code(update, context)
    elif query.data == "register_with_code":
        await register_with_code(update, context)
    elif query.data == "back_to_language":
        user_data[user_id]["state"] = "selecting_language"
        keyboard = [
            [InlineKeyboardButton("English", callback_data="lang_en")],
            [InlineKeyboardButton("فارسی", callback_data="lang_fa")],
            [InlineKeyboardButton("Español", callback_data="lang_es")],
            [InlineKeyboardButton("العربية", callback_data="lang_ar")],
            [InlineKeyboardButton("Deutsch", callback_data="lang_de")],
            [InlineKeyboardButton("Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("中文", callback_data="lang_zh")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Please choose your language:", reply_markup=reply_markup)

# تابع بازگشت به منو


async def handle_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data[user_id]["state"] = None
    keyboard = [
        [InlineKeyboardButton(get_translation(
            user_id, "register_without_code"), callback_data="register_without_code")],
        [InlineKeyboardButton(get_translation(
            user_id, "register_with_code"), callback_data="register_with_code")],
        [InlineKeyboardButton(get_translation(
            user_id, "support_button"), callback_data="support")],
        [InlineKeyboardButton(get_translation(
            user_id, "back_to_language"), callback_data="back_to_language")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(get_translation(user_id, "register_prompt"), reply_markup=reply_markup)

# تابع انتخاب ارز


async def handle_currency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    currency = query.data.replace("currency_", "")
    print(f"[DEBUG] User {user_id} selected currency: {currency}")

    if currency == "other":
        await query.edit_message_text("Please enter the currency code (e.g., HMSTR):")
        user_data[user_id]["state"] = "awaiting_currency_code"
        return

    user_data[user_id]["currency"] = currency
    payment_url = await create_payment(user_id, currency)
    if payment_url:
        user_data[user_id]["state"] = UserState.AWAITING_PAYMENT.value
        print(
            f"[DEBUG] Updated user_data for user {user_id}: {user_data[user_id]}")
        await query.edit_message_text(
            f"Please complete the payment using the following link:\n{payment_url}\n\n"
            "After payment, enter the Payment ID provided by NowPayments."
        )
    else:
        await query.edit_message_text("Failed to create payment. Please try again.")
# تابع مدیریت ثبت‌نام


async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data in ["register_without_code", "register_with_code"]:
        await handle_menu_selection(update, context)

# تابع مدیریت پیام‌ها


class UserState(Enum):
    NONE = "none"
    WAITING_FOR_CODE = "waiting_for_code"
    SELECTING_CURRENCY = "selecting_currency"
    AWAITING_PAYMENT = "awaiting_payment"
    AWAITING_STELLAR_ADDRESS = "awaiting_stellar_address"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    user_state = user_data.get(user_id, {}).get("state", UserState.NONE.value)
    print(
        f"[DEBUG] Handle message - user_id: {user_id}, message_text: {message_text}, user_state: {user_state}")

    if user_state == UserState.WAITING_FOR_CODE.value:
        print("[DEBUG] In waiting_for_code state, checking referral code")
        referral_code = message_text
        if any(user["referral_code"] == referral_code for user in user_list):
            user_data[user_id]["used_referral_code"] = referral_code
            user_data[user_id]["state"] = UserState.SELECTING_CURRENCY.value
            print(
                f"[DEBUG] Updated user_data for user {user_id}: {user_data[user_id]}")
            popular_currencies = ["BTC", "ETH", "XLM",
                                  "USDT", "TRX", "ADA", "SOL", "DOT", "LTC"]
            keyboard = [
                [InlineKeyboardButton(
                    currency, callback_data=f"currency_{currency}") for currency in popular_currencies[i:i+5]]
                for i in range(0, len(popular_currencies), 5)
            ]
            keyboard.append([InlineKeyboardButton(
                "Other Currencies", callback_data="currency_other")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Please select the currency for payment:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Invalid referral code. Please try again.")
        return

    if user_state == UserState.AWAITING_PAYMENT.value:
        payment_id = message_text.strip()
        if not payment_id.isdigit():
            await update.message.reply_text("Payment ID must be a number. Please try again.")
            return
        user_data[user_id]["payment_id"] = payment_id
        is_valid, message = await verify_payment(payment_id)
        if is_valid:
            user = get_user(user_id)
            if user:
                user["payment_id"] = payment_id
                save_user_list()
            user_data[user_id]["state"] = UserState.NONE.value
            print(
                f"[DEBUG] Updated user_data for user {user_id}: {user_data[user_id]}")
            await update.message.reply_text(
                f"{message}\n\nYou have successfully completed the payment process!"
            )
        else:
            await update.message.reply_text(message)
        return

    if user_state == UserState.AWAITING_STELLAR_ADDRESS.value:
        stellar_address = message_text.strip()
        user_data[user_id]["stellar_address"] = stellar_address
        user = get_user(user_id)
        if user:
            user["stellar_address"] = stellar_address
            save_user_list()
        user_data[user_id]["state"] = UserState.NONE.value
        print(
            f"[DEBUG] Updated user_data for user {user_id}: {user_data[user_id]}")
        await update.message.reply_text("Stellar address saved successfully!")
        return

    await update.message.reply_text("Please use the menu to proceed.")
# تابع پشتیبانی


async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "support":
        user_data[user_id]["state"] = "support_chat"
        await query.edit_message_text(get_translation(user_id, "support_initial_message"))

# تابع اصلی


def main():
    if not TELEGRAM_TOKEN:
        print("[ERROR] TELEGRAM_TOKEN is not set. Please set it in the .env file.")
        return
    if not NOWPAYMENTS_API_KEY:
        print("[ERROR] NOWPAYMENTS_API_KEY is not set. Please set it in the .env file.")
        return
    if not ROBOT_SECRET_KEY:
        print("[ERROR] ROBOT_SECRET_KEY is not set. Please set it in the .env file.")
        return
    init_db()
    load_translations()
    load_user_list()
#    print_user_list()  # اضافه کردن این خط
    if len(user_list) < 1000:
        generate_simulated_users(1000 - len(user_list))
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(
        handle_currency_selection, pattern="^currency_"))
    app.add_handler(CallbackQueryHandler(handle_menu_selection,
                    pattern="^(register_without_code|register_with_code|back_to_language)$"))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(
        handle_terms_acceptance, pattern="^accept_terms$"))
    app.add_handler(CallbackQueryHandler(handle_support, pattern="^support$"))
    app.add_handler(CallbackQueryHandler(handle_registration,
                    pattern="^(register_without_code|register_with_code)$"))
    app.add_handler(CallbackQueryHandler(
        handle_back_to_menu, pattern="^back_to_menu$"))
    app.job_queue.run_repeating(check_rewards, interval=60)
    print("[DEBUG] Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
