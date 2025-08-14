import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from binance.client import Client

# ---------------- Config Vars ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")  # placeholder
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")  # placeholder

# ---------------- Binance Client ----------------
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)

# ---------------- Products ----------------
PRODUCTS_FILE = "products.json"
try:
    with open(PRODUCTS_FILE) as f:
        PRODUCTS = json.load(f)
except:
    PRODUCTS = {}

# ---------------- Orders ----------------
ORDERS_FILE = "orders.json"
try:
    with open(ORDERS_FILE) as f:
        ORDERS = json.load(f)
except:
    ORDERS = {}

# ---------------- Helper Functions ----------------
def save_products():
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(PRODUCTS, f)

def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(ORDERS, f)

def send_product(context: CallbackContext, order_id):
    order = ORDERS[order_id]
    user_id = order['user_id']
    product_name = order['product']
    content = PRODUCTS[product_name]['content']
    context.bot.send_message(chat_id=user_id, text=f"✅ Payment confirmed! Here is your product:\n{content}")

def reduce_stock(order_id):
    order = ORDERS[order_id]
    product_name = order['product']
    qty = order['quantity']
    PRODUCTS[product_name]['quantity'] -= qty
    save_products()

def notify_admin(context: CallbackContext, order_id):
    order = ORDERS[order_id]
    text = f"💰 New Order:\nUser: @{order['user_name']}\nProduct: {order['product']}\nQuantity: {order['quantity']}\nAmount: ${order['total']}"
    context.bot.send_message(chat_id=ADMIN_ID, text=text)

# ---------------- Admin Commands ----------------
def addproduct(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        name = context.args[0]
        price = float(context.args[1])
        quantity = int(context.args[2])
        content = " ".join(context.args[3:])
        PRODUCTS[name] = {"price": price, "quantity": quantity, "content": content}
        save_products()
        update.message.reply_text(f"✅ Product {name} added!")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

def addstock(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        name = context.args[0]
        qty = int(context.args[1])
        PRODUCTS[name]['quantity'] += qty
        save_products()
        update.message.reply_text(f"✅ Stock updated for {name}.")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

def setprice(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        name = context.args[0]
        price = float(context.args[1])
        PRODUCTS[name]['price'] = price
        save_products()
        update.message.reply_text(f"✅ Price updated for {name}.")
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

def stock(update: Update, context: CallbackContext):
    msg = "\n".join([f"{p} | ${v['price']} | {v['quantity']}" for p,v in PRODUCTS.items()])
    update.message.reply_text(msg)

# ---------------- User Commands ----------------
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Buy", callback_data='buy')],
        [InlineKeyboardButton("Support", callback_data='support')],
        [InlineKeyboardButton("Availability", callback_data='availability')],
        [InlineKeyboardButton("Terms", callback_data='terms')]
    ]
    update.message.reply_text("Welcome to the store!", reply_markup=InlineKeyboardMarkup(keyboard))

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == "support":
        query.edit_message_text("Contact admin: @stein_black")
    elif query.data == "availability":
        msg = "\n".join([f"{p}: {v['quantity']} available" for p,v in PRODUCTS.items()])
        query.edit_message_text(msg)
    elif query.data == "terms":
        query.edit_message_text("⚠️ Store Rules...\nFollow safely, enjoy your purchase!")

# ---------------- Payment Checking ----------------
def check_payments(context: CallbackContext):
    deposits = client.get_deposit_history()  # Binance deposit history
    for dep in deposits:
        tx_id = dep['txId']
        coin = dep['coin']
        amount = float(dep['amount'])
        # match to orders
        for order_id, order in ORDERS.items():
            if order['processed']:
                continue
            if amount >= order['total'] and order['tx_id'] == tx_id:
                send_product(context, order_id)
                reduce_stock(order_id)
                notify_admin(context, order_id)
                ORDERS[order_id]['processed'] = True
                save_orders()

# ---------------- Main ----------------
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addproduct", addproduct))
    dp.add_handler(CommandHandler("addstock", addstock))
    dp.add_handler(CommandHandler("setprice", setprice))
    dp.add_handler(CommandHandler("stock", stock))
    dp.add_handler(CallbackQueryHandler(button_callback))

    # Check payments every 30 seconds
    job_queue = updater.job_queue
    job_queue.run_repeating(check_payments, interval=30, first=10)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
