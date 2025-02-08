# ajuda.py

import discord
from discord.ext import commands
from discord import Embed, Interaction, ui
import globals
from paginacaoPersonagens import PaginacaoPersonagens

class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="comandos", help="Lista todos os comandos disponíveis.")
    async def comandos(self, ctx):
        comandos_gerais = []
        comandos_adm = []

        for command in self.bot.commands:
            if command.cog_name == "Ajuda":  # Ignora o próprio comando de ajuda
                continue
            if any("moderador" in str(check) for check in command.checks):
                comandos_adm.append(f"**!!{command.name}**: {command.help}")
            else:
                comandos_gerais.append(f"**!!{command.name}**: {command.help}")

        embed = discord.Embed(
            title="📜 Lista de Comandos",
            color=discord.Color.blue()
        )

        if comandos_gerais:
            embed.add_field(name="✨ Comandos Gerais ✨", value="\n".join(comandos_gerais), inline=False)

        if comandos_adm:
            embed.add_field(name="🔒 Comandos de Administradores 🔒", value="\n".join(comandos_adm), inline=False)

        await ctx.send(embed=embed)
    

# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(Ajuda(bot))
