# utils.py 24/03/2025 20:00 (corrigido para concorrência e corrupção de dados)

import random
import discord
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_guild, salvar_estatisticas_seguro, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario
import globals
import logging
import asyncio
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Dicionário global de locks por guilda
guild_locks = {}

def get_guild_lock(guild_id: str) -> asyncio.Lock:
    if guild_id not in guild_locks:
        guild_locks[guild_id] = asyncio.Lock()
    return guild_locks[guild_id]

def log_relatorio_personagem_perdido(guild_id: str, chamado_por: str, mensagem: str):
    """Armazena informações de debug em um arquivo txt, substituindo o anterior."""
    caminho = f"resources/servidores/{guild_id}/relatorios/relatorio_personagem_perdido.txt"
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    
    hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conteudo = (
        f"Relatório de personagem_perdido\n"
        f"Guild ID: {guild_id}\n"
        f"Chamado por: {chamado_por}\n"
        f"Hora da chamada: {hora_atual}\n"
        f"Detalhes:\n{mensagem}\n"
    )
    
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

async def personagem_perdido(guild, chamado_por, quantidade=1, usar_trevo=True, dm=True, cor_chamado=discord.Colour.blue()):
    guild_id = str(guild.id)
    lock = get_guild_lock(guild_id)
    
    async with lock:  # Protege contra concorrência
        log_relatorio_personagem_perdido(guild_id, chamado_por, "Carregando dados da guild")
        dados_guild = carregar_dados_guild(guild_id)
        log_relatorio_personagem_perdido(guild_id, chamado_por, f"Dados carregados para guild: tipo {type(dados_guild)}")
        if not dados_guild:
            logger.warning(f"Dados não carregados para a guilda {guild_id}")
            return None

        # Carrega estatísticas do bot
        log_relatorio_personagem_perdido(guild_id, chamado_por, "Carregando estatísticas globais da guild")
        estatisticas_bot = carregar_estatisticas_guild(guild_id)
        log_relatorio_personagem_perdido(guild_id, chamado_por, f"Estatísticas globais carregadas: tipo {type(estatisticas_bot)}")
        bot_default = {
            "chamadas_por": {},
            "coracoes_concedidos": 0,
            "trevos_consumidos": 0,
            "estatisticas_meus_personagens": {}
        }
        if "ponymemories" not in estatisticas_bot:
            estatisticas_bot["ponymemories"] = bot_default
        else:
            estatisticas_bot["ponymemories"] = {**bot_default, **estatisticas_bot["ponymemories"]}
        
        # Garante que as chaves críticas sejam dicionários
        if "estatisticas_meus_personagens" not in estatisticas_bot:
            estatisticas_bot["estatisticas_meus_personagens"] = {}
        estatisticas_bot["ponymemories"].setdefault("chamadas_por", {})

        # Incrementa chamadas por chamado_por
        estatisticas_bot["ponymemories"]["chamadas_por"][chamado_por] = estatisticas_bot["ponymemories"]["chamadas_por"].get(chamado_por, 0) + 1

        personagens = dados_guild.setdefault("personagens", [])
        personagens_por_usuario = dados_guild.setdefault("personagens_por_usuario", {})
        personagens_salvos = dados_guild.setdefault("personagens_salvos", [])
        usuarios = dados_guild.setdefault("usuarios", {})

        log_relatorio_personagem_perdido(guild_id, chamado_por, f"Acessando personagens_por_usuario: tipo {type(personagens_por_usuario)}")
        todos_personagens_salvos = [
            (str(user_id), personagem)
            for user_id, lista in personagens_por_usuario.items()
            for personagem in lista
        ]

        if not todos_personagens_salvos:
            embed = discord.Embed(
                title="Equestria está em perigo",
                description="Ajude nossos amigos em Equestria, salvando-os do esquecimento",
                color=discord.Color.blue()
            )
            log_relatorio_personagem_perdido(guild_id, chamado_por, "Salvando dados da guild antes de retornar por falta de personagens salvos")
            salvar_dados_guild(guild_id, dados_guild)
            log_relatorio_personagem_perdido(guild_id, chamado_por, "Salvando estatísticas globais da guild antes de retornar")
            await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
            return [embed]

        if len(todos_personagens_salvos) < quantidade:
            quantidade = len(todos_personagens_salvos)

        personagens_selecionados = random.sample(todos_personagens_salvos, quantidade)

        perdidos = []
        salvos_por_trevo = {}
        estatisticas_usuarios = {}

        for user_id, personagem in personagens_selecionados:
            user_id = str(user_id)
            log_relatorio_personagem_perdido(guild_id, chamado_por, f"Acessando dados do usuário {user_id}")
            user_data = usuarios.setdefault(user_id, {"trevo": 0, "coracao": 0, "receber_dm": True})
            if "trevo" not in user_data:
                logger.error(f"Chave 'trevo' ausente em user_data para user_id {user_id}: {user_data}")
                user_data["trevo"] = 0
            
            personagem_nome = personagem["nome"]

            # Carrega estatísticas do usuário
            if user_id not in estatisticas_usuarios:
                log_relatorio_personagem_perdido(guild_id, chamado_por, f"Carregando estatísticas do usuário {user_id}")
                estatisticas_usuarios[user_id] = carregar_estatisticas_usuario(guild_id, user_id)
                log_relatorio_personagem_perdido(guild_id, chamado_por, f"Estatísticas carregadas para usuário {user_id}: tipo {type(estatisticas_usuarios[user_id])}")
                usuario_default = {"coracoes_ganhos": 0}
                if "perdido" not in estatisticas_usuarios[user_id]:
                    estatisticas_usuarios[user_id]["perdido"] = usuario_default
                else:
                    estatisticas_usuarios[user_id]["perdido"] = {**usuario_default, **estatisticas_usuarios[user_id]["perdido"]}
                if "estatisticas_meus_personagens" not in estatisticas_usuarios[user_id]:
                    estatisticas_usuarios[user_id]["estatisticas_meus_personagens"] = {}
            #der
            personagem_stats_bot = estatisticas_bot["estatisticas_meus_personagens"].setdefault(personagem_nome, {})
            default_stats_bot = {
                "resgatado": 0,
                "sorteado_para_recompensa": 0,
                "coracoes_concedidos_recompensa": 0,
                "nome_no_biscoito": 0,
                "sorteado_para_dica": 0,
                "salvo_por_trevo_por_chamado": {},
                "perdido_por_chamado": {}
            }
            personagem_stats_bot.update({k: v for k, v in default_stats_bot.items() if k not in personagem_stats_bot})
            personagem_stats_user = estatisticas_usuarios[user_id]["estatisticas_meus_personagens"].setdefault(personagem_nome, {})
            default_stats_user = {
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
                "receber_nome_loja": 0
            }
            personagem_stats_user.update({k: v for k, v in default_stats_user.items() if k not in personagem_stats_user})

            # Garante que as chaves sejam dicionários antes de usá-las
            for stats in (personagem_stats_bot, personagem_stats_user):
                if not isinstance(stats["salvo_por_trevo_por_chamado"], dict):
                    logger.warning(f"Chave 'salvo_por_trevo_por_chamado' corrompida para {personagem_nome}. Reinicializando.")
                    stats["salvo_por_trevo_por_chamado"] = {}
                if not isinstance(stats["perdido_por_chamado"], dict):
                    logger.warning(f"Chave 'perdido_por_chamado' corrompida para {personagem_nome}. Reinicializando.")
                    stats["perdido_por_chamado"] = {}

            if usar_trevo and user_data["trevo"] > 0:
                user_data["trevo"] -= 1
                user_data["coracao"] += 15
                salvos_por_trevo.setdefault(user_id, []).append(personagem_nome)
                
                estatisticas_bot["ponymemories"]["trevos_consumidos"] += 1
                estatisticas_bot["ponymemories"]["coracoes_concedidos"] += 15
                personagem_stats_bot["salvo_por_trevo_por_chamado"][chamado_por] = personagem_stats_bot["salvo_por_trevo_por_chamado"].get(chamado_por, 0) + 1

                estatisticas_usuarios[user_id]["perdido"]["coracoes_ganhos"] += 15
                personagem_stats_user["salvo_por_trevo_por_chamado"][chamado_por] = personagem_stats_user["salvo_por_trevo_por_chamado"].get(chamado_por, 0) + 1
            else:
                user_chars = personagens_por_usuario.get(user_id, [])
                if user_chars and any(p["nome"] == personagem_nome for p in user_chars):
                    personagens_por_usuario[user_id] = [p for p in user_chars if p["nome"] != personagem_nome]
                
                if any(p["nome"] == personagem_nome for p in personagens_salvos):
                    personagens_salvos[:] = [p for p in personagens_salvos if p["nome"] != personagem_nome]
                
                personagens.append(personagem)
                user_data["coracao"] += 5
                perdidos.append(personagem_nome)
                
                estatisticas_bot["ponymemories"]["coracoes_concedidos"] += 5
                personagem_stats_bot["perdido_por_chamado"][chamado_por] = personagem_stats_bot["perdido_por_chamado"].get(chamado_por, 0) + 1

                estatisticas_usuarios[user_id]["perdido"]["coracoes_ganhos"] += 5
                personagem_stats_user["perdido_por_chamado"][chamado_por] = personagem_stats_user["perdido_por_chamado"].get(chamado_por, 0) + 1

        # Cria a lista de embeds a serem retornados
        embeds = []
        embed_principal = discord.Embed(title="O esquecimento alcançou alguns amigos 🥀", color=cor_chamado)
        if len(perdidos) == 1:
            embed_principal.add_field(name="", value="1 amigo tentando ajudar foi perdido 🥀", inline=False)
        else:
            embed_principal.add_field(name="", value=f"{len(perdidos)} amigos tentando ajudar foram perdidos 🥀", inline=False)
        embed_principal.add_field(name="Seu amor permanece", value="Antes de serem esquecidos, cada amigo deixou 5 corações ❤️", inline=False)
        if perdidos and globals.mostra_nomes_perdidos:
            embed_principal.add_field(name="Amigos Perdidos", value=", ".join(perdidos), inline=False)

        # Trata os campos dos salvos por trevo, criando mais embeds se necessário
        if salvos_por_trevo:
            resumo_salvos = "\n".join(f"<@{uid}>: {', '.join(nomes)}" for uid, nomes in salvos_por_trevo.items())
            max_chars = 1024  # limite de caracteres para o valor de um campo
            # Divide o texto em partes, se necessário
            chunks = [resumo_salvos[i : i + max_chars] for i in range(0, len(resumo_salvos), max_chars)]
            embed_principal.add_field(name="🍀 Sorte mágica 🍀", value=chunks[0], inline=False)
            embed_principal.add_field(name="Recompensa Mágica", value="Os amigos salvos por trevo agradecem com 15 corações", inline=False)
            embeds.append(embed_principal)
            # Se houver mais partes, cria embeds extras
            for idx, chunk in enumerate(chunks[1:], start=2):
                embed_extra = discord.Embed(title="🍀 Sorte mágica (cont.)", color="#800080")
                embed_extra.add_field(name=f"Parte {idx}", value=chunk, inline=False)
                embeds.append(embed_extra)
        else:
            embeds.append(embed_principal)

        # Envio de DM: somente se o parâmetro 'dm' for True
        for user_id, nomes in salvos_por_trevo.items():
            # Garante que o usuário possua a chave 'receber_dm'
            user_settings = usuarios.setdefault(user_id, {"trevo": 0, "coracao": 0, "receber_dm": True})
            if "receber_dm" not in user_settings:
                user_settings["receber_dm"] = True

            if dm and user_settings["receber_dm"]:
                member = guild.get_member(int(user_id))
                if member:
                    mensagem = f"🍀 Estes amigos que você ajudou foram salvos por trevo no servidor **{guild.name}**:\n- " + "\n- ".join(nomes)
                    try:
                        await member.send(mensagem)
                    except discord.Forbidden:
                        logger.warning(f"Não foi possível enviar DM para {user_id}: permissões insuficientes")
                    except Exception as e:
                        logger.error(f"Erro ao enviar DM para {user_id}: {e}")

        try:
            log_relatorio_personagem_perdido(guild_id, chamado_por, "Salvando dados da guild após processamento")
            salvar_dados_guild(guild_id, dados_guild)
            log_relatorio_personagem_perdido(guild_id, chamado_por, "Salvando estatísticas globais da guild após processamento")
            await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
            for user_id, estatisticas in estatisticas_usuarios.items():
                log_relatorio_personagem_perdido(guild_id, chamado_por, f"Salvando estatísticas do usuário {user_id}: tipo {type(estatisticas)}")
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
        except Exception as e:
            logger.error(f"Erro ao salvar dados ou estatísticas para guild {guild_id}: {e}")
            return None

        return embeds



def gerar_resumo_ranking(guild_id: str, bot) -> discord.Embed:
    """
    Gera um embed com o resumo dos 10 usuários mais bem posicionados no ranking de personagens,
    considerando bônus de personagens especiais, com desempate por corações e trevos.
    
    Args:
        guild_id (str): ID da guilda.
        bot: Instância do bot para acessar o cache de usuários.
    
    Returns:
        discord.Embed: Embed com o resumo do ranking.
    """
    dados = carregar_dados_guild(guild_id)
    personagens_por_usuario = dados.get("personagens_por_usuario", {})
    personagens_especiais = dados.get("personagens_especiais", {})
    usuarios = dados.get("usuarios", {})

    if not personagens_por_usuario:
        embed = discord.Embed(
            title="🏆 Resumo do Fim da Jornada",
            description="Nenhum personagem foi resgatado ainda.",
            color=discord.Color.gold()
        )
        return embed

    # Calcula o ranking com bônus e desempates
    ranking_dict = {}
    user_cache = getattr(bot, "user_cache", {})  # Acessa o cache de usuários do bot

    for user_id, personagens in personagens_por_usuario.items():
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
                    break
                elif bonus > max_ranking_bonus:
                    max_ranking_bonus = bonus

        total_ranking = count + max_ranking_bonus
        coracoes = usuarios.get(user_id, {}).get("coracao", 0)
        trevos = usuarios.get(user_id, {}).get("trevo", 0)

        # Obtém o nome do usuário
        if user_id not in user_cache:
            user_obj = bot.get_user(int(user_id))
            if not user_obj:
                try:
                    user_obj = bot.loop.run_until_complete(bot.fetch_user(int(user_id)))
                except Exception:
                    user_obj = f"Usuário {user_id}"
            user_cache[user_id] = user_obj

        user_name = (
            user_cache[user_id].name
            if not isinstance(user_cache[user_id], str)
            else user_cache[user_id]
        )

        # Armazena como tupla para ordenação: (total_ranking, coracoes, trevos, user_info)
        prefix = "🌈" if has_lightly_unicorn else "⭐" if max_ranking_bonus > 0 else ""
        bonus_text = f" (+{max_ranking_bonus})" if max_ranking_bonus > 0 else ""
        ranking_dict[user_id] = (
            total_ranking,
            coracoes,
            trevos,
            f"{prefix}**{user_name}**: {total_ranking} personagem(s){bonus_text} | 💖 {coracoes} | 🍀 {trevos}"
        )

    if not ranking_dict:
        embed = discord.Embed(
            title="🏆 Resumo do Fim da Jornada",
            description="Nenhum personagem foi resgatado ainda.",
            color=discord.Color.gold()
        )
        return embed

    # Ordena pelo total de personagens, depois corações, depois trevos (em ordem decrescente)
    ranking_lista = [
        entry[1][3]  # Extrai apenas a string formatada
        for entry in sorted(ranking_dict.items(), key=lambda x: (x[1][0], x[1][1], x[1][2]), reverse=True)
    ]

    # Pega os top 10 (ou menos, se não houver 10)
    top_10 = ranking_lista[:10]
    ranking_text = "\n".join(f"{i+1}. {entry}" for i, entry in enumerate(top_10))

    # Cria o embed
    embed = discord.Embed(
        title="🏆 Resumo do Fim da Jornada",
        description="Todos os personagens foram resgatados! Aqui um resumo do Ranking:\n\n" + ranking_text,
        color=discord.Color.gold()
    )
    embed.set_footer(text="Obrigado a todos por salvarem os amigos!")
    return embed