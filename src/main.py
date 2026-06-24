import os
import discord
from discord.ext import commands
from keep_alive import keep_running
from tinydb import TinyDB, Query
import random
from utils import views
import yaml
from asyncio import sleep as async_sleep
from dotenv import load_dotenv
load_dotenv()

with open("utils/strings.yaml", "r", encoding="utf-8") as f:
    bot_messages = yaml.safe_load(f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!!", intents=intents)

db = TinyDB("people_in_debt.json")
debtors = Query()

mod_ids = bot_messages.get("mod_ids")


@bot.tree.command(name="nostalgia", description="Just nostalgia...")
async def nostalgia(interaction: discord.Interaction, romanji: bool = False):     
    if romanji:
        await interaction.response.send_message(bot_messages.get("theme_song", {}).get("romanji"))
        return
    await interaction.response.send_message(bot_messages.get("theme_song", {}).get("japanese"))


@bot.tree.command(name="register", description="Sign your soul away today!")
async def register(interaction: discord.Interaction, user: discord.User = None):
    if user is None:
        user = interaction.user
    
    if db.search(debtors.id == user.id):
        await interaction.response.send_message("User has already been had by the greedy creators of this bot, sorry lol")
        return
        
    db.insert({"id": user.id, "money": 1000, "canWork": True})
    
    await interaction.response.send_message(
        f"`Successfully registered:` {user.mention}! Thank you for signing your soul away!"
    )

@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


@bot.tree.command(name="give", description="Give or take money from someone's account (Can only be used by mods)")
async def give(interaction: discord.Interaction, user: discord.User, amount: int):

    if interaction.user.id not in mod_ids:
        await interaction.response.send_message("Command can only be used by mods")
        return
    
    results = db.search(debtors.id == user.id)
    if not results:
        await interaction.response.send_message("User is not registered")
        return
    
    target = results[0]
    
    new_balance = int(target["money"]) + int(amount)
    db.update({"money": new_balance}, debtors.id == target["id"])

    await interaction.response.send_message(
        f"Succesfully updated the account balance of {user.mention}\n" +
        f"New account balance = ${new_balance}")

def get_players(player1, player2):
    response1 = db.search(debtors.id == player1.id)
    if not response1:
        return False, False
    response2 = db.search(debtors.id == player2.id)
    if not response2:
        return False, False
    return response1[0], response2[0]


@bot.tree.command(name="play", description="The epic showdown.")
async def play(interaction: discord.Interaction, slave: discord.User, slave_bet: int, emperor: discord.User, emp_bet: int):
    if interaction.user == bot.user:  # you don't want to respond to urself
        return
    if slave == emperor:
        await interaction.response.send_message("You can't play against yourself, thats a rigged gamble.")
        return
    try:
        slave_bet = int(slave_bet)
        emp_bet = int(emp_bet)
    except ValueError:
        await interaction.response.send_message("Your bet is not a number.")
        return

    if slave_bet < 100 or emp_bet < 100:
        await interaction.response.send_message("Your bet must be greater than or equal to 100 debloons, type /rules to know more")
        return

    userS, userE = get_players(slave, emperor)
    if not userS or not userE:
        await interaction.response.send_message("Either one of the users in not registered yet, please run /register to register the user.")
        return
    if userS["money"] < slave_bet or userE["money"] < emp_bet:
        await interaction.response.send_message(
            "Bruh you can't bet more than you own, what you want more debt???")
        return

    betconf = views.BetConfirmationView(slave, emperor)
    await interaction.response.send_message(
        f"Both players please confirm your bets:\n {slave.name} = ${slave_bet} (playing Slave side)\n {emperor.name} = ${emp_bet} (playing Emperor side)",
        view=betconf)
    confmsg = await interaction.original_response()
    timeout = await betconf.wait()
    if timeout or (not betconf.confirm1) or (not betconf.confirm2):
        newmsg = await interaction.followup.send(
            "One or both players didn't confirm, please make a new game")
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

        if A and not B:  # A chose citizen, B choses emp
            outcome = f"{emperor.name} WON and got {emp_bet + slave_bet} coins!"
            did_slave_win = False
            break
        elif not A and not B:  # Both sides play key cards
            outcome = f"{slave.name} WON and got {(slave_bet*5) + emp_bet} coins!"
            did_slave_win = True
            break
        elif not A and B:  # A chose slave, B chose citizen
            outcome = f"{emperor.name} WON and got {emp_bet + slave_bet} coins!"
            did_slave_win = False
            break
        else:
            await msg.edit(content="`both sides chose Citizen 🟦`")
            await async_sleep(1)
        # if all these conditions are false, then both chose citizen
        rounds += 1

    if rounds >= 5:
        outcome = f"{slave.name} WON (by default) and got {(slave_bet*5) + emp_bet} coins!"
        did_slave_win = True

    choiceA = "Citizen 🟦" if A else "Slave 🟥"
    choiceB = "Citizen 🟦" if B else "Emperor 🟩"

    slave_bal_new = userS['money']
    emp_bal_new = userE['money']

    if did_slave_win:
        money_diff = (slave_bet * 5) + emp_bet
        slave_bal_new += money_diff
        emp_bal_new -= money_diff
    else:
        money_diff = slave_bet + emp_bet
        emp_bal_new += money_diff
        slave_bal_new -= slave_bet

    db.update({"money": emp_bal_new}, debtors.id == userE["id"])
    db.update({"money": slave_bal_new}, debtors.id == userS["id"])

    #final message
    await msg.delete()
    await turne.delete()
    await interaction.followup.send(
        f"```{slave.name} chose {choiceA}\n{emperor.name} chose {choiceB}\n{outcome}```{slave.mention} {emperor.mention}"
    )


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


#run the bot


@bot.tree.command(name="rules", description="check out the rules!")
async def rules(interaction):
    await interaction.response.send_message(bot_messages.get("rules"))


@bot.tree.command(name="balance", description="Check your balance (we all know you broke)")
async def balance(interaction: discord.Interaction, user: discord.User = None):
    if user is None:
        user = interaction.user

    res = db.search(debtors.id == user.id)
    if not res:
        await interaction.response.send_message(
            f"{user.name} has never played an E-card game before, run /register to register")
    else:
        money = res[0]['money']
        money = "${}".format(money) if money >= 0 else "-${}".format(abs(money)) 
        if user == interaction.user:
            await interaction.response.send_message(f"`Your current Balance is: {money}`")
        else:
            await interaction.response.send_message(f"`{user.name}'s current Balance is: {money}`")



@bot.tree.command(name="work", description="Work hard and get some debloons to gamble away")
async def work(interaction):
    resp = db.search(debtors.id == interaction.user.id)
    if not resp:
        await interaction.response.send_message(
            "This user has not played a game yet, run /register to register")
        return

    resp = resp[0]
    if resp["canWork"]:
        db.update({"canWork": False}, debtors.id == interaction.user.id)
        game = views.WorkView(interaction)
        await game.initiate_game()
        winnings = resp["money"] + game.reward
        db.update({"money": winnings}, debtors.id == interaction.user.id)
        await async_sleep(60)
        db.update({"canWork": True}, debtors.id == interaction.user.id)
    else:
        await interaction.response.send_message(
            "`You are on cooldown. Wait for 1 minute before you can work again`"
        )

@bot.command() # prefix is !!sync
async def sync(ctx, spec: str = None):
    if ctx.author.id not in mod_ids:
        await ctx.send("You do not have permission to use this command bruh")
        return

    if spec == "global":
        await bot.tree.sync()
        await ctx.send("Synced globally, It might take a moment to update everywhere")
    else:
        bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced instantly to **{ctx.guild.name}** for testing")

if __name__ == "__main__":
    token = os.getenv("TOKEN")
    keep_running()
    bot.run(token)
