import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import random
import secrets
import string
import aiohttp
import datetime
import re
import io
import os
import time
import requests
from lxml import etree
from aiogram.types import User
TOKEN = '' # your bot token
bot_id = '' #BOT name
channel_id = '' #you channel username
adminstartr = [] #you are telegram_id
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

def filter_dangerous_chars(text):
    if text is None:
        return ''
    dangerous_chars = {'<', '>', '&', '"', '\''}
    for char in text:
        if char in dangerous_chars:
            text = text.replace(char, '')
    return text


def generate_promo_id():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))

def data_dict(my_dict):
    dictionary = ''
    for key, value in my_dict.items():
        dictionary += f"{key}:{value}\n"
    return dictionary

async def getqqinfo(qq):
    url = f'https://zy.xywlapi.cc/qqcx2023?qq={qq}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data_dict(data)
            else:
                return 'DPROP'

def filter_alphanumeric_regex(input_string):
    regex = r"[^a-zA-Z0-9/]"
    filtered_string = re.sub(regex, "", input_string)
    return filtered_string
conn = sqlite3.connect("promote_users.db")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        promo_id INTEGER UNIQUE,
        free_chances INTEGER DEFAULT 1,
        daily_chances INTEGER DEFAULT 0,
        last_check_in INTEGER DEFAULT 0,
        first_name TEXT,
        last_name TEXT
    )
""")
conn.commit()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = message.from_user
    user_text = message.text
    record_user_info(user, user_text)
    cur.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cur.fetchone()
    if user:
        await message.reply("You have already registered. Use /my or /help to see your chances.")
        return
    referrer_id = filter_alphanumeric_regex(message.get_args())
    if len(referrer_id) >= 9:
        print('Dangerous user: ' + str(message.from_user.id) + ' Dangerous character: ' + message.text)
        return
    if referrer_id:
        cur.execute("SELECT * FROM users WHERE promo_id=?", (referrer_id,))
        referrer = cur.fetchone()
        if not referrer:
            await message.reply("Invalid referral code. Please try again.")
            return
        elif referrer[0] == message.from_user.id:
            await message.reply("You cannot use your own referral code. Please enter a valid referral code or leave it blank.")
            return
        else:
            cur.execute("UPDATE users SET free_chances=free_chances+10 WHERE user_id=?", (referrer[0],))
            conn.commit()
    first_name = filter_dangerous_chars(message.from_user.first_name)
    last_name = filter_dangerous_chars(message.from_user.last_name)
    promo_id = generate_promo_id()
    cur.execute("INSERT INTO users (user_id, promo_id, first_name, last_name) VALUES (?, ?, ?, ?)", (message.from_user.id, promo_id, first_name, last_name))
    cur.execute("UPDATE users SET free_chances=free_chances+20 WHERE user_id=?", (message.from_user.id,))
    conn.commit()
    if referrer_id:
        await message.reply(f"Welcome to the game! You have been referred by {referrer[2]}. Your referral code is {promo_id}. You have 1 extra chance to play.")
    else:
        await message.reply(f"Welcome to the game! Your referral code is {promo_id}.")  

@dp.message_handler(commands=["checkin"])
async def daily_check_in(message: types.Message):
    cur.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cur.fetchone()
    if not user:
        await message.reply("You have not registered. Please use /start to register.")
        return
    last_check_in = user[4]
    if last_check_in == 0:
        last_check_in = datetime.datetime(2000, 1, 1)
    else:
        last_check_in = datetime.datetime.strptime(str(last_check_in), "%Y-%m-%d %H:%M:%S")
    current_time = datetime.datetime.now().timestamp()
    if last_check_in.date() == datetime.datetime.fromtimestamp(current_time).date():
        await message.reply("You have already checked in today.")
        return
    cur.execute("UPDATE users SET daily_chances=daily_chances+1, last_check_in=? WHERE user_id=?", (datetime.datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id))
    conn.commit()
    await message.reply("You have received three free chances for today.")

@dp.message_handler(commands=["help"])
async def show_help_message(message: types.Message):
    help_text = "Here are the available commands:\n\n"
    help_text = "/about me\n"
    help_text += "/start <promo_id> - Register with a promo ID (optional)\n"
    help_text += "/checkin - Check in to get a chance\n"
    help_text += "/promo - Promote the bot\n"
    help_text += "/my - Show your information\n"
    help_text += "/qq - Check if your information has been leaked\n"
    help_text += "/help - Show this help message\n\n"
    help_text += "To use the /start command, enter the command followed by the promo ID (if any). For example: /start ABC123\n"
    help_text += "To use the /checkin command, enter the command. You can only check in once a day.\n"
    help_text += "To use the /promo command, enter the command. This will promote the bot and give you free chances.\n"
    help_text += "To use the /my command, enter the command. This will show your user ID, promo ID, free chances, daily chances, and last check-in time.\n"
    help_text += "To use the /qq command, enter the command followed by your QQ number. For example: /qq 10001\n"
    help_text += "To use the /help command, enter the command. This will show this help message.\n"
    help_text += "My game channel @daowenjin771"
    await message.reply(help_text)
    
@dp.message_handler(commands=["my"])
async def show_user_info(message: types.Message):
    cur.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cur.fetchone()
    if not user:
        await message.reply("You have not registered. Please use /start to register.")
        return
    if user[1]:
        cur.execute("SELECT user_id, first_name, last_name, free_chances FROM users WHERE promo_id=?", (user[1],))
        referrer = cur.fetchone()
        if referrer:
            referrer_name = f"{referrer[1]} {referrer[2]}"
            referrer_chances = referrer[3]
        else:
            referrer_name = "Unknown"
            referrer_chances = 0
    else:
        referrer_name = "None"
        referrer_chances = 0
    msg = f"User ID: {user[0]}\nPromo ID: {user[1]}\nReferrer: {referrer_name}\nReferrer's Free Chances: {referrer_chances}\nFree Chances: {user[2]}\nDaily Chances: {user[3]}\nLast Check-in: {user[4]}"
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)
    
@dp.message_handler(commands=["promo"])
async def promo_button(message: types.Message):
    global bot_id
    user_id = message.from_user.id
    cur.execute("SELECT promo_id FROM users WHERE user_id=?", (user_id,))
    print(cur.execute)
    promo_id = cur.fetchone()[0]
    if not promo_id:
        await message.reply("You have not registered yet. Please use the /start command to register. ")
        return
    promo_text = "🔒🔍Worried about personal information being leaked? Use our 🤖 to check if your personal information has ever been leaked! 👀\nOur 🤖 can help you check if your phone number📱, email address📧, password🔑, and other sensitive information have been exposed to the risk of leaks. Use our 🤖 to check your personal information and feel more secure online! 💻"
    referral_link = f"{promo_text}\nhttps://t.me/{bot_id}?start={promo_id}"
    promo_button = types.InlineKeyboardButton("Quick forward", url=f"https://t.me/share/url?url={referral_link}")
    promo_keyboard = types.InlineKeyboardMarkup().add(promo_button)
    await message.reply(f"Share this link to promote the bot:https://t.me/{bot_id}?start={promo_id}", reply_markup=promo_keyboard)

@dp.message_handler(commands=["about"])
async def about_me(message: types.Message):
    about_text = "Xin chào, tôi là một sinh viên đến từ Việt Nam. Tôi học lập trình để phát triển kỹ năng bảo vệ an ninh mạng và thông tin nhạy cảm. Với sự gia tăng của internet và các thiết bị kết nối, việc bảo vệ thông tin của mọi người trở nên ngày càng quan trọng. Như một người đam mê công nghệ, tôi muốn học lập trình để có thể bảo vệ thông tin của mọi người và trở thành một nhà phát triển tin cậy hơn.\n\nCảm ơn bạn đã sử dụng dịch vụ của tôi!"
    await message.reply(about_text)

@dp.message_handler(commands=["qq"])
async def qq(message: types.Message):
    user = message.from_user
    user_text = message.text
    record_user_info(user, user_text)
    cur.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cur.fetchone()
    if not user:
        await message.reply("You have not registered. Please use /start to register.")
        return
    if user[2] + user[3] <= 0:
        await message.reply("You have no free chances left. Please invite more friends to get more free chances.")
        return
    fields = ["free_chances", "daily_chances"]
    non_zero_fields = [f for f in fields if user[fields.index(f) + 2] > 0]
    if not non_zero_fields:
        await message.reply("You have no free chances left. Please try again later.")
        return
    qq_number = message.get_args()
    if not qq_number:
        await message.reply("Please provide a QQ number.")
        return
    chosen_field = random.choice(non_zero_fields)
    cur.execute(f"UPDATE users SET {chosen_field}={chosen_field}-1 WHERE user_id=?", (message.from_user.id,))
    conn.commit()
    keyboard = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton(text="Yes", callback_data="qq_info_yes")
    no_button = types.InlineKeyboardButton(text="No", callback_data="qq_info_no")
    keyboard.row(yes_button, no_button)
    await message.reply(f"You have used 1 {chosen_field} and have {user[2] + user[3] - 1} chances left.\n\nDo you want to continue to check the QQ number {qq_number}?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "qq_info_yes")
async def process_callback_qq_info_yes(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    qq_number = callback_query.message.text.split(" ")[-1][:-1]
    result = await getqqinfo(qq_number)
    if len(result) == 24:
        result == 'Not leaked'
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=result)

@dp.callback_query_handler(lambda c: c.data == "qq_info_no")
async def process_callback_qq_info_no(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=f'mud in your eye！')

@dp.message_handler(commands=['sendphoto'])
async def send_photo(message: types.Message):
    if message.from_user.id not in adminstartr:
        return await message.reply('Non-robotic administrator.')
    sendphotoday = message.get_args()
    cont = 0
    timestamp = time.time()
    local_time = time.localtime(timestamp)
    month = local_time.tm_mon
    day = local_time.tm_mday
    times = f"{month}-{day}"
    url = 'https://www.xhfz8.com/'
    if sendphotoday:
        times = sendphotoday
    try:
        response_text = requests.get(url=url).text
    except Exception as e:
        print(e)
        return
    html = etree.HTML(response_text)
    list_data = [li for li in html.xpath("//li[@class='contentli']")]
    for li in list_data:
        li_time = li.xpath("./span[@class='spanli']/text()")[0]
        if times == li_time:
            print(times)
            title = li.xpath("./span[@class='lileft']/a/text()")[0]
            herf = li.xpath("./span[@class='lileft']/a/@href")[0]
            try:
                response_text = requests.get(url=herf).text
            except Exception as e:
                print(e)
                continue
            A_html = etree.HTML(response_text)
            link = A_html.xpath("//span[@class='icon icon-03']")[0]
            a_text = link.xpath('./following-sibling::a/text()')[0]
            down_link = re.findall(r"window.open\('(.*?)'\);", A_html.xpath("//span[@class='Fengdown']/@onclick")[0])
            img = A_html.xpath("//div[@class='art-content pt10 f16 lh200']//img/@src")
            data = f"{title}\n{down_link[0]}\n#{a_text}"
            data = data.replace("软件截图", "")
            if img:
                photo_path_url = img[-1]
                await getwebhook(photo_path_url, caption=data)
            else:
                await getwebhook(photo_path_url=None, caption=data)
            time.sleep(0.3)
            cont += 1
    await message.reply(f"Update completed today:{times}Total renewal:{cont}")
    
async def getwebhook(photo_path_url, caption):
    if photo_path_url:
            await bot.send_chat_action(chat_id=channel_id, action=types.ChatActions.UPLOAD_PHOTO)
            await bot.send_photo(chat_id=channel_id, photo=photo_path_url, caption=caption)
    else:
        await bot.send_message(chat_id=channel_id, text=caption)

def record_user_info(user, user_text):
    user_id = user.id
    user_first_name = user.first_name
    user_last_name = user.last_name
    user_full_name = user.full_name
    user_username = user.username
    info = f"User ID: {user_id}, First Name: {user_first_name}, Last Name: {user_last_name}, Full Name: {user_full_name}, Username: {user_username}, Your text: {user_text}"
    print(info)
    with open('bot.log', 'a') as f:
        f.write(info + '\n')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
