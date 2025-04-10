# usuario.py 21/03/2025 22:00 (atualizado para navegação com views.py, suporte completo a argumentos e ranking especial)

import asyncio
import discord
from discord import Embed
from discord.ext import commands
from server_data import carregar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario, require_resgate
from funcoes import maintenance_off, no_dm
from views import PaginatedView

class Usuario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_cache = {}

    @commands.command(name="meus", help="Exibe os personagens salvos ou changelings de um usuário com paginação. Use '!!meus' para personagens, '!!meus changelings' para changelings, '!!meus <ID>' ou '!!meus @usuário' para outro usuário, ou '!!meus changelings <ID>'/'!!meus changelings @usuário' para changelings de outro usuário.")
    @no_dm()
    @require_resgate
    @maintenance_off()
    async def meus_personagens(self, ctx, *, args: str = None):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Carrega e inicializa estatísticas do autor
        estatisticas_autor = carregar_estatisticas_usuario(guild_id, user_id)
        usuario_default = {
            "uso_comando_meus": 0,
            "visualizacoes_personagens": 0,
            "visualizacoes_changelings": 0,
            "visualizacoes_outros_usuarios": 0,
            "uso_comando_ranking": 0,
            "uso_comando_ostentar": 0,
            "visualizacoes_por_outros": 0
        }
        if "usuario" not in estatisticas_autor:
            estatisticas_autor["usuario"] = usuario_default
        else:
            estatisticas_autor["usuario"] = {**usuario_default, **estatisticas_autor["usuario"]}
        estatisticas_autor["usuario"]["uso_comando_meus"] += 1

        # Determina o usuário alvo e o modo (personagens ou changelings)
        user = ctx.author
        is_changelings = False
        if args:
            args_split = args.split()
            if args_split[0].lower() == "changelings":
                is_changelings = True
                if len(args_split) > 1:
                    target = " ".join(args_split[1:])
                    if target.startswith("<@"):
                        try:
                            user = await commands.UserConverter().convert(ctx, target)
                            estatisticas_autor["usuario"]["visualizacoes_outros_usuarios"] += 1
                        except commands.UserNotFound:
                            pass
                    elif target.isdigit() and len(target) == 18:
                        try:
                            user = await self.bot.fetch_user(int(target))
                            estatisticas_autor["usuario"]["visualizacoes_outros_usuarios"] += 1
                        except (discord.NotFound, ValueError):
                            await ctx.send("❌ **ID de usuário inválido ou não encontrado.**")
                            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
                            return
            else:
                if args.startswith("<@"):
                    try:
                        user = await commands.UserConverter().convert(ctx, args)
                        estatisticas_autor["usuario"]["visualizacoes_outros_usuarios"] += 1
                    except commands.UserNotFound:
                        pass
                elif args.isdigit() and len(args) == 18:
                    try:
                        user = await self.bot.fetch_user(int(args))
                        estatisticas_autor["usuario"]["visualizacoes_outros_usuarios"] += 1
                    except (discord.NotFound, ValueError):
                        await ctx.send("❌ **ID de usuário inválido ou não encontrado.**")
                        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
                        return

        dados = carregar_dados_guild(guild_id)
        user_id_target = str(user.id)
        usuarios = dados.get("usuarios", {})
        user_data = usuarios.get(user_id_target, {"coracao": 0, "quantidade_amor": 0, "trevo": 0, "changeling": []})

        # Carrega e inicializa estatísticas do usuário alvo (se diferente do autor)
        if user_id_target != user_id:
            estatisticas_alvo = carregar_estatisticas_usuario(guild_id, user_id_target)
            if "usuario" not in estatisticas_alvo:
                estatisticas_alvo["usuario"] = usuario_default
            else:
                estatisticas_alvo["usuario"] = {**usuario_default, **estatisticas_alvo["usuario"]}
            estatisticas_alvo["usuario"]["visualizacoes_por_outros"] += 1

        if is_changelings:
            changelings = user_data.get("changeling", [])
            if not changelings:
                await ctx.send(f"❌ **Nenhum changeling possuído por {user.name}.**")
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
                if user_id_target != user_id:
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id_target, estatisticas_alvo)
                return
            
            items = []
            for ch in changelings:
                if isinstance(ch, dict) and "nome" in ch:
                    items.append(f"**{ch['nome']}** ({ch.get('especie', 'Desconhecida')})")
                else:
                    items.append(f"**{ch}**")
            title = f"Changelings possuídos por {user.name}"
            color = 0x800080
            estatisticas_autor["usuario"]["visualizacoes_changelings"] += 1
        else:
            personagens_por_usuario = dados.get("personagens_por_usuario", {})
            personagens = personagens_por_usuario.get(user_id_target, [])
            
            if not personagens:
                await ctx.send(f"❌ **Nenhum personagem salvo por {user.name}.**")
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
                if user_id_target != user_id:
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id_target, estatisticas_alvo)
                return
            
            items = [f"**{p['nome']}** ({p.get('especie', 'Desconhecida')})" for p in personagens]
            title = f"Personagens salvos por {user.name}"
            color = 0x00ff00
            estatisticas_autor["usuario"]["visualizacoes_personagens"] += 1

        view = PaginatedView(ctx, ctx.author, items, title, "", color, items_per_page=10)
        view.message = await ctx.send(embed=view.get_embed(), view=view)

        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
        if user_id_target != user_id:
            await salvar_estatisticas_seguro_usuario(guild_id, user_id_target, estatisticas_alvo)

    @commands.command(name="ranking", help="Mostra quantos personagens cada usuário resgatou, com bônus de personagens especiais")
    @no_dm()
    @require_resgate
    @maintenance_off()
    async def ranking(self, ctx):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        usuario_default = {
            "uso_comando_meus": 0,
            "visualizacoes_personagens": 0,
            "visualizacoes_changelings": 0,
            "visualizacoes_outros_usuarios": 0,
            "uso_comando_ranking": 0,
            "uso_comando_ostentar": 0,
            "visualizacoes_por_outros": 0
        }
        if "usuario" not in estatisticas:
            estatisticas["usuario"] = usuario_default
        else:
            estatisticas["usuario"] = {**usuario_default, **estatisticas["usuario"]}
        estatisticas["usuario"]["uso_comando_ranking"] += 1

        dados = carregar_dados_guild(guild_id)
        personagens_por_usuario = dados.get("personagens_por_usuario", {})
        personagens_especiais = dados.get("personagens_especiais", {})

        if not personagens_por_usuario:
            await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        ranking_dict = {}
        for user_id_target, personagens in personagens_por_usuario.items():
            count = len(personagens)

            # Calcula o bônus de ranking dos personagens especiais
            max_ranking_bonus = 0
            has_lightly_unicorn = False
            for p in personagens:
                nome = p["nome"]
                if nome in personagens_especiais and "ranking" in personagens_especiais[nome]:
                    bonus = personagens_especiais[nome]["ranking"]
                    if nome == "Lightly Unicorn":
                        has_lightly_unicorn = True
                        max_ranking_bonus = bonus  # Lightly Unicorn tem prioridade
                        break  # Não cumulativo, para aqui
                    elif bonus > max_ranking_bonus:
                        max_ranking_bonus = bonus

            total_ranking = count + max_ranking_bonus

            if user_id_target not in self.user_cache:
                user_obj = self.bot.get_user(int(user_id_target))
                if not user_obj:
                    try:
                        user_obj = await self.bot.fetch_user(int(user_id_target))
                    except Exception:
                        user_obj = f"Usuário {user_id_target}"
                self.user_cache[user_id_target] = user_obj

            user_name = (
                self.user_cache[user_id_target].name
                if not isinstance(self.user_cache[user_id_target], str)
                else self.user_cache[user_id_target]
            )

            prefix = "🌈" if has_lightly_unicorn else "⭐" if max_ranking_bonus > 0 else ""
            bonus_text = f" (+{max_ranking_bonus})" if max_ranking_bonus > 0 else ""
            ranking_dict[user_id_target] = (total_ranking, f"{prefix}**{user_name}**: {total_ranking} personagem(s){bonus_text}")

        if not ranking_dict:
            await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        # Corrige a extração para pegar apenas o texto formatado (segundo elemento da tupla)
        ranking_lista = [entry[1][1] for entry in sorted(ranking_dict.items(), key=lambda x: x[1][0], reverse=True)]

        view = PaginatedView(ctx, ctx.author, ranking_lista, "🏆 **Detentores de Personagens** 🏆", "", discord.Color.green(), items_per_page=10)
        view.message = await ctx.send(embed=view.get_embed(), view=view)

        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

    @commands.command(name="ostentar", help="Mostra os usuários com mais corações e trevos.")
    @no_dm()
    @require_resgate
    @maintenance_off()
    async def ostentar(self, ctx):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        usuario_default = {
            "uso_comando_meus": 0,
            "visualizacoes_personagens": 0,
            "visualizacoes_changelings": 0,
            "visualizacoes_outros_usuarios": 0,
            "uso_comando_ranking": 0,
            "uso_comando_ostentar": 0,
            "visualizacoes_por_outros": 0
        }
        if "usuario" not in estatisticas:
            estatisticas["usuario"] = usuario_default
        else:
            estatisticas["usuario"] = {**usuario_default, **estatisticas["usuario"]}
        estatisticas["usuario"]["uso_comando_ostentar"] += 1

        dados = carregar_dados_guild(guild_id)
        usuarios = dados.get("usuarios", {})

        if not usuarios:
            await ctx.send("💖 **Nenhum usuário tem corações ainda.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        ranking_lista = []
        for user_id_target, user_data in usuarios.items():
            coracoes = user_data.get("coracao", 0)
            trevos = user_data.get("trevo", 0)

            if coracoes == 0 and trevos == 0:
                continue

            if user_id_target not in self.user_cache:
                user_obj = self.bot.get_user(int(user_id_target))
                if not user_obj:
                    try:
                        user_obj = await self.bot.fetch_user(int(user_id_target))
                    except Exception:
                        user_obj = f"Usuário {user_id_target}"
                self.user_cache[user_id_target] = user_obj

            user_name = (
                self.user_cache[user_id_target].name
                if not isinstance(self.user_cache[user_id_target], str)
                else self.user_cache[user_id_target]
            )

            ranking_lista.append((user_name, coracoes, trevos))

        if not ranking_lista:
            await ctx.send("💖 **Nenhum usuário tem corações ainda.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        ranking_lista.sort(key=lambda item: (item[1], item[2]), reverse=True)
        max_coracoes = max(len(str(item[1])) for item in ranking_lista)
        max_trevos = max(len(str(item[2])) for item in ranking_lista)
        ranking_texto = [
            f"**{user}**:\n 💖 {str(coracoes).ljust(max_coracoes)} | 🍀 {str(trevos).ljust(max_trevos)}"
            for user, coracoes, trevos in ranking_lista
        ]

        view = PaginatedView(ctx, ctx.author, ranking_texto, "💖 **Ricos de Coração. E Trevos** 🍀", "", discord.Color.pink(), items_per_page=10)
        view.message = await ctx.send(embed=view.get_embed(), view=view)

        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

async def setup(bot):
    await bot.add_cog(Usuario(bot))