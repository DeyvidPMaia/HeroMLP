import discord
import random
import asyncio
import globals
import json

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

            # Carrega sortes diretamente do arquivo
            sortes = carregar_sortes()
            sorte_msg = random.choice(sortes["sortes"]) if "sortes" in sortes else "Não há mensagem de sorte disponível no momento."

            # Desabilita o botão para que ninguém mais possa abrir o biscoito
            button.disabled = True
            await interaction.response.send_message(f"✨ Seu biscoito da sorte diz:\n*{sorte_msg}*", ephemeral=True)
            # Atualiza a mensagem pública para refletir que o biscoito foi aberto
            await interaction.message.edit(view=self)

async def enviar_sorte_automatico(bot):
    """
    Envia automaticamente o biscoito da sorte a cada intervalo definido por globals.tempo_sorte.
    A cada envio, o canal é buscado usando globals.ID_DO_CANAL_DICAS.
    """
    while True:
        await asyncio.sleep(globals.tempo_sorte + int(globals.tempo_sorte / 4))  # Espera o tempo definido para sorte
        # Verifica se o canal de sorte está configurado
        if globals.ID_DO_CANAL_SORTE is None:
            print("Canal para sorte não configurado. Pulando envio.")
            continue

        canal = bot.get_channel(globals.ID_DO_CANAL_SORTE)
        if canal is None:
            print(f"Canal com ID {globals.ID_DO_CANAL_SORTE} não encontrado.")
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
