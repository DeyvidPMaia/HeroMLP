# biscoitosorte.py 22/03/2025 16:30 (renomeado recompensas_recebidas para recompensas_recebidas_biscoito_sorte no usuário)

import discord
import random
import time
import json
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_guild, salvar_estatisticas_seguro, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario
import globals

def carregar_sortes():
    """
    Carrega as sortes a partir do arquivo resources/sortesbr/sortesbr.json.
    Retorna:
        dict: Dicionário com as mensagens de sorte.
    """
    caminho = "resources/sortesbr/sortesbr.json"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar sortes: {e}")
        return {}

class SorteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed = False  # Indica se o biscoito já foi aberto
        self.winner = None    # Guarda o usuário que abriu o biscoito

    @discord.ui.button(label="Abrir Biscoito da Sorte", style=discord.ButtonStyle.primary, custom_id="sorte_button")
    async def abrir_sorte(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.claimed:
            await interaction.response.send_message("Esse biscoito já foi aberto por outro usuário.", ephemeral=True)
            return

        self.claimed = True
        self.winner = interaction.user

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        # Carrega as estatísticas do bot
        estatisticas_bot = carregar_estatisticas_guild(guild_id)
        bot_default = {
            "biscoitos_enviados_por": {},
            "recompensas_enviadas_biscoito_sorte": {}
        }
        if "ponymemories" not in estatisticas_bot:
            estatisticas_bot["ponymemories"] = bot_default
        else:
            if not isinstance(estatisticas_bot["ponymemories"].get("recompensas_enviadas_biscoito_sorte"), dict):
                estatisticas_bot["ponymemories"]["recompensas_enviadas_biscoito_sorte"] = {}
            estatisticas_bot["ponymemories"] = {**bot_default, **estatisticas_bot["ponymemories"]}
        estatisticas_bot.setdefault("estatisticas_meus_personagens", {})

        # Carrega as estatísticas do usuário
        estatisticas_usuario = carregar_estatisticas_usuario(guild_id, user_id)
        usuario_default = {
            "biscoitos_abertos": 0,
            "recompensas_recebidas_biscoito_sorte": {},
            "coracoes_ganhos": 0
        }
        if "sorte" not in estatisticas_usuario:
            estatisticas_usuario["sorte"] = usuario_default
        else:
            if not isinstance(estatisticas_usuario["sorte"].get("recompensas_recebidas_biscoito_sorte"), dict):
                estatisticas_usuario["sorte"]["recompensas_recebidas_biscoito_sorte"] = {}
            estatisticas_usuario["sorte"] = {**usuario_default, **estatisticas_usuario["sorte"]}
        estatisticas_usuario.setdefault("estatisticas_meus_personagens", {})

        # Incrementa biscoitos abertos pelo usuário
        estatisticas_usuario["sorte"]["biscoitos_abertos"] += 1

        # Carrega as sortes do arquivo
        sortes = carregar_sortes()
        sorte_msg = random.choice(sortes["sortes"]) if "sortes" in sortes else "Não há mensagem de sorte disponível no momento."

        # Carrega os dados da guild
        dados = carregar_dados_guild(guild_id)

        # Escolhe aleatoriamente entre três opções
        opcao = random.choice(["personagem", "cooldown", "hearts"])
        resultado = ""
        recompensa_tipo = ""

        if opcao == "personagem":
            saved_names = {p["nome"] for p in dados.get("personagens_salvos", [])}
            unsaved = [p for p in dados.get("personagens", []) if p.get("nome") not in saved_names]
            if unsaved:
                personagem = random.choice(unsaved)
                personagem_nome = personagem["nome"]
                resultado = f"\n**{personagem_nome}** é um personagem ainda não salvo."
                recompensa_tipo = "personagem"
                personagem_stats_bot = estatisticas_bot["estatisticas_meus_personagens"].setdefault(personagem_nome, {
                    "resgatado": 0,
                    "sorteado_para_recompensa": 0,
                    "coracoes_concedidos_recompensa": 0,
                    "nome_no_biscoito": 0
                })
                personagem_stats_bot["nome_no_biscoito"] += 1
                personagem_stats_usuario = estatisticas_usuario["estatisticas_meus_personagens"].setdefault(personagem_nome, {
                    "resgatado": 0,
                    "enviado": 0,
                    "recebido": 0,
                    "exibido": 0,
                    "uso_como_changeling_conquista": 0,
                    "sorteado_para_recompensa": 0,
                    "coracoes_concedidos_recompensa": 0,
                    "nome_no_biscoito": 0
                })
                personagem_stats_usuario["nome_no_biscoito"] += 1
            else:
                resultado = "\nTodos os personagens já foram salvos! Você recebeu 5 coração(es)!"
                recompensa_tipo = "hearts_personagens_salvos"
                if "usuarios" not in dados:
                    dados["usuarios"] = {}
                usuarios = dados["usuarios"]
                user_data = usuarios.get(user_id, {"coracao": 0, "quantidade_amor": 0})
                user_data["coracao"] += 5
                usuarios[user_id] = user_data
                dados["usuarios"] = usuarios
                estatisticas_usuario["sorte"]["coracoes_ganhos"] += 5
                salvar_dados_guild(guild_id, dados)

        elif opcao == "cooldown":
            tempo_impedimento = dados.get("tempo_impedimento", globals.tempo_impedimento)
            if "ultimo_resgate_por_usuario" not in dados:
                dados["ultimo_resgate_por_usuario"] = {}
            ultimo = dados["ultimo_resgate_por_usuario"].get(user_id)
            current_time = time.time()
            if ultimo is None:
                remaining = 0
            else:
                elapsed = current_time - ultimo
                remaining = max(tempo_impedimento - elapsed, 0)

            if remaining == 0:
                if "usuarios" not in dados:
                    dados["usuarios"] = {}
                usuarios = dados["usuarios"]
                user_data = usuarios.get(user_id, {"coracao": 0, "quantidade_amor": 0})
                user_data["coracao"] += 10
                usuarios[user_id] = user_data
                dados["usuarios"] = usuarios
                resultado = "\nVocê já podia resgatar, então recebeu 10 coração(es)!"
                recompensa_tipo = "hearts_cooldown_zero"
                estatisticas_usuario["sorte"]["coracoes_ganhos"] += 10
                salvar_dados_guild(guild_id, dados)
            else:
                opcoes = ["reset", "quarter", "half"]
                escolha = random.choice(opcoes)
                if escolha == "reset":
                    novos_valor = current_time - tempo_impedimento
                    resultado = "\nSeu tempo de impedimento foi zerado!"
                    recompensa_tipo = "cooldown_reset"
                elif escolha == "quarter":
                    novo_remaining = remaining * 0.75
                    novos_valor = current_time - (tempo_impedimento - novo_remaining)
                    resultado = "\nSeu tempo de impedimento foi reduzido em 25%!"
                    recompensa_tipo = "cooldown_quarter"
                else:  # escolha == "half"
                    novo_remaining = remaining * 0.5
                    novos_valor = current_time - (tempo_impedimento - novo_remaining)
                    resultado = "\nSeu tempo de impedimento foi reduzido pela metade!"
                    recompensa_tipo = "cooldown_half"
                dados["ultimo_resgate_por_usuario"][user_id] = novos_valor
                salvar_dados_guild(guild_id, dados)
        else:  # opcao == "hearts"
            hearts_awarded = random.randint(10, 15)
            if "usuarios" not in dados:
                dados["usuarios"] = {}
            usuarios = dados["usuarios"]
            user_data = usuarios.get(user_id, {"coracao": 0, "quantidade_amor": 0})
            user_data["coracao"] += hearts_awarded
            usuarios[user_id] = user_data
            dados["usuarios"] = usuarios
            salvar_dados_guild(guild_id, dados)
            resultado = f"\nVocê recebeu {hearts_awarded} coração(es)!"
            recompensa_tipo = "hearts_random"
            estatisticas_usuario["sorte"]["coracoes_ganhos"] += hearts_awarded

        # Atualiza recompensas enviadas (bot) e recebidas (usuário)
        estatisticas_bot["ponymemories"]["recompensas_enviadas_biscoito_sorte"].setdefault(recompensa_tipo, 0)
        estatisticas_bot["ponymemories"]["recompensas_enviadas_biscoito_sorte"][recompensa_tipo] += 1
        estatisticas_usuario["sorte"]["recompensas_recebidas_biscoito_sorte"].setdefault(recompensa_tipo, 0)
        estatisticas_usuario["sorte"]["recompensas_recebidas_biscoito_sorte"][recompensa_tipo] += 1

        button.disabled = True
        await interaction.response.send_message(
            f"✨ Seu biscoito da sorte diz:\n*{sorte_msg}*{resultado}",
            ephemeral=True
        )
        embed = discord.Embed(
            title="🍪 Biscoito da Sorte",
            description=f"Este biscoito foi aberto por {interaction.user.mention}!",
            color=discord.Color.purple()
        )
        await interaction.message.edit(embed=embed, view=self)

        # Salva as estatísticas
        await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_usuario)

async def biscoito_sorte(channel, enviado_por):
    """
    Envia um biscoito da sorte diretamente no canal especificado.
    """
    guild_id = str(channel.guild.id)

    # Carrega as estatísticas do bot
    estatisticas_bot = carregar_estatisticas_guild(guild_id)
    bot_default = {
        "biscoitos_enviados_por": {},
        "recompensas_enviadas_biscoito_sorte": {}
    }
    if "ponymemories" not in estatisticas_bot:
        estatisticas_bot["ponymemories"] = bot_default
    else:
        if not isinstance(estatisticas_bot["ponymemories"].get("recompensas_enviadas_biscoito_sorte"), dict):
            estatisticas_bot["ponymemories"]["recompensas_enviadas_biscoito_sorte"] = {}
        estatisticas_bot["ponymemories"] = {**bot_default, **estatisticas_bot["ponymemories"]}
    estatisticas_bot.setdefault("estatisticas_meus_personagens", {})

    # Incrementa biscoitos enviados por enviado_por
    estatisticas_bot["ponymemories"]["biscoitos_enviados_por"].setdefault(enviado_por, 0)
    estatisticas_bot["ponymemories"]["biscoitos_enviados_por"][enviado_por] += 1

    embed = discord.Embed(
        title="🍪 Biscoito da Sorte",
        description="Clique no botão para abrir o biscoito da sorte.\n*Apenas uma pessoa pode abrir e receber uma mensagem!*",
        color=discord.Color.purple()
    )
    view = SorteView()
    await channel.send(embed=embed, view=view)

    # Salva as estatísticas do bot
    await salvar_estatisticas_seguro(guild_id, estatisticas_bot)