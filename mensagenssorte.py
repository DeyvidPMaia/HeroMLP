import discord
import random
import asyncio
import globals
import json
from server_data import carregar_dados_guild  # Certifique-se de que essa função está implementada

class SorteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed = False  # Indica se o biscoito já foi aberto
        self.winner = None    # Guarda o usuário que abriu o biscoito

    @discord.ui.button(label="Abrir Biscoito da Sorte", style=discord.ButtonStyle.primary, custom_id="sorte_button")
    async def abrir_sorte(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.claimed:
            # Se já foi aberto, informa ao usuário que já foi reclamado
            await interaction.response.send_message("Esse biscoito já foi aberto por outro usuário.", ephemeral=True)
        else:
            self.claimed = True
            self.winner = interaction.user

            # Carrega as sortes diretamente do arquivo
            sortes = carregar_sortes()
            sorte_msg = random.choice(sortes["sortes"]) if "sortes" in sortes else "Não há mensagem de sorte disponível no momento."

            # Carrega os dados da guild para obter os personagens
            dados = carregar_dados_guild(interaction.guild.id)
            # Extrai os nomes dos personagens já salvos
            saved_names = {p["nome"] for p in dados.get("personagens_salvos", [])}
            # Filtra os personagens que ainda não foram salvos
            unsaved = [p for p in dados.get("personagens", []) if p.get("nome") not in saved_names]

            if unsaved:
                personagem = random.choice(unsaved)
                personagem_msg = f"\n**{personagem['nome']}** é um personagem ainda não salvo."
            else:
                personagem_msg = f"\nTodos os personagens já foram salvos!"

            # Desabilita o botão para que ninguém mais possa abrir o biscoito
            button.disabled = True
            await interaction.response.send_message(
                f"✨ Seu biscoito da sorte diz:\n*{sorte_msg}*{personagem_msg}",
                ephemeral=True
            )
            # Atualiza a mensagem pública para refletir que o biscoito foi aberto
            await interaction.message.edit(view=self)

async def enviar_sorte_automatico(bot, guild_id):
    """
    Envia automaticamente o biscoito da sorte a cada intervalo definido no JSON do servidor.
    """
    while True:
        # Carrega os dados específicos do servidor
        dados = carregar_dados_guild(guild_id)
        # Obtém o tempo de sorte do JSON ou usa o valor padrão em globals
        tempo_sorte = dados.get("tempo_sorte", globals.tempo_sorte)
        await asyncio.sleep(tempo_sorte + int(tempo_sorte / 4))
        
        canal_id = dados.get("ID_DO_CANAL_SORTE")
        if canal_id is None:
            print(f"[SORTE] Canal para sorte não configurado na guild {guild_id}. Pulando envio.")
            continue

        canal = bot.get_channel(canal_id)
        if canal is None:
            print(f"[SORTE] Canal com ID {canal_id} não encontrado na guild {guild_id}.")
            continue

        # Cria o embed com a mensagem do biscoito da sorte
        embed = discord.Embed(
            title="🍪 Biscoito da Sorte",
            description="Clique no botão para abrir o biscoito da sorte.\n*Apenas clicar receberá uma mensagem!*",
            color=discord.Color.purple()
        )
        view = SorteView()
        await canal.send(embed=embed, view=view)

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
