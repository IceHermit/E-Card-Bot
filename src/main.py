# ============================== IMPORT =============================
import os
import discord
from discord.ext import commands
from keep_alive import keep_running
import sqlite3 as sql
from utils import views
import yaml
from asyncio import sleep as async_sleep
from dotenv import load_dotenv


# =============================== INIT ==============================
with open("utils/strings.yaml", "r", encoding="utf-8") as f:
    STRINGS = yaml.safe_load(f)
mod_ids = STRINGS.get("mod_ids")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!!", intents=intents)

SQL_CONNECTION = sql.connect("people_in_debt.db", autocommit = True)
SQL = SQL_CONNECTION.cursor()

SQL.execute("""CREATE TABLE IF NOT EXISTS users 
    (id INT PRIMARY KEY,
    money INT,
    can_work BOOLEAN);""")


# =============================== UTIL ==============================
def getPlayer(id):
    SQL.execute(f"SELECT * FROM users WHERE id = {id}")
    results = SQL.fetchall()
    if not len(results):
        return None
    return results[0]


def getTwoPlayers(player1, player2):
    p1 = getPlayer(player1.id)
    p2 = getPlayer(player2.id)
    if p1 is None or p2 is None:
        return False, False
    return p1, p2


# ========================== BOT COMMANDS ==========================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="nostalgia", description= STRINGS["descriptions"]["nostalgia"])
async def nostalgia(interaction: discord.Interaction, romanji: bool = False):     
    await interaction.response.send_message(STRINGS["theme_song"]["romanji" if romanji else "japanese"])


@bot.tree.command(name="register", description=STRINGS["descriptions"]["register"])
async def register(interaction: discord.Interaction, user: discord.User = None):
    if user is None:
        user = interaction.user
    
    if getPlayer(user.id) is not None:
        await interaction.response.send_message(STRINGS["errors"]["reregister"])
        return
        
    SQL.execute(f"INSERT INTO users VALUES ({user.id}, {1000}, {True})")
    await interaction.response.send_message(f"`Successfully registered:` {user.mention}! Thank you for signing your soul away!")


@bot.tree.command(name="give", description=STRINGS["descriptions"]["give"])
async def give(interaction: discord.Interaction, user: discord.User, amount: int):
    if interaction.user.id not in mod_ids:
        await interaction.response.send_message(STRINGS["errors"]["mod"])
        return
    
    target = getPlayer(user.id)
    if target is None:
        await interaction.response.send_message(STRINGS["errors"]["notregistered"])
        return
    
    
    new_balance = int(target[1]) + int(amount)
    SQL.execute(f"UPDATE users SET money = {new_balance} WHERE id = {target[0]}")

    await interaction.response.send_message(
        f"Succesfully updated the account balance of {user.mention}\n" +
        f"New account balance = ${new_balance}")


@bot.tree.command(name="play", description=STRINGS["descriptions"]["play"])
async def play(interaction: discord.Interaction, slave: discord.User, slave_bet: int, emperor: discord.User, emp_bet: int):
    if interaction.user == bot.user:
        return
    if slave == emperor:
        await interaction.response.send_message(STRINGS["errors"]["selfplay"])
        return
    try:
        slave_bet = int(slave_bet)
        emp_bet = int(emp_bet)
    except ValueError:
        await interaction.response.send_message(STRINGS["errors"]["nanbet"])
        return

    if slave_bet < 100 or emp_bet < 100:
        await interaction.response.send_message(STRINGS["errors"]["smallbet"])
        return

    userS, userE = getTwoPlayers(slave, emperor)
    if not userS or not userE:
        await interaction.response.send_message(STRINGS["errors"]["notregistered"])
        return
    if userS[1] < slave_bet or userE[1] < emp_bet:
        await interaction.response.send_message(STRINGS["errors"]["highbet"])
        return

    betconf = views.BetConfirmationView(slave, emperor)
    await interaction.response.send_message(
        f"Both players please confirm your bets:\n {slave.name} = ${slave_bet} (playing Slave side)\n {emperor.name} = ${emp_bet} (playing Emperor side)",
        view=betconf)
    confmsg = await interaction.original_response()
    timeout = await betconf.wait()
    if timeout or (not betconf.confirm1) or (not betconf.confirm2):
        newmsg = await interaction.followup.send(STRINGS["errors"]["noconfirmation"])
        await async_sleep(1)
        await confmsg.delete()
        await newmsg.delete()
        return

    await confmsg.delete()
    rounds = 1
    turne = await interaction.followup.send(
        f"`Epic showdown between {slave.name} and {emperor.name}\nTurn #{rounds}`"
    )
    msg = await interaction.followup.send(
        f"`Playing with bets of {slave_bet} on slave side and {emp_bet} on emperor side...Creating Game`"
    )
    await async_sleep(0.25)


    while rounds < 5:
        view = views.SlaveView(slave)
        viewB = views.EmperorView(emperor)
        if rounds > 1:
            await turne.edit(content=f"`Turn #{rounds}`")
        A, B = await turn(msg, slave, emperor, view, viewB)

        if A and not B: 
            outcome = f"{emperor.name} WON and got {emp_bet + slave_bet} coins!"
            did_slave_win = False
            break
        elif not A and not B:  
            outcome = f"{slave.name} WON and got {(slave_bet*5) + emp_bet} coins!"
            did_slave_win = True
            break
        elif not A and B:  
            outcome = f"{emperor.name} WON and got {emp_bet + slave_bet} coins!"
            did_slave_win = False
            break
        else:
            await msg.edit(content="`both sides chose Citizen 🟦`")
            await async_sleep(1)
        rounds += 1

    if rounds >= 5:
        outcome = f"{slave.name} WON (by default) and got {(slave_bet*5) + emp_bet} coins!"
        did_slave_win = True

    choiceA = "Citizen 🟦" if A else "Slave 🟥"
    choiceB = "Citizen 🟦" if B else "Emperor 🟩"

    slave_bal_new = userS[1]
    emp_bal_new = userE[1]

    if did_slave_win:
        money_diff = (slave_bet * 5) + emp_bet
        slave_bal_new += money_diff
        emp_bal_new -= money_diff
    else:
        money_diff = slave_bet + emp_bet
        emp_bal_new += money_diff
        slave_bal_new -= slave_bet

    SQL.execute(f"UPDATE users SET money = {emp_bal_new} WHERE id = {userE[0]}")
    SQL.execute(f"UPDATE users SET money = {slave_bal_new} WHERE id = {userS[0]}")
    
    await msg.delete()
    await turne.delete()
    await interaction.followup.send(
        f"```{slave.name} chose {choiceA}\n{emperor.name} chose {choiceB}\n{outcome}```{slave.mention} {emperor.mention}")


async def turn(msg, userOne, userTwo, view, viewB):

    #Slave side's turn
    await msg.edit(content=f"`{userOne.name} chooses first...`\n`which card?`", view=view)
    await view.wait()
    await msg.edit(content=f"`{userOne.name} chose their card`", view=view)

    #Emperor side's turn
    await msg.edit(content=f"`{userTwo.name} chooses next...`\n`which card?`", view=viewB)
    await viewB.wait()
    await msg.edit(content=f"`{userTwo.name} chose their card too`", view=viewB)
    return view.choseCivilian, viewB.choseCivilian


@bot.tree.command(name="rules", description=STRINGS["descriptions"]["rules"])
async def rules(interaction):
    await interaction.response.send_message(STRINGS["rules"])


@bot.tree.command(name="balance", description=STRINGS["descriptions"]["balance"])
async def balance(interaction: discord.Interaction, user: discord.User = None):
    if user is None:
        user = interaction.user

    res = getPlayer(user.id)
    if res is None:
        await interaction.response.send_message(STRINGS["errors"]["notregistered"])
        return

    money = res[1]
    money = f"${money}" if money >= 0 else f"-${-money}" 
    if user == interaction.user:
        await interaction.response.send_message(f"`Your current Balance is: {money}`")
    else:
        await interaction.response.send_message(f"`{user.name}'s current Balance is: {money}`")


@bot.tree.command(name="work", description=STRINGS["descriptions"]["work"])
async def work(interaction):
    res = getPlayer(interaction.user.id)
    if res is None:
        await interaction.response.send_message(STRINGS["errors"]["notregistered"])
        return

    if not res[2]:
        await interaction.response.send_message(STRINGS["errors"]["cooldown"])
        return

    SQL.execute(f"UPDATE users SET can_work = FALSE WHERE id = {interaction.user.id}")
    game = views.WorkView(interaction)
    await game.initiate_game()
    winnings = res[1] + game.reward
    SQL.execute(f"UPDATE users SET money = {winnings} WHERE id = {interaction.user.id}")
    await async_sleep(60)
    SQL.execute(f"UPDATE users SET can_work = TRUE WHERE id = {interaction.user.id}")


@bot.command() # prefix is !!sync
async def sync(ctx, spec: str = None):
    if ctx.author.id not in mod_ids:
        await ctx.send(STRINGS["errors"]["mod"])
        return

    if spec == "global":
        await bot.tree.sync()
        await ctx.send("Synced globally, It might take a moment to update everywhere")
    else:
        bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced instantly to **{ctx.guild.name}** for testing")


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("TOKEN")
    keep_running()
    bot.run(token)
