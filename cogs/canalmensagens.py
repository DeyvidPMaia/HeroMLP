#atualizado 05/03

import discord
from discord.ext import commands
from server_data import carregar_dados_guild, salvar_dados_guild
from mensagensdica import enviar_dica_personagem  # Função que aceita guild_id
from mensagenssorte import enviar_sorte_automatico  # Função que aceita guild_id
from mensagensrecompensa import enviar_recompensa_automatico  # Função que aceita guild_id
from funcoes import apenas_moderador, maintenance_off, no_dm

class CanalMensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dicionários para gerenciar tasks por guild
        self.dica_tasks = {}
        self.sorte_tasks = {}
        self.recompensa_task = {}
        self.__cog_name__ = "CanalMensagens"

    def reiniciar_task(self, tipo: str, guild_id: str):
        if tipo == "dicas":
            if guild_id in self.dica_tasks and not self.dica_tasks[guild_id].done():
                self.dica_tasks[guild_id].cancel()
            self.dica_tasks[guild_id] = self.bot.loop.create_task(enviar_dica_personagem(self.bot, guild_id))
        elif tipo == "recompensa":
            if guild_id in self.recompensa_task and not self.recompensa_task[guild_id].done():
                self.recompensa_task[guild_id].cancel()
            self.recompensa_task[guild_id] = self.bot.loop.create_task(enviar_recompensa_automatico(self.bot, guild_id))
        elif tipo == "sorte":
            if guild_id in self.sorte_tasks and not self.sorte_tasks[guild_id].done():
                self.sorte_tasks[guild_id].cancel()
            self.sorte_tasks[guild_id] = self.bot.loop.create_task(enviar_sorte_automatico(self.bot, guild_id))
    
    @commands.command(name="canal", help="Configura o canal para 'dicas', 'recompensa', 'sorte' ou 'principal'.\nUso: !!canal <tipo>")
    @no_dm()
    @maintenance_off()
    @apenas_moderador()
    async def canal(self, ctx, tipo: str):
        tipo = tipo.lower()
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        
        if tipo == "dicas":
            dados["ID_DO_CANAL_DICAS"] = ctx.channel.id
            salvar_dados_guild(guild_id, dados)
            await ctx.send(f"✅ Canal para dicas configurado para {ctx.channel.mention}.")
            self.reiniciar_task("dicas", guild_id)
        elif tipo == "recompensa":
            dados["ID_DO_CANAL_RECOMPENSA"] = ctx.channel.id
            salvar_dados_guild(guild_id, dados)
            await ctx.send(f"✅ Canal para recompensas configurado para {ctx.channel.mention}.")
            self.reiniciar_task("recompensa", guild_id)
        elif tipo == "sorte":
            dados["ID_DO_CANAL_SORTE"] = ctx.channel.id
            salvar_dados_guild(guild_id, dados)
            await ctx.send(f"✅ Canal para sorte configurado para {ctx.channel.mention}.")
            self.reiniciar_task("sorte", guild_id)
        elif tipo == "principal":
            dados["ID_DO_CANAL_PRINCIPAL"] = ctx.channel.id
            salvar_dados_guild(guild_id, dados)
            # Inicializa as tasks de dicas, recompensa e sorte
            self.reiniciar_task("dicas", guild_id)
            self.reiniciar_task("recompensa", guild_id)
            self.reiniciar_task("sorte", guild_id)
            await ctx.send(f"✅ Canal principal configurado para {ctx.channel.mention} e tasks iniciadas.")
        else:
            await ctx.send("❌ Tipo inválido. Use 'dicas', 'recompensa', 'sorte' ou 'principal'.")

async def setup(bot):
    await bot.add_cog(CanalMensagens(bot))
