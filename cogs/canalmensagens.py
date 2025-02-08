# canalmensagens.py

import discord
from discord.ext import commands
import globals 
from mensagensdica import enviar_dica_personagem
from mensagenssorte import enviar_sorte_automatico

class CanalMensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dica_task = None
        self.sorte_task = None

    @commands.command(name="canal", help="Configura o canal para 'dicas' ou 'sorte'.\nUso: !!canal dicas ou !!canal sorte")
    async def canal(self, ctx, tipo: str):
        tipo = tipo.lower()
        if tipo == "dicas":
            globals.ID_DO_CANAL_DICAS = ctx.channel.id
            await ctx.send(f"✅ Canal para dicas configurado para {ctx.channel.mention}.")
            if self.dica_task is None or self.dica_task.done():
                self.dica_task = self.bot.loop.create_task(enviar_dica_personagem(self.bot))
        elif tipo == "sorte":
            globals.ID_DO_CANAL_SORTE = ctx.channel.id
            await ctx.send(f"✅ Canal para sorte configurado para {ctx.channel.mention}.")
            if self.sorte_task is None or self.sorte_task.done():
                self.sorte_task = self.bot.loop.create_task(enviar_sorte_automatico(self.bot))
        else:
            await ctx.send("❌ Tipo inválido! Utilize 'dicas' ou 'sorte'.")


async def setup(bot):
    await bot.add_cog(CanalMensagens(bot))
