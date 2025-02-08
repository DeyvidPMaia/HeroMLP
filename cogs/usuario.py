#usuario.py

import discord
from discord import Embed
from discord.ext import commands
from server_data import carregar_dados_guild  # Função que carrega o JSON do servidor

class Usuario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_cache = {}

    @commands.command(name="meus", help="Exibe os personagens salvos por um usuário.")
    async def meus_personagens(self, ctx, user: discord.User = None):
        user = user or ctx.author
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        personagens_por_usuario = dados.get("personagens_por_usuario", {})

        personagens = personagens_por_usuario.get(str(user.id), [])

        if personagens:
            lista = "\n".join([f"{p['nome']} ({p['especie']})" for p in personagens])
            embed = Embed(
                title=f"Personagens salvos por {user.name}",
                description=lista,
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ **Nenhum personagem salvo por {user.name}.**")

    @commands.command(name="ranking", help="Mostra quantos personagens cada usuário salvou.")
    async def ranking(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        contador_personagens_salvos = dados.get("contador_personagens_salvos", {})
        personagens_por_usuario = dados.get("personagens_por_usuario", {})

        if contador_personagens_salvos:
            ranking_lista = []
            # Itera pelos usuários ordenados pelo número de personagens salvos (em ordem decrescente)
            for user_id, count in sorted(contador_personagens_salvos.items(), key=lambda item: item[1], reverse=True):
                # Pula usuários sem personagens salvos
                if not personagens_por_usuario.get(user_id) or len(personagens_por_usuario.get(user_id)) == 0:
                    continue

                # Busca o usuário na cache ou via API do Discord
                if user_id not in self.user_cache:
                    try:
                        user_obj = await self.bot.fetch_user(user_id)
                        self.user_cache[user_id] = user_obj
                    except Exception:
                        self.user_cache[user_id] = f"Usuário {user_id}"
                user_name = (
                    self.user_cache[user_id].name
                    if not isinstance(self.user_cache[user_id], str)
                    else self.user_cache[user_id]
                )

                ranking_lista.append(f"{user_name}: **{count} personagens salvos**")

            if ranking_lista:
                await ctx.send("🏆 **Ranking de Salvadores de Personagens:** 🏆\n" + "\n".join(ranking_lista))
            else:
                await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")
        else:
            await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")


async def setup(bot):
    await bot.add_cog(Usuario(bot))
