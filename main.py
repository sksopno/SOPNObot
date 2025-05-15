
# main.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import json

BOT_TOKEN = '7861108419:AAGgDqCuOcltA1Y9LA4Hd56HqNbUbbWir0A'
ADMIN_ID = 6453538686

user_data = {}
total_users = 0

def save_data():
    with open("data.json", "w") as f:
        json.dump(user_data, f)

def load_data():
    global user_data, total_users
    try:
        with open("data.json", "r") as f:
            user_data = json.load(f)
            total_users = 14646
    except:
        user_data = {}
        total_users = 14646

async def start(update: Update, context: CallbackContext):
    global total_users
    user_id = str(update.effective_user.id)
    args = context.args
    
    is_new_user = user_id not in user_data
    if is_new_user:
        user_data[user_id] = {
            "USDT": 0.02,
            "ID": user_id,
            "referrals": 0,
            "referred_by": None
        }
        total_users += 1
        
        # Handle referral
        if args and args[0] != user_id:
            referrer_id = args[0]
            if referrer_id in user_data:
                user_data[user_id]["referred_by"] = referrer_id
                user_data[referrer_id]["referrals"] += 1
                user_data[referrer_id]["USDT"] += 2.0  # Referral bonus
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎁 You received 2 USDT for referring a new user!"
                )
        
        # Notify admin about new user
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📱 New user joined!\nID: {user_id}\nTotal users: {total_users}"
        )
        
        save_data()
    
    if user_id == str(ADMIN_ID):
        keyboard = [["Add", "Remove"], ["My Wallet💰", "Stats"], ["Total Users"], ["Support"]]
        await update.message.reply_text("Welcome Admin!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    else:
        keyboard = [["My Wallet💰", "Deposit📥", "Withdrawal📤"], ["Refer & Earn", "Total Users"], ["Support"]]
        await update.message.reply_text("Welcome to SOPNO Wallet", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def wallet(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    usdt_balance = user_data.get(user_id, {}).get("USDT", 0)
    msg = f"""🧾 My Wallet

USDT: {usdt_balance:.2f} USDT
TRUMP: 0.00 TRUMP
ETH: 0.00 ETH
BNB: 0.00 BNB
NOT: 0.00 NOT
TON: 0.00 TON
SOPNO: 0.00 SOPNO

ID: `{user_id}`
≈ ${usdt_balance:.2f}

👥 Total Users: {total_users}"""
    await update.message.reply_text(msg, parse_mode="Markdown")

async def deposit(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Receive From SOPNO Wallet", callback_data='receive_sopno')],
        [InlineKeyboardButton("Crypto Deposit", callback_data='crypto_deposit')]
    ]
    await update.message.reply_text("Select deposit method:", reply_markup=InlineKeyboardMarkup(keyboard))

async def withdrawal(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Send", callback_data='send')],
        [InlineKeyboardButton("Crypto Withdrawal", callback_data='crypto')]
    ]
    await update.message.reply_text("Choose option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == 'send':
        context.user_data["stage"] = "token_select"
        token_buttons = [[InlineKeyboardButton(t, callback_data=f"token_{t}")] for t in ["USDT", "BTC", "ETH", "BNB"]]
        await query.message.reply_text("Select token:", reply_markup=InlineKeyboardMarkup(token_buttons))
    
    elif query.data == 'crypto':
        user_balance = user_data.get(user_id, {}).get("USDT", 0)
        if user_balance < 50:
            await query.message.reply_text("Minimum withdrawal amount is 50 USDT")
        else:
            await query.message.reply_text("Processing crypto withdrawal...")
            
    elif query.data == 'receive_sopno':
        await query.message.reply_text(f"Your ID: `{user_id}`\nShare this ID with the sender.", parse_mode="Markdown")
        
    elif query.data == 'crypto_deposit':
        await query.message.reply_text("⚡ Crypto deposit coming soon!")

    elif query.data.startswith("token_"):
        token = query.data.split("_")[1]
        context.user_data["token"] = token
        context.user_data["stage"] = "receiver_id"
        await query.message.reply_text("Enter receiver Chat ID:")

async def message_handler(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if user_id == str(ADMIN_ID):
        if text == "Add":
            context.user_data["admin_action"] = "add"
            await update.message.reply_text("Enter user ID to add USDT:")
            return
        elif text == "Remove":
            context.user_data["admin_action"] = "remove"
            await update.message.reply_text("Enter user ID to remove USDT:")
            return
        elif context.user_data.get("admin_action") in ["add", "remove"]:
            if "target_user" not in context.user_data:
                context.user_data["target_user"] = text
                await update.message.reply_text("Enter USDT amount:")
                return
            try:
                amount = float(text)
                target_id = context.user_data["target_user"]
                if target_id not in user_data:
                    user_data[target_id] = {"USDT": 0.0, "ID": target_id}
                
                if context.user_data["admin_action"] == "add":
                    user_data[target_id]["USDT"] += amount
                    await update.message.reply_text(f"Added {amount} USDT to user {target_id}")
                else:
                    user_data[target_id]["USDT"] = max(0, user_data[target_id]["USDT"] - amount)
                    await update.message.reply_text(f"Removed {amount} USDT from user {target_id}")
                
                save_data()
                context.user_data.clear()
                return
            except ValueError:
                await update.message.reply_text("Invalid amount. Please enter a number.")
                return

    if text == "My Wallet💰":
        await wallet(update, context)
    elif text == "Deposit📥":
        await deposit(update, context)
    elif text == "Withdrawal📤":
        await withdrawal(update, context)
    elif text == "Refer & Earn":
        refs = user_data[user_id].get("referrals", 0)
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        msg = f"🔗 Your Referral Link:\n{ref_link}\n\n👥 Total Referrals: {refs}\n\n💰 Earn 2 USDT for each referral!"
        await update.message.reply_text(msg)
    elif text == "Stats":
        if user_id == str(ADMIN_ID):
            msg = f"📊 Bot Statistics\n\n👥 Total Users: {total_users}"
            await update.message.reply_text(msg)
        else:
            msg = f"👥 Total Users in Bot: {total_users}"
            await update.message.reply_text(msg)
    elif text == "Total Users":
        msg = f"👥 Total Users in Bot: {total_users}"
        await update.message.reply_text(msg)
    elif text == "Support":
        msg = "❓ If you have any problems or need assistance, please message this account: @OwnerOf_Xion_Crypto"
        await update.message.reply_text(msg)
    elif context.user_data.get("stage") == "receiver_id":
        context.user_data["receiver_id"] = text
        context.user_data["stage"] = "amount"
        await update.message.reply_text("Enter amount:")
    elif context.user_data.get("stage") == "amount":
        try:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("Invalid amount.")
                return

            if user_data[user_id]["USDT"] < amount:
                await update.message.reply_text("Insufficient balance.")
                return

            receiver_id = context.user_data["receiver_id"]
            if receiver_id not in user_data:
                user_data[receiver_id] = {"USDT": 0.0, "ID": receiver_id}

            user_data[user_id]["USDT"] -= amount
            user_data[receiver_id]["USDT"] += amount
            save_data()

            # Show processing message
            process_msg = await update.message.reply_text("⏳ Processing transfer...")
            
            # Wait 5 seconds before showing success
            await asyncio.sleep(5)
            await process_msg.edit_text("✅ Transfer Successful!")
            
            # Send notification to receiver
            try:
                await context.bot.send_message(
                    chat_id=receiver_id,
                    text=f"✅ Successfully Received {amount} USDT from ID: {user_id}"
                )
            except:
                pass

        except:
            await update.message.reply_text("Invalid input.")

async def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Send in format:\n/add ID amount\n/remove ID amount")

async def admin_commands(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    parts = update.message.text.split()
    if len(parts) != 3:
        return
    cmd, uid, amt = parts
    try:
        amt = float(amt)
        if uid not in user_data:
            user_data[uid] = {"USDT": 0.0, "ID": uid}
        if cmd == "/add":
            user_data[uid]["USDT"] += amt
        elif cmd == "/remove":
            user_data[uid]["USDT"] -= amt
        save_data()
        await update.message.reply_text("Updated.")
    except:
        await update.message.reply_text("Error.")

def main():
    load_data()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/add|/remove"), admin_commands))
    app.add_handler(MessageHandler(filters.TEXT, message_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
