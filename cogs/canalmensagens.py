# canalmensagens.py

import discord
from discord.ext import commands
from server_data import carregar_dados_guild, salvar_dados_guild
from mensagensdica import enviar_dica_personagem  # Atualize essa função para aceitar guild_id
from mensagenssorte import enviar_sorte_automatico  # Atualize essa função para aceitar guild_id
from funcoes import apenas_moderador

class CanalMensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Utilizamos dicionários para gerenciar tasks por guild
        self.dica_tasks = {}
        self.sorte_tasks = {}

    @commands.command(name="canal", help="Configura o canal para 'dicas' ou 'sorte'.\nUso: !!canal dicas ou !!canal sorte")
    @apenas_moderador()
    async def canal(self, ctx, tipo: str):
        tipo = tipo.lower()
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        if tipo == "dicas":
            dados["ID_DO_CANAL_DICAS"] = ctx.channel.id
            salvar_dados_guild(guild_id, dados)
            await ctx.send(f"✅ Canal para dicas configurado para {ctx.channel.mention}.")

            # Cancela a tarefa anterior, se existir
            if guild_id in self.dica_tasks and not self.dica_tasks[guild_id].done():
                self.dica_tasks[guild_id].cancel()

            # Reinicia a tarefa de envio de dicas
            self.dica_tasks[guild_id] = self.bot.loop.create_task(enviar_dica_personagem(self.bot, guild_id))

        elif tipo == "sorte":
            dados["ID_DO_CANAL_SORTE"] = ctx.channel.id
            salvar_dados_guild(guild_id, dados)
            await ctx.send(f"✅ Canal para sorte configurado para {ctx.channel.mention}.")

            # Cancela a tarefa anterior, se existir
            if guild_id in self.sorte_tasks and not self.sorte_tasks[guild_id].done():
                self.sorte_tasks[guild_id].cancel()

            # Reinicia a tarefa de envio de sorte
            self.sorte_tasks[guild_id] = self.bot.loop.create_task(enviar_sorte_automatico(self.bot, guild_id))


async def setup(bot):
    await bot.add_cog(CanalMensagens(bot))
