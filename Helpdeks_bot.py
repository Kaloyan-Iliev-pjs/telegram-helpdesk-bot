import telegram
from telegram.ext import filters,ApplicationBuilder, MessageHandler
import re

#Awakes the bot, and keeps it running
bot_key = open("key_bot.txt").read()

app = ApplicationBuilder().token(bot_key).build()
bot = telegram.Bot(bot_key)

#admin user info - used to notify me, when someone asks the bot for assistance from operator
admin_user = open("admin_user.txt").read()

# device_types, extract_user_info - currently not used, they are for future upgrades.
# I want to connect a DB with users  and devices that the bot will work with.
device_types = {
        "lp" : "Laptop",
        "pc" : "Computer",
        "pt" : "Printer",
        "pj" : "Projector",
        "ni" : "Неизвестен тип"
    }

#mainly for future use, for now it gives info in the terminal incase an operator needs it when connecting to the chat
def extract_user_info(message):
    user = message.from_user.first_name, message.from_user.last_name, message.from_user.id
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    user_id = message.from_user.id

    return user, user_first_name, user_last_name, user_id

#For future needs - longer answers and more specific problems with specific devices that cause less seen problems
def extract_device_info(text:str):
    pattern = r"\b(pj|pt|pc|lp)\d{4}\b"
    matches = list(re.finditer(pattern, text))
    devices = []
    for m in matches:
        prefix = m.group(1)  # lp / pj / ...
        code = m.group(0)  # lp1001
        devices.append({
            "prefix": prefix,
            "code": code,
            "type_name": device_types.get(prefix, "Неизвестен тип")
        })

    return devices

#Main function, responsible for messages reading and sending
async def handle_message(update, context):

    #separetes message part from the whole update
    msg = update.message
    print(msg)

    #user info mostly for future use, user_id is used for now, and lists with keyword for easier use
    user, user_first_name, user_last_name, user_id = extract_user_info(msg)
    help_words = ["помощ", "съдействие", "не работи"]
    device_prefixes = ["pj", "pt", "pc", "lp"]

    if not msg or not msg.text:
        return

    # extracts user id, chat type, text from message, sets user chat state
    user_text = msg.text.lower()
    state = context.user_data.get("state", "idle")
    chat = msg.chat

    #defines what messages will be sent if they meet certain criteria is met
    # if - for group chats and user - bot conversation start
    # else for continuing started conversation and operator connection/notification
    if chat.type in ("group", "supergroup")\
            and any(word in user_text for word in help_words)\
            and any(pref in user_text for pref in device_prefixes)\
            and state == "idle":

        device_info = extract_device_info(user_text)

        #device_info is printed in the console in case the operator needs it when taking over the chat
        print(device_info)

        #notifies in the group chat that he will help the user and sends message to the user to get more info about the problem
        await msg.reply_text("Здравейте, заемаме се с казуса :)")
        await bot.send_message(user_id, "С какво можем да бъдем полези?\n"
                                            "- Проблем с принтер\n"
                                            "- Проблем с Проектор\n"
                                            "- Проблем със звука\n"
                                            "- Проблем с Интернет\n"
                                            "- Връзка с оператор")
        context.user_data["state"] = "waiting_issue"
        return

    else:
        #reading the basic instruction that will be sent to the user depending on his problem
        printer_solve = open("printer.txt", "r", encoding="utf-8").read()
        internet_solve = open("no_internet.txt", "r", encoding="utf-8").read()
        projector_solve = open("projector.txt", "r", encoding="utf-8").read()
        sound_solve = open("sound.txt", "r", encoding="utf-8").read()

        #sends simple instruction and if needed notifies operator to take over the chat.
        #the first if checks the user status and chat type, so it can write to open cases in private messages
        if chat.type == "private" and state == "waiting_issue":
            if "принтер" in user_text:
                await bot.send_message(user_id, printer_solve)
                await bot.send_message(user_id, text = "Ако проблема е разрешен след изпълняване на стъпките моля напишете 'готово' в чата :)")
            elif "интернет" in user_text or "интернета" in user_text:
                await bot.send_message(user_id, internet_solve)
                await bot.send_message(user_id,text="Ако проблема е разрешен след изпълняване на стъпките моля напишете 'готово' в чата :)")
            elif "проектор" in user_text:
                await bot.send_message(user_id, projector_solve)
                await bot.send_message(user_id, text="Ако проблема е разрешен след изпълняване на стъпките моля напишете 'готово' в чата :)")
            elif "звук" in user_text:
                await bot.send_message(user_id, sound_solve)
                await bot.send_message(user_id,text="Ако проблема е разрешен след изпълняване на стъпките моля напишете 'готово' в чата :)")
            elif "готово" in user_text:
                context.user_data["state"] = "idle"
                await bot.send_message(user_id, text="Радваме се, че бяхме полезни :) ")
            else:
                await bot.send_message(user_id, "Оператор ще продължи чата")
                await bot.send_message(chat_id=admin_user, text="Проблем")
                while True:
                    op_user_text = input("> ")
                    if op_user_text == "done":
                        context.user_data["state"] = "idle"
                        await bot.send_message(user_id, text="Радваме се, че бяхме полезни :) ")
                        return
                    await bot.send_message(chat_id=user_id, text=op_user_text)

app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()