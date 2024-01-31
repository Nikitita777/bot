# bot
import discord
import requests
from discord.ext import commands, tasks
from cfg import token
import random
import mysql.connector
from PIL import Image, ImageDraw, ImageFont

dbconfig = {'host': '127.0.0.1', 'user': 'root', 'password': '11111111', 'database': 'sys'}
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='*', intents=intents)
name = ["Привет", "Хай", "Ку", "Хелоу"]
game = ["Чтобы произвести стекло, нужно использовать глину?0",
        "Самый большой материк – это Евразия?1",
        "Правда, что если смешать красный и зеленый, то получится коричневый?1"]
sent = ""
images = ["purple.jpg", "roza.jpg", "flower.jpg"]
list_of_players = []
game_status = False
win_list = []


@bot.command()
async def start(ctx):
    await ctx.send(random.choice(name))


@bot.command()
async def text(ctx, arg="500"):
    response = requests.get("https://fakerapi.it/api/v1/texts?_quantity=1&_characters=" + str(arg))
    result = response.json()
    await ctx.send(result["data"][0]["content"])


@bot.command()
async def reg(ctx, arg=None):
    conn = mysql.connector.connect(**dbconfig)
    cursor = conn.cursor()
    _SQL = '''select * from users where name=(%s)'''
    cursor.execute(_SQL, (arg,))
    user_name = cursor.fetchall()
    if len(user_name) == 0:
        _SQL = '''insert into users(name) values(%s)'''
        cursor.execute(_SQL, (arg,))
        conn.commit()
        await ctx.send("Пользователь" + arg + "успешно зарегистрирован!")
    else:
        await ctx.send("ид:" + str(user_name[0][0]) + "имя:" + str(user_name[0][1]) + "зарегистрирован!")
    cursor.close()
    conn.close()


@bot.command()
async def rating(message):
    conn = mysql.connector.connect(**dbconfig)
    cursor = conn.cursor()
    _SQL = '''select u.name, max(s.score) from scores s left join users u on s.user_id = u.id group by u.id order by max(s.score) desc limit 5 '''
    cursor.execute(_SQL)
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    answer = ''
    smile_list = [":one:", ":two:", ":three:", ":four:", ":five:", ]
    s = 0
    for i in records:
        answer += (smile_list[s] + "Игрок " + i[0] + " набирает " + str(i[1]) + " очков" + "\n")
        s += 1
    embed = discord.Embed(
        title="ТОП 5 ИГРОКОВ",
        description=answer,
        colour=discord.Colour.from_rgb(50, 220, 170)
    )
    await message.channel.send(embed=embed)


@tasks.loop(hours=3)
async def newloop():
    conn = mysql.connector.connect(**dbconfig)
    cursor = conn.cursor()
    _SQL = '''SELECT sum(s.score), s.user_id, u.name FROM scores s
    LEFT JOIN users u ON s.user_id=u.id
    GROUP BY user_id
    ORDER BY sum(s.score) DESC;'''
    cursor.execute(_SQL)
    users_name = cursor.fetchall()
    cursor.close()
    conn.close()
    img = Image.open("stars.png")
    font = ImageFont.truetype("arial.ttf", size=10)
    canvas = ImageDraw.Draw(img)
    text = "Игрок набравший больше всего очков " + users_name[0][2] + \
           ", который набирает " + str(users_name[0][0]) + " очков "
    canvas.text((10, 10), text, "white", font=font)
    img.save("stars1.png")
    id_channel = bot.get_channel(1161306503806992477)
    await id_channel.send(file=discord.File("stars1.png"))


@bot.command()
async def topplayer(message):
    print(message.channel.id)
    await newloop.start()


@bot.command()
async def persons(ctx):
    for i in range(5):
        response = requests.get(
            "https://fakerapi.it/api/v1/persons?_quantity=1&_gender=male&_birthday_start=2000-01-01&_birthday_end=2003-11-4")
        result = response.json()
        await ctx.send(result["data"][0]["firstname"] + "\n" \
                       + result["data"][0]["lastname"] + "\n" \
                       + result["data"][0]["email"] + "\n")


@bot.command()
async def status(ctx):
    response = requests.get("https://http.cat/")
    await ctx.send("https://http.cat/" + str(response.status_code))


@bot.command()
async def kub(ctx, arg=None):
    if arg == None:
        await ctx.send("Вы не указали количество граней на кубике")
    number = random.randint(1, int(arg))
    await ctx.send(number)


@bot.command()
async def pic(ctx):
    await ctx.send(file=discord.File(random.choice(images)))


@bot.command()
async def play(ctx):
    global sent
    sent = random.choice(game)
    await ctx.send(sent[:-1])


@bot.event
async def on_message(message):
    global sent
    if "правда" in message.content.lower() and sent[-1] == "1":
        await message.channel.send("Да, это правильный ответ!")
    if "ложь" in message.content.lower() and sent[-1] == "0":
        await message.channel.send("Да, это правильный ответ!")
    if "речка" in message.content.lower():
        await message.channel.send("Да, это правильный ответ!")
    await bot.process_commands(message)


@bot.command()
async def connect(ctx):
    global list_of_players
    if not game_status:
        if ctx.author.name not in list_of_players:
            list_of_players.append(ctx.author.name)
            await ctx.send("Теперь вы в игре!")
        else:
            await ctx.send("Не надо, вы в игре!")
    else:
        await ctx.send("Игра уже началась, вы не можете присоедениться!")


@bot.command()
async def brain(ctx):
    global game_status
    win_list.clear()
    if not game_status and len(list_of_players) != 0:
        game_status = True
        await ctx.send("Игра началась! Угадай что на изображении:")
        await ctx.send(file=discord.File(random.choice(images)))


@bot.command()
async def answer(ctx, arg):
    global game_status
    if game_status:
        if ctx.author.name in list_of_players:
            if arg == "роза":
                win_list.append(ctx.author.name)
                await ctx.send("И побеждает игрок:" + win_list[0])
                game_status = False
                list_of_players.clear()
            else:
                await ctx.send("Подумай ещё...")
        else:
            await ctx.send("Вы ещё не зарегистрировались!")
    else:
        await ctx.send("Игра ущё не началась!")


@bot.command()
async def info(ctx):
    await ctx.send("И так, это правила игры brain. Написав эту комманду, вы зайдете в игру, правила очень просты, надо "
                   "угадывать что на картинке, если угадываешь, проходишь на следующий уровень и так пока не закончатся"
                   "все уровни, а дальше определяется победитель")


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.event
async def on_ready():
    print("Я готов!")


@bot.command()
async def riddle(ctx):
    await ctx.send("Что может бежать, но не может идти?")
