#usuario.py

import asyncio
import discord
from discord import Embed
from discord.ext import commands
from server_data import carregar_dados_guild  # Função que carrega o JSON do servidor

class Usuario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_cache = {}


    @commands.command(name="meus", help="Exibe os personagens salvos por um usuário com paginação.")
    async def meus_personagens(self, ctx, user: discord.User = None):
        user = user or ctx.author
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        personagens_por_usuario = dados.get("personagens_por_usuario", {})

        personagens = personagens_por_usuario.get(str(user.id), [])

        if not personagens:
            await ctx.send(f"❌ **Nenhum personagem salvo por {user.name}.**")
            return

        # Configuração da paginação
        items_per_page = 10
        total_pages = (len(personagens) + items_per_page - 1) // items_per_page
        current_page = 0

        async def update_embed():
            start_index = current_page * items_per_page
            end_index = start_index + items_per_page
            page_content = "\n".join([f"**{p['nome']}** ({p['especie']})" for p in personagens[start_index:end_index]])

            embed = Embed(
                title=f"Personagens salvos por {user.name}",
                description=page_content,
                color=0x00ff00
            )
            embed.set_footer(text=f"Página {current_page + 1} de {total_pages}")
            return embed

        message = await ctx.send(embed=await update_embed())

        # Adiciona reações para navegar
        if total_pages > 1:
            await message.add_reaction("⏪")  # Primeira página
            await message.add_reaction("◀")  # Página anterior
            await message.add_reaction("▶")  # Próxima página
            await message.add_reaction("⏩")  # Última página

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id and reaction.emoji in ["⏪", "◀", "▶", "⏩"]

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if reaction.emoji == "⏪":
                        current_page = 0
                    elif reaction.emoji == "◀" and current_page > 0:
                        current_page -= 1
                    elif reaction.emoji == "▶" and current_page < total_pages - 1:
                        current_page += 1
                    elif reaction.emoji == "⏩":
                        current_page = total_pages - 1

                    await message.edit(embed=await update_embed())
                    await message.remove_reaction(reaction.emoji, user)

                except asyncio.TimeoutError:
                    break

            await message.clear_reactions()

    @commands.command(name="ranking", help="Mostra quantos personagens cada usuário salvou.")
    async def ranking(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        contador_personagens_salvos = dados.get("contador_personagens_salvos", {})

        if not contador_personagens_salvos:
            await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")
            return

        ranking_lista = []
        for user_id, count in sorted(contador_personagens_salvos.items(), key=lambda item: item[1], reverse=True):
            if count == 0:
                continue

            # Busca o usuário na cache ou via API do Discord
            if user_id not in self.user_cache:
                try:
                    user_obj = await self.bot.fetch_user(int(user_id))
                    self.user_cache[user_id] = user_obj
                except Exception:
                    self.user_cache[user_id] = f"Usuário {user_id}"
            user_name = (
                self.user_cache[user_id].name
                if not isinstance(self.user_cache[user_id], str)
                else self.user_cache[user_id]
            )

            ranking_lista.append(f"**{user_name}**: {count} personagens salvos")

        if not ranking_lista:
            await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")
            return

        # Configuração da paginação
        items_per_page = 10
        total_pages = (len(ranking_lista) + items_per_page - 1) // items_per_page
        current_page = 0

        async def update_embed():
            start_index = current_page * items_per_page
            end_index = start_index + items_per_page
            page_content = "\n".join(ranking_lista[start_index:end_index])

            embed = discord.Embed(
                title="🏆 **Ranking de Salvadores de Personagens** 🏆",
                description=page_content,
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Página {current_page + 1} de {total_pages}")
            return embed

        message = await ctx.send(embed=await update_embed())

        # Adiciona reações para navegar
        if total_pages > 1:
            await message.add_reaction("⏪")  # Primeira página
            await message.add_reaction("◀")  # Página anterior
            await message.add_reaction("▶")  # Próxima página
            await message.add_reaction("⏩")  # Última página

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id and reaction.emoji in ["⏪", "◀", "▶", "⏩"]

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if reaction.emoji == "⏪":
                        current_page = 0
                    elif reaction.emoji == "◀" and current_page > 0:
                        current_page -= 1
                    elif reaction.emoji == "▶" and current_page < total_pages - 1:
                        current_page += 1
                    elif reaction.emoji == "⏩":
                        current_page = total_pages - 1

                    await message.edit(embed=await update_embed())
                    await message.remove_reaction(reaction.emoji, user)

                except asyncio.TimeoutError:
                    break

            await message.clear_reactions()

async def setup(bot):
    await bot.add_cog(Usuario(bot))
