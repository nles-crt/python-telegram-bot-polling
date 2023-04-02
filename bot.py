import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import random
import secrets
import string
import aiohttp
import datetime

TOKEN = ''        #设置机器人

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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
                return '获取失败'


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
    # Check if user is already registered
    cur.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cur.fetchone()
    if user:
        await message.reply("You have already registered. Use /chances to see your chances.")
        return

    # Check if referrer ID is valid
    referrer_id = message.get_args()
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
            # Increment referral's chances
            cur.execute("UPDATE users SET free_chances=free_chances+1 WHERE user_id=?", (referrer[0],))
            conn.commit()

    # Add user to database
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    promo_id = generate_promo_id()
    cur.execute("INSERT INTO users (user_id, promo_id, first_name, last_name) VALUES (?, ?, ?, ?)", (message.from_user.id, promo_id, first_name, last_name))
    conn.commit()

    # Send welcome message
    if referrer_id:
        await message.reply(f"Welcome to the game! You have been referred by {referrer[2]} {referrer[3]}. Your referral code is {promo_id}. You have 1 extra chance to play.")
    else:
        await message.reply(f"Welcome to the game! Your referral code is {promo_id}.")
        


@dp.message_handler(commands=["checkin"])
async def daily_check_in(message: types.Message):
    cur.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cur.fetchone()
    if not user:
        await message.reply("You have not registered. Please use /start to register.")
        return
    
    # 获取上次签到时间和当前时间
    last_check_in = user[4]
    if last_check_in == 0:
        last_check_in = datetime.datetime(2000, 1, 1) # 设置一个默认日期时间
    else:
        last_check_in = datetime.datetime.strptime(str(last_check_in), "%Y-%m-%d %H:%M:%S")
    current_time = datetime.datetime.now().timestamp()
    
    # 检查是否已经签到过了
    if last_check_in.date() == datetime.datetime.fromtimestamp(current_time).date():
        await message.reply("You have already checked in today.")
        return
    
    # 更新用户的每日机会数量和上次签到时间
    cur.execute("UPDATE users SET daily_chances=3000, last_check_in=? WHERE user_id=?", (datetime.datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S"), message.from_user.id))
    conn.commit()
    await message.reply("You have received three free chances for today.")


@dp.message_handler(commands=["help"])
async def show_help_message(message: types.Message):
    help_text = "以下是可用的命令：\n\n"
    help_text += "/start <promo_id> - 使用推广 ID 注册（可选）\n"
    help_text += "/checkin - 打卡以获得机会\n"
    help_text += "/my - 显示您的信息\n"
    help_text += "/help - 显示此帮助信息\n\n"
    help_text += "要使用 /start 命令，请输入该命令，后面跟着推广 ID（如果有）。例如：/start ABC123\n"
    help_text += "要使用 /checkin 命令，请输入该命令。您每天只能打卡一次。\n"
    help_text += "要使用 /my 命令，请输入该命令。这将显示您的用户 ID、推广 ID、免费机会、每日机会和最后打卡时间。\n"
    help_text += "要使用 /help 命令，请输入该命令。这将显示此帮助信息。\n"
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
    
"""@dp.message_handler(commands=["play"])
async def use_chances(message: types.Message):
    cur.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cur.fetchone()
    if not user:
        await message.reply("You have not registered. Please use /start to register.")
        return
    if user[2] > 0:
        cur.execute("UPDATE users SET free_chances=free_chances-1 WHERE user_id=?", (message.from_user.id,))
        conn.commit()
        await message.reply("Congratulations! You have won a prize with your free chance.")
        return
    if user[3] > 0:
        cur.execute("UPDATE users SET daily_chances=daily_chances-1 WHERE user_id=?", (message.from_user.id,))
        conn.commit()
        await message.reply("Congratulations! You have won a prize with your daily chance.")
        return
    # No chances left
    await message.reply("Sorry, you do not have any chances")"""

@dp.message_handler(commands=["qq"])
async def qq(message: types.Message):
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
    chosen_field = random.choice(non_zero_fields)
    cur.execute(f"UPDATE users SET {chosen_field}={chosen_field}-1 WHERE user_id=?", (message.from_user.id,))
    conn.commit()
    
    # 调用异步函数获取 QQ 号码信息
    qq_number = message.get_args()
    if not qq_number:
        await message.reply("Please provide a QQ number.")
        return
    result = await getqqinfo(qq_number)
    
    # 将结果返回给用户
    await message.reply(f"You have used 1 {chosen_field} and have {user[2] + user[3] - 1} chances left.\n\n{result}")
    
    
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)