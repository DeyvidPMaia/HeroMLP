# exibir.py 23/03/2025 00:10 (atualizado para reações persistentes com dados_recompensa_exibir.json, ajustado para botões silenciosos)

import discord
from discord import Embed, File
from discord.ext import commands
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario, carregar_dados_recompensa_exibir, salvar_dados_recompensa_exibir_seguro, evento_esquecimento
import os
from io import BytesIO
import logging
from funcoes import maintenance_off, no_dm
import json
import asyncio
import time
from PIL import Image, ImageOps, ImageEnhance
from views import ExibirViewBotoes, HeartButton, ButterflyButton, TrashButton
from funcoes import normalize

reacoes_requeridas = 8

logger = logging.getLogger(__name__)

def is_moderator(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or (discord.utils.get(member.roles, name="MagoMLP") is not None)

"""def normalize(name: str) -> str:
    return "".join(name.lower().split())"""

def get_cooldown_status(personagem: dict) -> str:
    current_time = time.time()
    ultima_exibicao = personagem.get("recompensa_exibir", 0)
    if current_time - ultima_exibicao < 86400:
        remaining = 86400 - (current_time - ultima_exibicao)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        return f"Disponível em {hours}h {minutes}m {seconds}s"
    return f"{reacoes_requeridas} amigos clicando no coração concede uma recompensa"

def is_on_cooldown(personagem: dict) -> bool:
    current_time = time.time()
    ultima_exibicao = personagem.get("recompensa_exibir", 0)
    return current_time - ultima_exibicao < 86400

def get_recompensa_corações(quantidade_recompensa: int) -> int:
    if quantidade_recompensa < 5:
        return 5
    elif quantidade_recompensa < 10:
        return 4
    elif quantidade_recompensa < 15:
        return 3
    elif quantidade_recompensa < 20:
        return 2
    else:
        return 1

class Exibir(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_exhibits = {}  # {user_id: {nome_personagem: discord.Message}}

    def is_transformed(self, changeling) -> bool:
        if isinstance(changeling, str):
            nome = changeling
        elif isinstance(changeling, dict):
            nome = changeling.get("nome", "")
        else:
            return False
        if nome.startswith("cha"):
            suffix = nome[3:]
            return not suffix.isdigit()
        return False

    def get_changeling_name(self, changeling):
        if isinstance(changeling, str):
            return changeling
        elif isinstance(changeling, dict):
            return changeling.get("nome", "")
        return ""

    def carregar_descricoes(self):
        caminho = "resources/descricoes.json"
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar descrições: {e}")
            return {}

    async def disable_previous_exhibit(self, user_id: str, nome_personagem: str):
        if user_id in self.active_exhibits and nome_personagem in self.active_exhibits[user_id]:
            previous_message = self.active_exhibits[user_id][nome_personagem]
            try:
                view = previous_message.components[0] if previous_message.components else ExibirViewBotoes(timeout=None, mode="normal")
                view.disable_all()
                await previous_message.edit(view=view)
                logger.info(f"Exibição anterior de {nome_personagem} por {user_id} desativada.")
            except discord.errors.NotFound:
                logger.warning(f"Mensagem anterior de {nome_personagem} por {user_id} não encontrada.")
            except Exception as e:
                logger.error(f"Erro ao desativar exibição anterior de {nome_personagem} por {user_id}: {e}")
            del self.active_exhibits[user_id][nome_personagem]
            if not self.active_exhibits[user_id]:
                del self.active_exhibits[user_id]

    @commands.command(name="exibir", help="Exibe um personagem salvo ou um changeling o imitado.\nUso: !!exibir <nome_do_personagem> ou !!exibir changelings")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    async def exibir(self, ctx, *, nome_personagem: str = None):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Dicionário padrão para estatísticas de personagens
        estatisticas_personagem_padrao = {
            "resgatado": 0, "enviado": 0, "recebido": 0, "exibido": 0,
            "uso_como_changeling_conquista": 0, "sorteado_para_recompensa": 0,
            "coracoes_concedidos_recompensa": 0, "nome_no_biscoito": 0,
            "salvo_por_trevo_por_chamado": {}, "perdido_por_chamado": {},
            "receber_nome_loja": 0
        }

        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        estatisticas.setdefault("estatisticas_meus_personagens", {})
        estatisticas.setdefault("exibir", {})
        chaves_iniciais = {
            "uso_comando_exibir": 0,
            "exibicoes_reais_exibir": 0,
            "exibicoes_falsas_exibir": 0,
            "recompensas_recebidas_exibir": 0,
            "coracoes_ganhos_exibir": 0,
            "transformacoes_changeling_exibir": 0,
            "remocoes_changeling_exibir": 0,
        }
        for chave, valor in chaves_iniciais.items():
            estatisticas["exibir"].setdefault(chave, valor)
            
        estatisticas["exibir"]["uso_comando_exibir"] += 1

        if not nome_personagem:
            await ctx.send("❌ **Você precisa informar o nome do personagem ou 'changelings'.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        nome_normalizado = normalize(nome_personagem)
        dados = carregar_dados_guild(guild_id)
        usuarios = dados.setdefault("usuarios", {})
        user_data = usuarios.setdefault(user_id, {"coracao": 0, "quantidade_amor": 0, "trevo": 0, "changeling": [], "quantidade_recompensa": 0, "ultimo_reset_recompensa": 0})

        personagens_especiais = dados.setdefault("personagens_especiais", {
            "Lightly Unicorn": {"recompensa": 25, "copiavel": False},
            "Fyreheart Flare": {"recompensa": 10, "copiavel": True},
            "Fyreheart Flare Seapony": {"recompensa": 15, "copiavel": True},
            "Lauren Faust": {"recompensa": 10, "copiavel": True},
            "Starlight Glimmer": {"recompensa": 10, "copiavel": True}
        })

        if nome_normalizado == "changelings":
            changelings = user_data.get("changeling", [])
            if not changelings:
                await ctx.send("❌ **Você não possui changelings.**")
            else:
                total = len(changelings)
                transformed = sum(1 for c in changelings if self.is_transformed(c))
                details = "Detalhes dos seus changelings:\n"
                for ch in changelings:
                    nome_ch = self.get_changeling_name(ch)
                    especie = ch.get("especie", "Desconhecida") if isinstance(ch, dict) else "Desconhecida"
                    if self.is_transformed(ch):
                        details += f"- {nome_ch}: imitando {nome_ch[3:]} (Espécie: {especie})\n"
                    else:
                        details += f"- {nome_ch}: default (Espécie: {especie})\n"
                await ctx.send(f"Você possui {total} changelings, dos quais {transformed} já foram transformados.\n{details}")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        personagens_usuario = {normalize(p.get("nome", "")): p for p in dados.get("personagens_por_usuario", {}).get(user_id, [])}
        changelings = user_data.get("changeling", [])
        changelings_transformados = {normalize(self.get_changeling_name(ch)[3:]): ch for ch in changelings if self.is_transformed(ch)}

        personagem = personagens_usuario.get(nome_normalizado)
        changeling = None
        nome_original = None

        if not personagem:
            for ch_nome, ch in changelings_transformados.items():
                if nome_normalizado in ch_nome:
                    changeling = ch
                    nome_original = self.get_changeling_name(ch)[3:]
                    break
            if not changeling:
                for p_nome, p in personagens_usuario.items():
                    if nome_normalizado in p_nome:
                        personagem = p
                        nome_original = p["nome"]
                        break
        else:
            nome_original = personagem["nome"]
        
        # Inicializa estatísticas do personagem apenas se não existir
        #estatisticas["estatisticas_meus_personagens"].setdefault(nome_original, estatisticas_personagem_padrao.copy()) /remover esta linha
        inicializar_chaves_personagem = estatisticas["estatisticas_meus_personagens"].setdefault(nome_original, {})
        inicializar_chaves_personagem.update({k: v for k, v in estatisticas_personagem_padrao.items() if k not in inicializar_chaves_personagem})

        if is_moderator(ctx.author):
            if not personagem and not changeling:
                lista_global = {normalize(p.get("nome", "")): p for p in dados.get("personagens", []) + dados.get("personagens_salvos", [])}
                personagem = lista_global.get(nome_normalizado)
                if not personagem:
                    for p_nome, p in lista_global.items():
                        if nome_normalizado in p_nome:
                            personagem = p
                            nome_original = p["nome"]
                            break
                if not personagem:
                    await ctx.send("❌ **Personagem não encontrado.**")
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
                    return
            admin_owns = nome_original in [p["nome"] for p in dados.get("personagens_por_usuario", {}).get(user_id, [])]
        


            if changeling and not personagem:
                estatisticas["exibir"]["exibicoes_falsas_exibir"] += 1
                estatisticas["estatisticas_meus_personagens"][nome_original]["exibido"] += 1
                await self.exibir_fake(ctx, nome_original)
            elif not admin_owns:
                await self.exibir_real(ctx, personagem, reward_override="Gerenciador, você não possui esse personagem", monitor_buttons=False)
            else:
                reward_status = get_cooldown_status(personagem)
                estatisticas["exibir"]["exibicoes_reais_exibir"] += 1
                estatisticas["estatisticas_meus_personagens"][nome_original]["exibido"] += 1
                await self.exibir_real(ctx, personagem, reward_override=None if reward_status == f"{reacoes_requeridas} amigos clicando no coração concede uma recompensa" else reward_status)
        else:
            if not personagem and not changeling:
                await ctx.send("❌ **Você não possui esse personagem ou um changeling correspondente.**")
            else:
                # Inicializa estatísticas do personagem apenas se não existir
                estatisticas["estatisticas_meus_personagens"].setdefault(nome_original, estatisticas_personagem_padrao.copy())
                
                if changeling:
                    estatisticas["exibir"]["exibicoes_falsas_exibir"] += 1
                    estatisticas["estatisticas_meus_personagens"][nome_original]["exibido"] += 1
                    await self.exibir_fake(ctx, nome_original)
                elif personagem:
                    estatisticas["exibir"]["exibicoes_reais_exibir"] += 1
                    estatisticas["estatisticas_meus_personagens"][nome_original]["exibido"] += 1
                    await self.exibir_real(ctx, personagem)
        
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

    async def check_ownership_loop(self, guild_id: str, user_id: str, nome_personagem: str, view: discord.ui.View, message: discord.Message):
        """Verifica continuamente se o personagem ainda pertence ao usuário."""
        while True:
            # Carrega os dados mais recentes da guild
            dados = carregar_dados_guild(guild_id)
            personagens_usuario = dados.get("personagens_por_usuario", {}).get(user_id, [])
            personagem_possuido = any(p["nome"] == nome_personagem for p in personagens_usuario)

            # Se o usuário não possui mais o personagem, desativa os botões e encerra
            if not personagem_possuido:
                try:
                    view.disable_all()
                    await message.edit(view=view)
                    logger.info(f"Personagem '{nome_personagem}' não pertence mais a {user_id}. Monitoramento desativado.")
                    if user_id in self.active_exhibits and nome_personagem in self.active_exhibits[user_id]:
                        del self.active_exhibits[user_id][nome_personagem]
                        if not self.active_exhibits[user_id]:
                            del self.active_exhibits[user_id]
                    break
                except Exception as e:
                    logger.error(f"Erro ao desativar exibição de {nome_personagem} para {user_id}: {e}")
                    break

            # Verifica se a view ainda está ativa (timeout ou recompensa concedida)
            if view.is_finished():
                break

            # Aguarda 5 segundos antes da próxima verificação
            await asyncio.sleep(5)

    async def exibir_real(self, ctx, personagem: dict, reward_override: str = None, monitor_buttons: bool = True):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        caminho_imagem = os.path.join("resources", "poneis", f"{personagem['nome']}.png")
        if not os.path.exists(caminho_imagem):
            caminho_imagem = os.path.join("resources", "poneis", "semimagem.png")
            if not os.path.exists(caminho_imagem):
                await ctx.send(f"❌ **Imagem do personagem '{personagem['nome']}' não encontrada.**")
                return

        try:
            with open(caminho_imagem, "rb") as f:
                imagem_bytes = f.read()
        except Exception as e:
            logger.error(f"Erro ao ler a imagem {caminho_imagem}: {e}")
            return

        dados = carregar_dados_guild(guild_id)
        especiais = dados.get("personagens_especiais", {})
        eh_especial = personagem["nome"] in especiais
        reward_status = reward_override or get_cooldown_status(personagem)
        em_cooldown = is_on_cooldown(personagem)

        # Carrega os dados persistentes de cliques no coração
        dados_recompensa = carregar_dados_recompensa_exibir(guild_id)
        cliques = dados_recompensa.get(personagem["nome"], [])

        # Configura o status da recompensa
        if eh_especial:
            recompensa_fixa = especiais[personagem["nome"]]["recompensa"]
            if reward_status == f"{reacoes_requeridas} amigos clicando no coração concede uma recompensa" and not reward_override:
                reward_status = f"{recompensa_fixa} corações com {reacoes_requeridas} ajudas"
        else:
            if reward_status == f"{reacoes_requeridas} amigos clicando no coração concede uma recompensa" and not reward_override:
                user_data = dados["usuarios"][user_id]
                current_time = time.time()
                ultimo_reset = user_data.get("ultimo_reset_recompensa", 0)
                if current_time - ultimo_reset >= 86400:
                    user_data["quantidade_recompensa"] = 0
                    user_data["ultimo_reset_recompensa"] = current_time
                    salvar_dados_guild(guild_id, dados)
                coracoes_ganhos = get_recompensa_corações(user_data.get("quantidade_recompensa", 0))
                reward_status = f"{coracoes_ganhos} corações com {reacoes_requeridas} ajudas"

        descricoes = self.carregar_descricoes()
        descricao = descricoes.get(personagem["nome"], "Sem descrição.")
        embed = discord.Embed(title=personagem["nome"], color=discord.Color.blue())
        embed.add_field(name="Descrição", value=descricao, inline=False)
        embed.add_field(name="Recompensa", value=reward_status, inline=False)
        embed.set_footer(text=personagem.get("especie", "Desconhecida"))
        embed.set_image(url="attachment://imagem.png")
        message = await ctx.send(embed=embed, file=discord.File(fp=BytesIO(imagem_bytes), filename="imagem.png"))

        if monitor_buttons:
            await self.disable_previous_exhibit(user_id, personagem["nome"])
            
            view = ExibirViewBotoes(
                heart_callback=None,
                butterfly_callback=None,
                timeout=15*60,
                mode="normal"
            )
            for item in view.children:
                if isinstance(item, HeartButton):
                    item.disabled = em_cooldown
                    if not em_cooldown:
                        item.label = f"{len(cliques)}/{reacoes_requeridas}"  # Reflete o número persistente de cliques
                        item.callback_func = self._heart_callback_factory(ctx, personagem, user_id, view, message)
                elif isinstance(item, ButterflyButton):
                    item.callback_func = self._butterfly_callback_factory(ctx, personagem, user_id, view)
            
            # Armazena a mensagem na view
            view.message = message
            await message.edit(view=view)

            if user_id not in self.active_exhibits:
                self.active_exhibits[user_id] = {}
            self.active_exhibits[user_id][personagem["nome"]] = message

            # Chama a função assíncrona de verificação de posse
            asyncio.create_task(self.check_ownership_loop(guild_id, user_id, personagem["nome"], view, message))

    def _heart_callback_factory(self, ctx, personagem, author_id, view: discord.ui.View, message: discord.Message):
        async def heart_callback(interaction: discord.Interaction):
            if interaction.user.id == int(author_id):
                await interaction.response.defer()  # Silenciosamente ignora a interação do autor
                return

            guild_id = str(ctx.guild.id)
            user_id_inter = str(interaction.user.id)
            dados_recompensa = carregar_dados_recompensa_exibir(guild_id)
            cliques = dados_recompensa.get(personagem["nome"], [])

            if user_id_inter not in cliques:
                cliques.append(user_id_inter)
                dados_recompensa[personagem["nome"]] = cliques
                await salvar_dados_recompensa_exibir_seguro(guild_id, dados_recompensa)

                # Atualiza o label do botão de coração
                for item in view.children:
                    if isinstance(item, HeartButton):
                        item.label = f"{len(cliques)}/{reacoes_requeridas}"
                        break
                
                # Edita a mensagem apenas com a view atualizada
                await message.edit(view=view)
                await interaction.response.defer()  # Confirma a interação sem resposta visível

                required_reactions = reacoes_requeridas
                if len(cliques) >= required_reactions:
                    dados = carregar_dados_guild(guild_id)
                    usuarios = dados["usuarios"]
                    usuario = usuarios[author_id]
                    current_time = time.time()
                    ultimo_reset = usuario.get("ultimo_reset_recompensa", 0)
                    if current_time - ultimo_reset >= 86400:
                        usuario["quantidade_recompensa"] = 0
                        usuario["ultimo_reset_recompensa"] = current_time
                    especiais = dados.get("personagens_especiais", {})
                    eh_especial = personagem["nome"] in especiais
                    if eh_especial:
                        coracoes_ganhos = especiais[personagem["nome"]]["recompensa"]
                    else:
                        usuario["quantidade_recompensa"] = usuario.get("quantidade_recompensa", 0) + 1
                        coracoes_ganhos = get_recompensa_corações(usuario["quantidade_recompensa"])
                    usuario["coracao"] = usuario.get("coracao", 0) + coracoes_ganhos
                    for p in dados["personagens_por_usuario"][author_id]:
                        if p["nome"] == personagem["nome"]:
                            p["recompensa_exibir"] = time.time()
                            break
                    salvar_dados_guild(guild_id, dados)
                    
                    # Limpa a lista de cliques após a recompensa
                    dados_recompensa[personagem["nome"]] = []
                    await salvar_dados_recompensa_exibir_seguro(guild_id, dados_recompensa)
                    
                    estatisticas = carregar_estatisticas_usuario(guild_id, author_id)
                    estatisticas["exibir"]["recompensas_recebidas_exibir"] += 1
                    estatisticas["exibir"]["coracoes_ganhos_exibir"] += coracoes_ganhos
                    await salvar_estatisticas_seguro_usuario(guild_id, author_id, estatisticas)
                    
                    await interaction.followup.send(f"🎉 Parabéns {ctx.author.mention}! Você ganhou {coracoes_ganhos} corações por ostentar {personagem['nome']}!", ephemeral=False)
                    view.disable_all()
                    await message.edit(view=view)
                    if author_id in self.active_exhibits and personagem["nome"] in self.active_exhibits[author_id]:
                        del self.active_exhibits[author_id][personagem["nome"]]
                        if not self.active_exhibits[author_id]:
                            del self.active_exhibits[author_id]
            else:
                await interaction.response.defer()  # Silenciosamente ignora interação repetida
        return heart_callback

    def _butterfly_callback_factory(self, ctx, personagem, author_id, view: discord.ui.View):
        async def butterfly_callback(interaction: discord.Interaction):
            if interaction.user.id == int(author_id):
                await interaction.response.send_message("Você não pode transformar changelings no seu próprio personagem.", ephemeral=True)
                return
            guild_id = str(ctx.guild.id)
            dados = carregar_dados_guild(guild_id)
            usuarios = dados["usuarios"]
            user_id_inter = str(interaction.user.id)
            user_data = usuarios.setdefault(user_id_inter, {"changeling": [], "coracao": 0, "quantidade_amor": 0, "trevo": 0, "quantidade_recompensa": 0, "ultimo_reset_recompensa": 0})
            changelings = user_data["changeling"]
            for idx, ch in enumerate(changelings):
                if not self.is_transformed(ch):
                    changelings[idx] = {"nome": f"cha{personagem['nome']}", "especie": personagem.get("especie", "Desconhecida")}
                    salvar_dados_guild(guild_id, dados)
                    estatisticas = carregar_estatisticas_usuario(guild_id, user_id_inter)
                    estatisticas.setdefault("exibir", {"transformacoes_changeling_exibir": 0})
                    estatisticas["exibir"]["transformacoes_changeling_exibir"] += 1
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id_inter, estatisticas)
                    await interaction.response.send_message(f"{interaction.user.mention} Seu changeling foi transformado para imitar {personagem['nome']}!", ephemeral=False)
                    return
            await interaction.response.send_message("Você não possui um changeling disponível para transformação.", ephemeral=True)
        return butterfly_callback

    async def exibir_fake(self, ctx, nome_personagem: str):
        guild_id = str(ctx.guild.id)
        caminho_imagem = os.path.join("resources", "poneis", f"{nome_personagem}.png")
        if not os.path.exists(caminho_imagem):
            caminho_imagem = os.path.join("resources", "poneis", "semimagem.png")
            if not os.path.exists(caminho_imagem):
                await ctx.send(f"❌ **Imagem do personagem '{nome_personagem}' não encontrada para exibição fake.**")
                return

        try:
            with Image.open(caminho_imagem) as img:
                img_mirrored = ImageOps.mirror(img.convert("RGB"))
                enhancer = ImageEnhance.Brightness(img_mirrored)
                img_processada = enhancer.enhance(0.8)
                img_byte_arr = BytesIO()
                img_processada.save(img_byte_arr, format="PNG")
                img_byte_arr.seek(0)
        except Exception as e:
            logger.error(f"Erro ao processar imagem para exibição fake: {e}")
            return

        embed = Embed(title=f"{nome_personagem}?", color=discord.Color.dark_gray())
        embed.set_image(url="attachment://fake.png")
        message = await ctx.send(embed=embed, file=File(fp=img_byte_arr, filename="fake.png"))
        view = ExibirViewBotoes(
            trash_callback=None,
            timeout=5*60,
            mode="changelings"
        )
        for item in view.children:
            if isinstance(item, TrashButton):
                item.callback_func = self._trash_callback_factory(ctx, nome_personagem, view)
        await message.edit(view=view)

    def _trash_callback_factory(self, ctx, nome_personagem: str, view: discord.ui.View):
        async def trash_callback(interaction: discord.Interaction):
            user_id = str(ctx.author.id)
            guild_id = str(ctx.guild.id)
            
            # Verifica se o usuário que clicou é o autor do comando
            if interaction.user.id != int(user_id):
                await interaction.response.send_message("❌ **Apenas o dono deste changeling pode removê-lo.**", ephemeral=True)
                return

            dados = carregar_dados_guild(guild_id)
            changelings = dados["usuarios"].get(user_id, {}).get("changeling", [])
            changeling_key = f"cha{nome_personagem}"
            
            # Remove apenas o primeiro changeling com o nome correspondente
            for idx, ch in enumerate(changelings):
                nome_ch = self.get_changeling_name(ch)
                if nome_ch == changeling_key:
                    changelings.pop(idx)  # Remove apenas este changeling
                    salvar_dados_guild(guild_id, dados)
                    estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
                    estatisticas.setdefault("exibir", {"remocoes_changeling_exibir": 0})
                    estatisticas["exibir"]["remocoes_changeling_exibir"] += 1
                    await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
                    view.disable_all()
                    await interaction.response.edit_message(view=view)
                    await interaction.followup.send(f"<@{user_id}> Seu changeling imitando {nome_personagem} foi removido.", ephemeral=False)
                    return
            
            await interaction.response.send_message("❌ **Nenhum changeling correspondente encontrado para exclusão.**", ephemeral=True)
        return trash_callback

async def setup(bot):
    await bot.add_cog(Exibir(bot))