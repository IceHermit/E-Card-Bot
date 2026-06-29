# ============================== IMPORT =============================
import discord, random
from asyncio import sleep as async_sleep
import yaml


# =============================== INIT ==============================
with open("utils/strings.yaml", "r", encoding="utf-8") as f:
    STRINGS = yaml.safe_load(f)


# =============================== VIEWS =============================
class EmperorView(discord.ui.View):
    def __init__(self, player: discord.User, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.player = player
        self.choseCivilian = None
        self.user = None


    @discord.ui.button(label="Citizen", style=discord.ButtonStyle.blurple)
    async def citizen(self, interaction: discord.Interaction, button: discord.Button):

        if interaction.user.id != self.player.id:
            await interaction.response.send_message(STRINGS["errors"]["wrongturn"], ephemeral=True)
            return

        self.choseCivilian = True
        self.user = interaction.user

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
                
        await interaction.response.edit_message(view=self)
        self.stop()


    @discord.ui.button(label="Emperor", style=discord.ButtonStyle.green)
    async def emperor(self, interaction: discord.Interaction, button: discord.Button):
        
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(STRINGS["errors"]["wrongturn"], ephemeral=True)
            return

        self.choseCivilian = False
        self.user = interaction.user

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()


class SlaveView(discord.ui.View):
    def __init__(self, player: discord.User, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.player = player
        self.choseCivilian = None
        self.user = None

    @discord.ui.button(label="Citizen", style=discord.ButtonStyle.blurple)
    async def citizen(self, interaction: discord.Interaction, button: discord.Button):

        if interaction.user.id != self.player.id:
            await interaction.response.send_message(STRINGS["errors"]["wrongturn"], ephemeral=True)
            return

        self.choseCivilian = True
        self.user = interaction.user

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
                
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Slave", style=discord.ButtonStyle.red)
    async def emperor(self, interaction: discord.Interaction, button: discord.Button):
        
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(STRINGS["errors"]["wrongturn"], ephemeral=True)
            return

        self.choseCivilian = False
        self.user = interaction.user

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()


class BetConfirmationView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__()
        self.player1 = player1
        self.confirm1 = False
        self.confirm2 = False
        self.player2 = player2


    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.player1.id, self.player2.id]:
            await interaction.response.send_message("This isn't your bet!", ephemeral=True)
            return
        
        if interaction.user.id == self.player1.id:
            self.confirm1 = True
        if interaction.user.id == self.player2.id:
            self.confirm2 = True
            
        if self.confirm1 and self.confirm2:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            button.label = "All Confirmed!"
            button.style = discord.ButtonStyle.grey
            await interaction.response.edit_message(view=self)
            self.stop()
        else:
            if self.confirm1:
                button.label = "Waiting for Player 2..."
            elif self.confirm2:
                button.label = "Waiting for Player 1..."
            
            button.style = discord.ButtonStyle.blurple 
            await interaction.response.edit_message(view=self)


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.player1.id, self.player2.id]:
            await interaction.response.send_message("This isn't your bet!", ephemeral=True)
            return
        
        self.confirm1 = self.confirm2 = False
        
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        
        button.label = f"Cancelled by {interaction.user.display_name}"
        await interaction.response.edit_message(view=self)
        self.stop()


class WorkView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.args = []
        self.interaction = interaction
        self.game = random.choice([AimGameView, ShovelView])
        self.reward = self.game.reward

    async def initiate_game(self):
        interaction = self.interaction
        if self.game.name == "aim_game":
            view = AimGameView(0, interaction.user)
            game_screen = "```|" + " " * view.pos + "V" + " " * (
                10 - view.pos
            ) + "|\n|" + " " * 11 + "|\n|" + " " * view.target + "O" + " " * (
                10 - view.target) + "|```"

            await interaction.response.send_message(
                "`Press 'Shoot' when V and O are lined up`\n" + game_screen)
            og_msg = await interaction.original_response()
            while not view.shot:
                await view.update_pos()
                await async_sleep(0.05)
                game_screen = "```|" + " " * view.pos + "V" + " " * (
                    10 - view.pos
                ) + "|\n|" + " " * 11 + "|\n|" + " " * view.target + "O" + " " * (
                    10 - view.target) + "|```"
                await og_msg.edit(content= "`Press 'Shoot' when V and O are lined up`\n" +
                    game_screen,
                    view=view)
            if view.win:
                await og_msg.edit(content="You win! Nice aim, 750 debloons for you!", view=None)
            else:
                await og_msg.edit(content="Absolute L you suck, no debloons >:)", view=None)
                
        elif self.game.name == "shovel_game":
            view = ShovelView(0, interaction.user)
            await interaction.response.send_message("`Press 'Shovel' to dig out the dirt like a good boy`", view=view)
            await view.wait()
            og_msg = await interaction.original_response()
            await og_msg.edit(content=f"`Good job peasant, you earned 500 debloons`", view=None)


class AimGameView(discord.ui.View):
    name = "aim_game"
    reward = 750

    def __init__(self, pos, worker):
        super().__init__()
        self.target = random.randint(3, 8)
        self.shot = False
        self.pos = pos
        self.moving_right = True
        self.win = False
        self.worker = worker

    async def update_pos(self):
        self.pos += 1 if self.moving_right else -1
        if self.pos == 10:
            self.moving_right = False
        elif self.pos == 0:
            self.moving_right = True

    @discord.ui.button(label="Shoot", style=discord.ButtonStyle.danger)
    async def shoot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.worker.id:
            await interaction.response.send_message("Not your job lil bro", ephemeral=True)
            return
        if abs(self.pos - self.target) <= 1:
            self.win = True
        else:
            self.win = False
        self.shot = True
        self.stop()


class ShovelView(discord.ui.View):
    name = "shovel_game"
    reward = 500

    def __init__(self, workdone: int, worker: discord.User):
        super().__init__(timeout=60.0)
        self.workdone = workdone
        self.worker = worker

    @discord.ui.button(label="Shovel", style=discord.ButtonStyle.danger)
    async def shovel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.worker.id:
            await interaction.response.send_message("Not your job lil bro", ephemeral=True)
            return

        self.workdone += 10
        
        if self.workdone >= 100:
            button.disabled = True
            button.label = "Job Finished... :D"
            button.style = discord.ButtonStyle.green
            self.stop()
        else:
            button.label = f"Shovel ({self.workdone}/100)"

        await interaction.response.edit_message(
            content=f"**{interaction.user.name} is working LMAO...**\nProgress: `{self.workdone}/100`", 
            view=self
        )
