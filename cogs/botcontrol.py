# botcontrol.py

import os
import sys
from discord.ext import commands
from funcoes import apenas_moderador

class BotControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rebot", help="Encerra e reinicia o bot.")
    @apenas_moderador()
    @commands.is_owner()  # Garante que apenas o dono do bot pode executar o comando
    async def reiniciar_bot(self, ctx):
        await ctx.send("♻️ **Reiniciando o bot...**")
        await self.bot.close()  # Fecha o bot de forma limpa

        # Reinicia o script principal
        python = sys.executable
        os.execv(python, [python] + sys.argv)

async def setup(bot):
    await bot.add_cog(BotControl(bot))
