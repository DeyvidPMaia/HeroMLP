# conquistas.py 24/03/2025 22:00 (excluir changelings)

import discord
from discord import Embed
from discord.ext import commands
import json
import os
import asyncio
import logging
import time
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario
from views import PaginatedSelectionView, ConfirmationView, PaginatedView

CONQUISTAS_PATH = "resources/conquistas.json"

logger = logging.getLogger(__name__)

def carregar_conquistas():
    """Carrega as conquistas do arquivo JSON."""
    if not os.path.exists(CONQUISTAS_PATH):
        logger.info("Arquivo de conquistas não encontrado. Retornando vazio.")
        return {"conquistas": []}
    with open(CONQUISTAS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def carregar_conquistas_usuarios(guild_id):
    """Carrega as conquistas dos usuários para um servidor específico."""
    path = f"resources/servidores/{guild_id}_conquistas_usuarios.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_conquistas_usuarios(guild_id, dados):
    """Salva as conquistas dos usuários no arquivo do servidor."""
    path = f"resources/servidores/{guild_id}_conquistas_usuarios.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def normalize(name: str) -> str:
    """Normaliza um nome para busca, removendo espaços e convertendo para minúsculas."""
    return "".join(name.lower().split())

async def simple_paginate(ctx, items, title, color, total_conquistas, possuidas, initial_page=0):
    """Função de paginação simples com botões para conquistas possuídas."""
    items_per_page = 10
    items_list = [{"nome": item.split("\n")[0].strip(), "especie": item.split("\n")[1].strip()} for item in items]
    total_pages = (len(items_list) + items_per_page - 1) // items_per_page
    initial_page = max(0, min(initial_page, total_pages - 1))  # Limita a página inicial
    description = f"{ctx.author.mention}, suas conquistas:"
    view = PaginatedSelectionView(ctx, ctx.author, items_list, title, description, color, items_per_page)
    view.current_page = initial_page  # Define a página inicial
    msg = await ctx.send(embed=view.get_embed(), view=view)

    last_interaction = time.time()
    last_page = initial_page
    while time.time() - last_interaction < 30:
        if view.result or view.current_page != last_page:  # Verifica seleção ou mudança de página
            view.result = None  # Reseta para navegação contínua
            view.current_page = max(0, min(view.current_page, total_pages - 1))
            last_page = view.current_page
            await msg.edit(embed=view.get_embed(), view=view)
            last_interaction = time.time()
        await asyncio.sleep(0.1)
    await msg.edit(view=None)  # Remove os botões silenciosamente após 30 segundos

class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_views = {}  # Armazena as views ativas por usuário

    @commands.command(name="conquistas", help="Mostra todas as conquistas disponíveis. Use !!conquistas <número> para ir a uma página específica.")
    async def conquistas(self, ctx, page: str = "1"):  # Mudado para str com padrão "1"
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Desativa qualquer view ativa anterior do usuário
        if user_id in self.active_views:
            old_view = self.active_views[user_id]
            await old_view["message"].edit(view=None)
            del self.active_views[user_id]

        # Converte page para inteiro, usa 1 se inválido
        try:
            page_num = int(page)
        except ValueError:
            page_num = 1  # Padrão para página 1 se a entrada for inválida

        # Inicializa estatísticas com todas as chaves necessárias
        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        conquistas_default = {
            "uso_comando_conquistas": 0,
            "uso_comando_conquistei": 0,
            "avaliacoes_conquista": 0,
            "conquistas_obtidas": 0,
            "tentativas_sem_coracoes": 0,
            "tentativas_falhadas": 0,
            "coracoes_gastos_conquista": 0,
            "changelings_usados_conquista": 0
        }
        estatisticas.setdefault("conquistas", conquistas_default)
        estatisticas.setdefault("estatisticas_meus_personagens", {})
        estatisticas["conquistas"]["uso_comando_conquistas"] += 1

        conquistas = carregar_conquistas().get("conquistas", [])
        if not conquistas:
            await ctx.send("📜 **Nenhuma conquista disponível em Equestria no momento.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        # Prepara a lista de conquistas para PaginatedSelectionView
        items_list = [{"nome": conq["nome"], "especie": conq["descricao"]} for conq in conquistas]
        total_pages = (len(items_list) + 9) // 10  # 10 itens por página
        initial_page = max(0, min(page_num - 1, total_pages - 1))  # Ajusta a página inicial
        title = "🏆 Conquistas de Equestria"
        description = f" Clique em um número para avaliar uma conquista."
        view = PaginatedSelectionView(ctx, ctx.author, items_list, title, description, discord.Color.gold())
        view.current_page = initial_page  # Define a página inicial
        msg = await ctx.send(embed=view.get_embed(), view=view)

        # Armazena a view ativa
        self.active_views[user_id] = {"message": msg, "view": view}

        # Processa seleções e navegação com timeout de 30 segundos sem interação
        last_interaction = time.time()
        last_page = initial_page
        while user_id in self.active_views and time.time() - last_interaction < 30:
            if view.result or view.current_page != last_page:  # Verifica seleção ou mudança de página
                if view.result:  # Seleção de conquista
                    conquista_selecionada = conquistas[items_list.index(view.result)]
                    await msg.edit(view=None)

                    title = "Avaliar Conquista"
                    description = f"{ctx.author.mention}, deseja avaliar **{conquista_selecionada['nome']}**?\nConfirme ou cancele abaixo."
                    confirm_view = ConfirmationView(ctx, [ctx.author], title, description, discord.Color.blue())
                    confirm_msg = await ctx.send(embed=confirm_view.get_embed(), view=confirm_view)
                    await confirm_view.wait()

                    if not confirm_view.cancelled and len(confirm_view.confirmations) == 1:
                        await self.evaluate_conquista(ctx, conquista_selecionada)
                    else:
                        await ctx.send("✅ Avaliação cancelada.")

                    view.result = None
                    view.current_page = max(0, min(view.current_page, total_pages - 1))
                    await msg.edit(embed=view.get_embed(), view=view)

                view.current_page = max(0, min(view.current_page, total_pages - 1))
                last_page = view.current_page
                await msg.edit(embed=view.get_embed(), view=view)
                last_interaction = time.time()
            await asyncio.sleep(0.1)

        if user_id in self.active_views:
            await msg.edit(view=None)
            del self.active_views[user_id]
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)


    async def evaluate_conquista(self, ctx, conquista):
        """Lógica de avaliação de uma conquista."""
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        conquistas_default = {
            "uso_comando_conquistas": 0,
            "uso_comando_conquistei": 0,
            "avaliacoes_conquista": 0,
            "conquistas_obtidas": 0,
            "tentativas_sem_coracoes": 0,
            "tentativas_falhadas": 0,
            "coracoes_gastos_conquista": 0,
            "changelings_usados_conquista": 0
        }
        estatisticas.setdefault("conquistas", conquistas_default)
        estatisticas.setdefault("estatisticas_meus_personagens", {})
        estatisticas["conquistas"]["avaliacoes_conquista"] += 1

        conquistas_usuario = carregar_conquistas_usuarios(guild_id)

        if user_id in conquistas_usuario and conquista["id"] in conquistas_usuario[user_id]:
            await ctx.send(f"🏅 **Você já trouxe '{conquista['nome']}' para a luz de Equestria!**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        dados_guild = carregar_dados_guild(guild_id)
        dados_guild.setdefault("usuarios", {})
        dados_guild.setdefault("personagens_por_usuario", {})
        dados_guild.setdefault("personagens", [])
        dados_guild.setdefault("personagens_salvos", [])
        usuario_dados = dados_guild["usuarios"].setdefault(user_id, {
            "coracao": 0,
            "quantidade_amor": 0,
            "changeling": [],
            "trevo": 0,
            "nivel_perfil": 0,
            "album": False,
            "filme": 0
        })

        coracoes = usuario_dados.get("coracao", 0)
        if coracoes < 5:
            estatisticas["conquistas"]["tentativas_sem_coracoes"] += 1
            await ctx.send(f"❌ **Você precisa de 5 ❤️ para buscar essa glória! Você tem apenas {coracoes}.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        personagens_usuario = dados_guild["personagens_por_usuario"].get(user_id, [])
        changelings = usuario_dados.get("changeling", [])
        personagens_validos = []

        for p in personagens_usuario:
            personagens_validos.append({"nome": p["nome"], "especie": p.get("especie", "Desconhecida")})

        for ch in changelings:
            if isinstance(ch, dict) and ch["nome"].startswith("cha") and not ch["nome"][3:].isdigit():
                nome_original = ch["nome"][3:]
                personagens_validos.append({"nome": nome_original, "especie": ch["especie"]})

        todos_personagens = dados_guild["personagens"] + dados_guild["personagens_salvos"]

        if self.verificar_condicoes(conquista["condicoes"], personagens_validos, todos_personagens):
            usuario_dados["coracao"] -= 5
            estatisticas["conquistas"]["coracoes_gastos_conquista"] += 5
            changelings_modificados = list(changelings)  # Cria uma cópia para modificação

            for cond in conquista["condicoes"]:
                if cond["tipo"] == "incluir":
                    required_name = cond["personagem"]
                    required_name_lower = normalize(required_name)
                    # Verifica se o personagem não está na lista de personagens normais
                    if not any(normalize(p["nome"]) == required_name_lower for p in personagens_usuario):
                        for idx, ch in enumerate(changelings_modificados):
                            if isinstance(ch, dict) and normalize(ch["nome"][3:]) == required_name_lower:
                                changelings_modificados.pop(idx)  # Remove o changeling usado
                                estatisticas["conquistas"]["changelings_usados_conquista"] += 1
                                estatisticas["estatisticas_meus_personagens"].setdefault(ch["nome"][3:], {
                                    "resgatado": 0,
                                    "enviado": 0,
                                    "recebido": 0,
                                    "exibido": 0,
                                    "uso_como_changeling_conquista": 0,
                                    "sorteado_para_recompensa": 0,
                                    "coracoes_concedidos_recompensa": 0,
                                    "nome_no_biscoito": 0,
                                    "salvo_por_trevo_por_chamado": {},
                                    "perdido_por_chamado": {},
                                    "uso_como_changeling_conquista": 0,
                                    "receber_nome_loja": 0,
                                })
                                estatisticas["estatisticas_meus_personagens"][ch["nome"][3:]]["uso_como_changeling_conquista"] += 1
                                break
                elif cond["tipo"] == "contar" and cond.get("atributo") == "especie":
                    especie = normalize(cond["valor"])
                    minimo = int(cond["min"])
                    count = sum(1 for p in personagens_validos if normalize(p["especie"]) == especie)
                    # Se precisar usar changelings para atingir o mínimo
                    if count >= minimo:
                        changelings_usados = 0
                        for idx, ch in enumerate(list(changelings_modificados)):
                            if normalize(ch["especie"]) == especie:
                                changelings_modificados.pop(idx)  # Remove o changeling usado
                                changelings_usados += 1
                                estatisticas["conquistas"]["changelings_usados_conquista"] += 1
                                estatisticas["estatisticas_meus_personagens"].setdefault(ch["nome"][3:], {
                                    "resgatado": 0,
                                    "enviado": 0,
                                    "recebido": 0,
                                    "exibido": 0,
                                    "uso_como_changeling_conquista": 0,
                                    "sorteado_para_recompensa": 0,
                                    "coracoes_concedidos_recompensa": 0,
                                    "nome_no_biscoito": 0,
                                    "salvo_por_trevo_por_chamado": {},
                                    "perdido_por_chamado": {},
                                    "uso_como_changeling_conquista": 0,
                                    "receber_nome_loja": 0,
                                })
                                estatisticas["estatisticas_meus_personagens"][ch["nome"][3:]]["uso_como_changeling_conquista"] += 1
                                if changelings_usados >= minimo:
                                    break

            usuario_dados["changeling"] = changelings_modificados  # Atualiza a lista de changelings

            conquistas_usuario.setdefault(user_id, []).append(conquista["id"])
            estatisticas["conquistas"]["conquistas_obtidas"] += 1
            salvar_conquistas_usuarios(guild_id, conquistas_usuario)
            await ctx.send(f"🎉 **Parabéns, {ctx.author.mention}! Você conquistou: {conquista['nome']}** 🏅 (-5 ❤️)")
        else:
            usuario_dados["coracao"] -= 5
            estatisticas["conquistas"]["coracoes_gastos_conquista"] += 5
            estatisticas["conquistas"]["tentativas_falhadas"] += 1
            await ctx.send("😔 **A glória de Equestria ainda está além do seu alcance. Continue ajudando os amigos!** (-5 ❤️)")

        dados_guild["usuarios"][user_id] = usuario_dados
        salvar_dados_guild(guild_id, dados_guild)
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

    def verificar_condicoes(self, condicoes, personagens_usuario, todos_personagens):
        """Verifica se as condições da conquista são atendidas pelo usuário."""
        for condicao in condicoes:
            tipo = condicao["tipo"]
            if tipo == "incluir":
                if not any(normalize(p["nome"]) == normalize(condicao["personagem"]) for p in personagens_usuario):
                    return False
            elif tipo == "excluir":
                if any(normalize(p["nome"]) == normalize(condicao["personagem"]) for p in personagens_usuario):
                    return False
            elif tipo == "contar":
                atributo = condicao.get("atributo")
                valor = normalize(condicao.get("valor"))
                minimo = int(condicao.get("min"))
                count = sum(1 for p in personagens_usuario if normalize(p.get(atributo, "")) == valor)
                if count < minimo:
                    return False
            elif tipo == "total":
                if condicao.get("min") == "total_personagens":
                    if len(personagens_usuario) < len(todos_personagens):
                        return False
                else:
                    try:
                        minimo = int(condicao.get("min"))
                    except:
                        return False
                    if len(personagens_usuario) < minimo:
                        return False
        return True


    @commands.command(name="conquistei", help="Exibe todas as conquistas que você possui. Use !!conquistei <número> para ir a uma página específica.")
    async def conquistei(self, ctx, page: str = "1"):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Desativa qualquer view ativa anterior do usuário em !!conquistei
        if user_id in self.active_views:
            old_view = self.active_views[user_id]
            await old_view["message"].edit(view=None)
            del self.active_views[user_id]

        # Tenta converter o argumento para inteiro, se falhar, define como 1
        try:
            page_num = int(page)
        except ValueError:
            page_num = 1

        # Inicializa estatísticas com todas as chaves necessárias
        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        conquistas_default = {
            "uso_comando_conquistas": 0,
            "uso_comando_conquistei": 0,
            "avaliacoes_conquista": 0,
            "conquistas_obtidas": 0,
            "tentativas_sem_coracoes": 0,
            "tentativas_falhadas": 0,
            "coracoes_gastos_conquista": 0,
            "changelings_usados_conquista": 0
        }
        estatisticas.setdefault("conquistas", conquistas_default)
        estatisticas.setdefault("estatisticas_meus_personagens", {})
        estatisticas["conquistas"]["uso_comando_conquistei"] += 1

        conquistas_usuario = carregar_conquistas_usuarios(guild_id)
        user_conquistas = conquistas_usuario.get(user_id, [])

        if not user_conquistas:
            await ctx.send("🏅 **Você ainda não ajudou a conquistar glórias em Equestria.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        todas = carregar_conquistas().get("conquistas", [])
        dicionario = {c["id"]: c for c in todas}

        items = []
        for cid in user_conquistas:
            conq = dicionario.get(cid)
            if conq:
                items.append(f"**{conq['nome']}**\n{conq['descricao']}")
            else:
                items.append(f"**ID: {cid}**\nConquista perdida no tempo")

        # Define o número máximo de conquistas por página (valor editável)
        max_conquistas = 5  # Altere este valor para mudar o número de conquistas por página

        # Calcula o total de páginas disponíveis
        total_pages = (len(items) + max_conquistas - 1) // max_conquistas
        # Ajusta a página inicial: se for menor que 1, usa 1; se for maior que total_pages, usa total_pages
        page_num = max(1, min(page_num, total_pages))  

        # Cria a view paginada para navegação sem seleção, utilizando PaginatedView
        view = PaginatedView(
            ctx,
            ctx.author,
            items,
            f"🏆 Conquistas de {ctx.author.name}",
            "Use os botões abaixo para navegar pelas suas conquistas.",
            discord.Color.purple(),
            items_per_page=max_conquistas
        )
        # Define a página inicial (lembre-se que PaginatedView usa index base 0)
        view.current_page = page_num - 1
        msg = await ctx.send(embed=view.get_embed(), view=view)
        view.message = msg

        # Armazena a view ativa para gerenciamento (caso necessário)
        self.active_views[user_id] = {"message": msg, "view": view}

        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))