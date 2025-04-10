# resgatar.py 26/03/2025 16:00 (corrigido para busca parcial, personagem perdido)

import discord
from discord.ext import commands
import time
from utils import gerar_resumo_ranking
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario, carregar_estatisticas_guild, salvar_estatisticas_seguro, evento_esquecimento
from funcoes import verificar_imagem, sortear_naoencontrado, maintenance_off, no_dm, normalize, sanitize_filename
from PIL import Image
from io import BytesIO
import asyncio
import logging
import random
import os

logger = logging.getLogger(__name__)

# Dicionário global de locks por guilda para dados compartilhados
guild_locks = {}

def get_guild_lock(guild_id: str) -> asyncio.Lock:
    if guild_id not in guild_locks:
        guild_locks[guild_id] = asyncio.Lock()
    return guild_locks[guild_id]

class Resgatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Lista de strings comuns que exigem correspondência exata se usadas sozinhas e letras a mais se com outros caracteres
        self.common_strings = [
            "apple",
            "pple",
            "appl",
            "princess",
            "rincess",
            "incess",
            "ncess",
            "princes",
            "prince",
            "seapony",
            "eapony",
            "apony",
            "pony",
            "eg",
            "g5",
            "g4",
            "shadow",
            "cake",
            "fyreheart",
            "fyre",
            "très",
            "tres",
            "mare",
            "night"
        ]
        self.quantidade_letras_exigidas = 6

    async def _salvar_dados(self, guild_id: str, dados: dict, ctx) -> bool:
        """Tenta salvar os dados da guild e envia uma mensagem de erro caso falhe."""
        try:
            salvar_dados_guild(guild_id, dados)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados da guild {guild_id}: {e}")
            await ctx.send("❌ **Erro ao salvar os dados do servidor.**")
            return False

    def _check_cooldown(self, dados: dict, user_id: str, agora: float, tempo_bloqueio: int) -> (bool, str):
        """Verifica se o usuário já resgatou recentemente."""
        if dados.get("restricao_usuario_unico", True) and user_id in dados.get("ultimo_resgate_por_usuario", {}):
            tempo_passado = agora - dados["ultimo_resgate_por_usuario"][user_id]
            if tempo_passado < tempo_bloqueio:
                tempo_restante = int(tempo_bloqueio - tempo_passado)
                minutos = tempo_restante // 60
                segundos = tempo_restante % 60
                mensagem = f"❌ **Você deve esperar {minutos} minuto(s) e {segundos} segundo(s) para resgatar outro personagem.**"
                return False, mensagem
        return True, ""

    def _check_ultimo_salvador(self, dados: dict, user_id: str) -> bool:
        """Verifica se o usuário foi o último a resgatar."""
        if dados.get("restricao_usuario_unico", False) and dados.get("ultimo_usuario_salvador") == user_id:
            return False
        return True

    def _create_error_embed(self, description: str, image_path: str = None) -> discord.Embed:
        """Cria um embed de erro padronizado."""
        embed = discord.Embed(description=description, color=discord.Color.red())
        if image_path:
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
        return embed

    def _calcular_similaridade(self, digitado: str, alvo: str) -> float:
        """Calcula a similaridade entre o nome digitado e o nome do personagem."""
        digitado_set = set(digitado)
        alvo_set = set(alvo)
        intersecao = len(digitado_set & alvo_set)
        uniao = len(digitado_set | alvo_set)
        jaccard = intersecao / uniao if uniao > 0 else 0
        # Penaliza diferenças grandes no comprimento
        diff_comprimento = abs(len(digitado) - len(alvo)) / max(len(digitado), len(alvo))
        return jaccard * (1 - diff_comprimento)


    @commands.command(name="r", help="Salva um personagem desaparecido.")
    @evento_esquecimento()
    @no_dm()
    @maintenance_off()
    async def resgatar(self, ctx, *, nome):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Validação inicial do argumento 'nome' (normalizado apenas para busca)
        nome_normalizado = normalize(nome.strip())
        if not nome_normalizado:
            embed = self._create_error_embed("❌ **Por favor, insira o nome de um personagem para salvar.**")
            await ctx.send(embed=embed)
            return

        lock = get_guild_lock(guild_id)
        async with lock:
            # Carrega os dados da guilda
            try:
                dados = carregar_dados_guild(guild_id)
            except Exception as e:
                logger.error(f"Erro ao carregar dados da guild {guild_id}: {e}")
                await ctx.send("❌ **Erro ao carregar os dados do servidor.**")
                return

            # Carrega e inicializa estatísticas do usuário
            estatisticas_usuario = carregar_estatisticas_usuario(guild_id, user_id)
            usuario_default = {
                "uso_comando_resgatar": 0,
                "resgates_tentados_resgatar": 0,
                "resgates_concluidos_resgatar": 0,
                "falhas_1_porcento_resgatar": 0,
                "coracoes_ganhos_resgatar": 0,
                "tentativas_em_cooldown_resgatar": 0,
                "bloqueios_ultimo_salvador_resgatar": 0,
                "tentativas_personagem_ja_resgatado_resgatar": 0,
                "tentativas_personagem_nao_encontrado_resgatar": 0,
                "tentativas_com_personagens_escondidos_resgatar": 0
            }
            if "resgatar" not in estatisticas_usuario:
                estatisticas_usuario["resgatar"] = usuario_default
            else:
                estatisticas_usuario["resgatar"] = {**usuario_default, **estatisticas_usuario["resgatar"]}
            estatisticas_usuario.setdefault("estatisticas_meus_personagens", {})

            # Carrega e inicializa estatísticas globais do bot
            estatisticas_bot = carregar_estatisticas_guild(guild_id)
            bot_default = {
                "resgates_totais_guild": 0,
                "resgates_tentados": 0,
                "resgates_concluidos": 0,
                "falhas_1_porcento": 0,
                "coracoes_ganhos_r": 0,
                "tentativas_em_cooldown": 0,
                "bloqueios_ultimo_salvador": 0,
                "tentativas_personagem_ja_resgatado": 0,
                "tentativas_personagem_nao_encontrado": 0,
                "tentativas_com_personagens_escondidos": 0
            }
            if "resgatar_bot" not in estatisticas_bot:
                estatisticas_bot["resgatar_bot"] = bot_default
            else:
                estatisticas_bot["resgatar_bot"] = {**bot_default, **estatisticas_bot["resgatar_bot"]}
            estatisticas_bot.setdefault("estatisticas_meus_personagens", {})

            # Incrementa o uso do comando e tentativas (usuário e bot)
            estatisticas_usuario["resgatar"]["uso_comando_resgatar"] += 1
            estatisticas_usuario["resgatar"]["resgates_tentados_resgatar"] += 1
            estatisticas_bot["resgatar_bot"]["resgates_tentados"] += 1
            logger.debug(f"Estatísticas para {user_id} em {guild_id}: {estatisticas_usuario}")

            # Garante que as chaves necessárias existam em dados
            dados.setdefault("ultimo_resgate_por_usuario", {})
            if "ultimo_usuario_salvador" not in dados:
                dados["ultimo_usuario_salvador"] = None
            if "restricao_usuario_unico" not in dados:
                dados["restricao_usuario_unico"] = True

            tempo_bloqueio = dados.get("tempo_impedimento", 300)
            agora = time.time()

            # Verifica o cooldown do usuário
            ok_cooldown, msg_cooldown = self._check_cooldown(dados, user_id, agora, tempo_bloqueio)
            if not ok_cooldown:
                estatisticas_usuario["resgatar"]["tentativas_em_cooldown_resgatar"] += 1
                estatisticas_bot["resgatar_bot"]["tentativas_em_cooldown"] += 1
                embed = self._create_error_embed(msg_cooldown)
                await ctx.send(embed=embed)
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                return

            # Verifica se há personagens disponíveis para resgatar
            personagens_disponiveis = dados.get("personagens", [])
            personagens_escondidos = dados.get("personagem_escondido", [])
            if not personagens_disponiveis and personagens_escondidos:
                embed = self._create_error_embed(f"Há {len(personagens_escondidos)} personagem(ns) escondidos ainda esperando para ser(em) salvo(s).")
                await ctx.send(embed=embed)
                estatisticas_usuario["resgatar"]["tentativas_com_personagens_escondidos_resgatar"] += 1
                estatisticas_bot["resgatar_bot"]["tentativas_com_personagens_escondidos"] += 1
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                return
            elif not personagens_disponiveis and not personagens_escondidos:
                embed = self._create_error_embed("❌ **Todos os amigos estão a salvo agora! Obrigado.**", "resources/fim.png")
                await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/fim.png")))
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                return

            # Verifica a restrição de usuário único
            if not self._check_ultimo_salvador(dados, user_id):
                estatisticas_usuario["resgatar"]["bloqueios_ultimo_salvador_resgatar"] += 1
                estatisticas_bot["resgatar_bot"]["bloqueios_ultimo_salvador"] += 1
                embed = self._create_error_embed("❌ **Você foi o último a salvar um personagem. Espere que mais alguém salve outro personagem!**", "resources/ultimosalvador.png")
                await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/ultimosalvador.png")))
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                return

            # Verifica se o personagem já foi resgatado (usando nome normalizado apenas para busca)
            personagens_salvos = {normalize(p["nome"]): p for p in dados.get("personagens_salvos", [])}
            if nome_normalizado in personagens_salvos:
                estatisticas_usuario["resgatar"]["tentativas_personagem_ja_resgatado_resgatar"] += 1
                estatisticas_bot["resgatar_bot"]["tentativas_personagem_ja_resgatado"] += 1
                embed = self._create_error_embed(f"❌ **O personagem '{nome}' já foi resgatado!**", "resources/jaresgatado.jpg")
                await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/jaresgatado.jpg")))
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                return

            # Procura o personagem na lista de disponíveis (usando nome normalizado apenas para busca)
            personagens_disponiveis_dict = {normalize(p["nome"]): p for p in personagens_disponiveis}
            personagem = personagens_disponiveis_dict.get(nome_normalizado)

            # Busca parcial ajustada
            if not personagem:
                is_exact_common_string = nome_normalizado in self.common_strings
                contains_common = any(common in nome_normalizado for common in self.common_strings)

                candidatos = []
                if is_exact_common_string:
                    pass  # Busca exata já foi feita
                elif contains_common:
                    for common in self.common_strings:
                        if common in nome_normalizado:
                            common_length = len(common)
                            additional_length = len(nome_normalizado) - common_length
                            if additional_length >= self.quantidade_letras_exigidas:
                                for p_nome, p in personagens_disponiveis_dict.items():
                                    if nome_normalizado in p_nome:
                                        similaridade = self._calcular_similaridade(nome_normalizado, p_nome)
                                        candidatos.append((similaridade, p))
                                break
                else:
                    if len(nome_normalizado) >= 5:
                        for p_nome, p in personagens_disponiveis_dict.items():
                            if nome_normalizado in p_nome:
                                similaridade = self._calcular_similaridade(nome_normalizado, p_nome)
                                candidatos.append((similaridade, p))

                if candidatos:
                    # Ordena por similaridade decrescente e pega o mais similar
                    candidatos.sort(key=lambda x: x[0], reverse=True)
                    personagem = candidatos[0][1]  # Pega o personagem com maior similaridade

            if personagem:
                # Chance de falha de 1%
                if random.random() < 0.01:
                    dados["ultimo_resgate_por_usuario"][user_id] = agora
                    dados["ultimo_usuario_salvador"] = user_id
                    embed = self._create_error_embed("❌ Você tentou ajudar, mas não pode resgatar ninguém desta vez.")
                    await ctx.send(embed=embed)
                    estatisticas_usuario["resgatar"]["falhas_1_porcento_resgatar"] += 1
                    estatisticas_bot["resgatar_bot"]["falhas_1_porcento"] += 1
                    await self._salvar_dados(guild_id, dados, ctx)
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                    await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                    return

                # Remove o personagem da lista de disponíveis e adiciona aos salvos
                try:
                    dados["personagens"].remove(personagem)
                except ValueError as e:
                    logger.error(f"Erro ao remover personagem: {e}")
                    await ctx.send("❌ **Erro ao processar o personagem. Tente novamente.**")
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                    await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                    return

                dados.setdefault("personagens_salvos", []).append(personagem)
                dados["ultimo_usuario_salvador"] = user_id
                dados.setdefault("personagens_por_usuario", {}).setdefault(user_id, []).append(personagem)
                dados["ultimo_resgate_por_usuario"][user_id] = agora

                # Atualiza os dados de amor do usuário
                usuarios = dados.setdefault("usuarios", {})
                user_data = usuarios.setdefault(user_id, {"coracao": 0, "quantidade_amor": 0})
                # Inicializa o campo "resgatou_personagem" se não existir
                if "resgatou_personagem" not in user_data:
                    user_data["resgatou_personagem"] = False
                coracoes_ganhos_r = 5
                user_data["coracao"] += coracoes_ganhos_r

                # Se for o primeiro personagem resgatado, marca o campo como True
                if not user_data["resgatou_personagem"]:
                    user_data["resgatou_personagem"] = True

                user_data["quantidade_amor"] = 0
                coracoes_ganhos_r = 5
                user_data["coracao"] += coracoes_ganhos_r

                # Atualiza estatísticas do usuário (nome original)
                estatisticas_usuario["resgatar"]["resgates_concluidos_resgatar"] += 1
                personagem_nome = personagem["nome"]  # Usa o nome original de todospersonagens.json
                
                chaves_iniciais = {
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

                estatisticas_personagem_usuario = estatisticas_usuario["estatisticas_meus_personagens"].setdefault(personagem_nome, {})
                estatisticas_personagem_usuario.update({k: v for k, v in chaves_iniciais.items() if k not in estatisticas_personagem_usuario})
                estatisticas_usuario["estatisticas_meus_personagens"][personagem_nome]["resgatado"] += 1
                estatisticas_usuario["resgatar"]["coracoes_ganhos_resgatar"] += coracoes_ganhos_r

                # Atualiza estatísticas globais do bot ("resgatar_bot")
                estatisticas_personagem_bot = estatisticas_bot["estatisticas_meus_personagens"].setdefault(personagem_nome, {})
                estatisticas_personagem_bot.update({k: v for k, v in chaves_iniciais.items() if k not in estatisticas_personagem_bot })

                estatisticas_bot["resgatar_bot"]["resgates_totais_guild"] += 1
                estatisticas_bot["resgatar_bot"]["resgates_concluidos"] += 1
                estatisticas_bot["resgatar_bot"]["coracoes_ganhos_r"] += coracoes_ganhos_r
                estatisticas_bot["estatisticas_meus_personagens"].setdefault(personagem_nome, {"resgatado": 0})
                estatisticas_bot["estatisticas_meus_personagens"][personagem_nome]["resgatado"] += 1

                # Processa a imagem do personagem
                imagem_path = f"resources/poneis/{personagem['nome']}.png"
                try:
                    imagem = verificar_imagem(imagem_path)
                except Exception as e:
                    logger.error(f"Erro ao processar imagem para {personagem['nome']}: {e}")
                    await ctx.send("❌ **Erro ao processar a imagem do personagem.**")
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                    await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                    return

                # Sanitiza o nome para o arquivo e embed
                nome_imagem = sanitize_filename(personagem['nome'])
                embed = discord.Embed(
                    title=f"✅ **'{personagem['nome']}' foi salvo!**",
                    description=f"**{ctx.author.name}** resgatou o personagem '{personagem['nome']}' com sucesso!",
                    color=discord.Color.green()
                )
                embed.set_image(url=f"attachment://{nome_imagem}.png")
                try:
                    await ctx.send(embed=embed, file=discord.File(imagem, f"{nome_imagem}.png"))
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem para {personagem['nome']}: {e}")
                    await ctx.send("❌ **Erro ao enviar a mensagem de sucesso.**")
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                    await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                    return

                # Verifica se todos os personagens de "personagens" foram resgatados
                if not dados.get("personagens"):
                    personagens_escondidos = dados.get("personagem_escondido", [])
                    quantidade_personagens_escondido = len(personagens_escondidos)
                    
                    if quantidade_personagens_escondido > 0:
                        # Exibe mensagem sobre personagens escondidos
                        embed_escondidos = discord.Embed(
                            description=f"Há ainda {quantidade_personagens_escondido} personagem(ns) escondidos esperando para ser(em) salvo(s).",
                            color=discord.Color.orange()
                        )
                        await ctx.send(embed=embed_escondidos)
                        estatisticas_usuario["resgatar"]["tentativas_com_personagens_escondidos_resgatar"] += 1
                        estatisticas_bot["resgatar_bot"]["tentativas_com_personagens_escondidos"] += 1
                    elif quantidade_personagens_escondido == 0:
                        # Exibe mensagem final com imagem se todos foram salvos
                        embed_final = discord.Embed(
                            description=f"🎉 **'{personagem['nome']}' foi o último amigo salvo! Todos estão seguros agora!** 🎉",
                            color=discord.Color.gold()
                        )
                        embed_final.set_image(url="attachment://fim.png")
                        await ctx.send(embed=embed_final, file=discord.File(verificar_imagem("resources/fim.png")))

                await self._salvar_dados(guild_id, dados, ctx)
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                await salvar_estatisticas_seguro(guild_id, estatisticas_bot)

                # Após salvar, verifica se deve mostrar o resumo
                dados = carregar_dados_guild(guild_id)
                if not dados.get("personagens") and not dados.get("personagem_escondido", []):
                    if dados.get("mostrar_resumo", True):
                        embed_resumo = gerar_resumo_ranking(guild_id, self.bot)
                        await ctx.send(embed=embed_resumo)
                        dados["mostrar_resumo"] = False  # Desativa para não mostrar novamente
                        await self._salvar_dados(guild_id, dados, ctx)  # Salva novamente para atualizar o mostrar_resumo


            else:
                estatisticas_usuario["resgatar"]["tentativas_personagem_nao_encontrado_resgatar"] += 1
                estatisticas_bot["resgatar_bot"]["tentativas_personagem_nao_encontrado"] += 1
                naoencontrado = sortear_naoencontrado()
                embed = self._create_error_embed(f"❌ **O personagem '{nome}' não foi encontrado!**", naoencontrado)
                try:
                    await ctx.send(embed=embed, file=discord.File(naoencontrado))
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem de personagem não encontrado: {e}")
                    await ctx.send("❌ **Erro ao enviar mensagem de personagem não encontrado.**")
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)
                await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
                return

async def setup(bot):
    await bot.add_cog(Resgatar(bot))