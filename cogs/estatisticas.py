#estatisticas.py 21/03/2025 10:00

import discord
from discord import Embed
from discord.ext import commands
import asyncio
from server_data import carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario
import logging

logger = logging.getLogger(__name__)

class Estatisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def paginate_stats(self, ctx, pages, title, color):
        """Função de paginação para exibir as estatísticas com navegação."""
        current_page = [0]
        total_pages = len(pages)

        def get_embed(page):
            embed = Embed(title=title, description=pages[page]["description"], color=color)
            for field in pages[page]["fields"]:
                embed.add_field(name=field["name"], value=field["value"], inline=field.get("inline", True))
            embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Página {page + 1}/{total_pages} | Use ◀ e ▶ para navegar")
            return embed

        # Verifica permissões antes de enviar a mensagem
        if not ctx.channel.permissions_for(ctx.me).send_messages:
            await ctx.send("❌ Não tenho permissão para enviar mensagens neste canal!")
            return
        if not ctx.channel.permissions_for(ctx.me).add_reactions:
            logger.warning(f"Bot sem permissão para adicionar reações no canal {ctx.channel.id}")
            # Prossegue sem reações, mas sem paginação interativa

        message = await ctx.send(embed=get_embed(current_page[0]))
        if total_pages <= 1:
            return

        navigation_emojis = ["◀", "▶"]
        try:
            for emoji in navigation_emojis:
                await message.add_reaction(emoji)
        except discord.Forbidden:
            logger.warning(f"Sem permissão para adicionar reações na mensagem {message.id}")
            return  # Sai se não puder adicionar reações

        def check(reaction, user):
            return (
                user == ctx.author and 
                reaction.message.id == message.id and 
                str(reaction.emoji) in navigation_emojis
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reaction.emoji) == "◀" and current_page[0] > 0:
                    current_page[0] -= 1
                elif str(reaction.emoji) == "▶" and current_page[0] < total_pages - 1:
                    current_page[0] += 1
                await message.edit(embed=get_embed(current_page[0]))
                try:
                    await message.remove_reaction(reaction.emoji, user)
                except discord.NotFound:
                    logger.info(f"Reação {reaction.emoji} não pôde ser removida: mensagem {message.id} não encontrada")
            except asyncio.TimeoutError:
                try:
                    await message.clear_reactions()
                except discord.NotFound:
                    logger.info(f"Não foi possível limpar reações: mensagem {message.id} não encontrada")
                except discord.Forbidden:
                    logger.warning(f"Sem permissão para limpar reações na mensagem {message.id}")
                break
            except discord.NotFound:
                logger.info(f"Mensagem {message.id} não encontrada durante interação")
                break

    @commands.command(name="estatisticas", aliases=["stats"], help="Exibe suas estatísticas pessoais em Equestria.")
    async def estatisticas(self, ctx):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Carrega e inicializa estatísticas gerais
        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        estatisticas.setdefault("estatisticas", {
            "uso_comando_estatisticas": 0
        })
        estatisticas["estatisticas"]["uso_comando_estatisticas"] += 1

        if not any(k in estatisticas for k in ["resgatar", "loja", "exibir", "amor", "criador", "trocar", "conquistas"]):
            await ctx.send("📊 **Você ainda não tem estatísticas para exibir. Comece a interagir com Equestria!**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        # Organiza as estatísticas em páginas
        pages = []

        # Página inicial: Visão geral
        overview_fields = []
        total_comandos = sum(
            estatisticas.get(cmd, {}).get(f"uso_comando_{cmd}", 0) 
            for cmd in ["resgatar", "loja", "exibir", "amor", "criador", "trocar", "conquistas", "estatisticas"]
        )
        overview_fields.append({"name": "📋 Comandos Usados", "value": f"{total_comandos} vezes"})
        
        if "resgatar" in estatisticas:
            overview_fields.append({"name": "🏇 Personagens Resgatados", "value": f"{estatisticas['resgatar'].get('resgates_totais_resgatar', 0)}"})
        if "trocar" in estatisticas:
            overview_fields.append({"name": "🔄 Trocas Concluídas", "value": f"{estatisticas['trocar'].get('trocas_concluidas_troca', 0)}"})
        if "conquistas" in estatisticas:
            overview_fields.append({"name": "🏆 Conquistas Obtidas", "value": f"{estatisticas['conquistas'].get('conquistas_obtidas', 0)}"})
        if "amor" in estatisticas:
            overview_fields.append({"name": "💖 Corações Ganhos (Amor)", "value": f"{estatisticas['amor'].get('coracoes_ganhos_amor', 0)}"})
        
        pages.append({
            "description": f"🌟 Bem-vindo(a) ao seu painel de estatísticas, {ctx.author.name}! Aqui está uma visão geral da sua jornada em Equestria.",
            "fields": overview_fields
        })

        # Página de Resgatar
        if "resgatar" in estatisticas:
            resgatar = estatisticas["resgatar"]
            fields = [
                {"name": "🏇 Resgates Totais", "value": f"{resgatar.get('resgates_totais_resgatar', 0)}"},
                {"name": "⏳ Resgates em Cooldown", "value": f"{resgatar.get('tentativas_resgate_em_cooldown_resgatar', 0)}"},
                {"name": "🔒 Resgates Bloqueados", "value": f"{resgatar.get('tentativas_resgate_bloqueado_resgatar', 0)}"},
                {"name": "🎯 Resgates por Tipo", "value": "\n".join([f"{k}: {v}" for k, v in resgatar.get('resgates_por_tipo_resgatar', {}).items()]) or "Nenhum"}
            ]
            pages.append({
                "description": "📜 **Estatísticas de Resgate** - Veja como você tem salvado os habitantes de Equestria!",
                "fields": fields
            })

        # Página de Loja
        if "loja" in estatisticas:
            loja = estatisticas["loja"]
            fields = [
                {"name": "🛒 Compras Realizadas", "value": f"{loja.get('compras_realizadas_loja', 0)}"},
                {"name": "💔 Sem Corações", "value": f"{loja.get('tentativas_sem_coracoes_loja', 0)}"},
                {"name": "🍀 Trevos Comprados", "value": f"{loja.get('trevos_comprados_loja', 0)}"},
                {"name": "🦋 Changelings Comprados", "value": f"{loja.get('changelings_comprados_loja', 0)}"}
            ]
            pages.append({
                "description": "🏪 **Estatísticas da Loja** - Suas aventuras de compras em Equestria!",
                "fields": fields
            })

        # Página de Exibir
        if "exibir" in estatisticas:
            exibir = estatisticas["exibir"]
            fields = [
                {"name": "🎭 Exibições Reais", "value": f"{exibir.get('exibicoes_reais_exibir', 0)}"},
                {"name": "🦋 Exibições Falsas", "value": f"{exibir.get('exibicoes_falsas_exibir', 0)}"},
                {"name": "🏆 Recompensas Recebidas", "value": f"{exibir.get('recompensas_recebidas_exibir', 0)}"},
                {"name": "💖 Corações Ganhos", "value": f"{exibir.get('coracoes_ganhos_exibir', 0)}"},
                {"name": "🔄 Transformações Changeling", "value": f"{exibir.get('transformacoes_changeling_exibir', 0)}"},
                {"name": "🗑️ Remoções Changeling", "value": f"{exibir.get('remocoes_changeling_exibir', 0)}"}
            ]
            pages.append({
                "description": "🎨 **Estatísticas de Exibição** - Mostre seu estilo em Equestria!",
                "fields": fields
            })

        # Página de Amor e Criador
        if "amor" in estatisticas or "criador" in estatisticas:
            fields = []
            if "amor" in estatisticas:
                amor = estatisticas["amor"]
                fields.extend([
                    {"name": "💕 Usos do Amor", "value": f"{amor.get('uso_comando_amor', 0)}"},
                    {"name": "🏆 Recompensas Amor", "value": f"{amor.get('recompensado_comando_amor', 0)}"},
                    {"name": "💖 Corações Ganhos", "value": f"{amor.get('coracoes_ganhos_amor', 0)}"},
                    {"name": "⏳ Amor em Cooldown", "value": f"{amor.get('uso_amor_em_cooldown', 0)}"}
                ])
            if "criador" in estatisticas:
                criador = estatisticas["criador"]
                fields.extend([
                    {"name": "📜 Usos do Criador", "value": f"{criador.get('uso_comando_criador', 0)}"},
                    {"name": "❌ Erros de Imagem", "value": f"{criador.get('erros_imagem_criador', 0)}"}
                ])
            pages.append({
                "description": "💖 **Estatísticas de Amor e Criador** - Espalhe carinho e celebre a magia!",
                "fields": fields
            })

        # Página de Trocar
        if "trocar" in estatisticas:
            trocar = estatisticas["trocar"]
            fields = [
                {"name": "🔄 Trocas Iniciadas", "value": f"{trocar.get('trocas_iniciadas_troca', 0)}"},
                {"name": "✅ Trocas Concluídas", "value": f"{trocar.get('trocas_concluidas_troca', 0)}"},
                {"name": "❌ Trocas Canceladas", "value": f"{trocar.get('trocas_canceladas_troca', 0)}"},
                {"name": "💔 Corações Gastos", "value": f"{trocar.get('coracoes_gastos_troca', 0)}"},
                {"name": "🚫 Sem Corações", "value": f"{trocar.get('tentativas_sem_coracoes_troca', 0)}"},
                {"name": "📉 Sem Personagens", "value": f"{trocar.get('tentativas_sem_personagens_troca', 0)}"}
            ]
            pages.append({
                "description": "🤝 **Estatísticas de Troca** - Suas negociações em Equestria!",
                "fields": fields
            })

        # Página de Conquistas
        if "conquistas" in estatisticas:
            conquistas = estatisticas["conquistas"]
            fields = [
                {"name": "🏆 Conquistas Obtidas", "value": f"{conquistas.get('conquistas_obtidas', 0)}"},
                {"name": "🔍 Avaliações", "value": f"{conquistas.get('avaliacoes_conquista', 0)}"},
                {"name": "💔 Corações Gastos", "value": f"{conquistas.get('coracoes_gastos_conquista', 0)}"},
                {"name": "❌ Falhas", "value": f"{conquistas.get('tentativas_falhadas', 0)}"},
                {"name": "🚫 Sem Corações", "value": f"{conquistas.get('tentativas_sem_coracoes', 0)}"},
                {"name": "🦋 Changelings Usados", "value": f"{conquistas.get('changelings_usados_conquista', 0)}"}
            ]
            pages.append({
                "description": "✨ **Estatísticas de Conquistas** - Suas glórias em Equestria!",
                "fields": fields
            })

        # Exibe as estatísticas com paginação
        await self.paginate_stats(ctx, pages, f"📊 Estatísticas de {ctx.author.name}", discord.Color.blue())
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

async def setup(bot):
    await bot.add_cog(Estatisticas(bot))