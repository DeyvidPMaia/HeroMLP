# paginacaoPersonagens.py

from discord import Embed, Interaction, ui
import discord
from discord.ext import commands
from discord import Embed

class PaginacaoPersonagens(ui.View):
    def __init__(self, personagens, ctx):
        super().__init__(timeout=60)
        self.personagens = personagens
        self.ctx = ctx
        self.pagina_atual = 0
        self.max_paginas = (len(personagens) - 1) // 25 + 1  # 20 personagens por página 'era 10, se der erro volta todos os 20 pra 10'

    async def send_pagina(self, interaction: Interaction = None):
        inicio = self.pagina_atual * 25
        fim = inicio + 25
        personagens_pagina = self.personagens[inicio:fim]

        # Cria o embed para a página atual
        embed = Embed(
            title=f"🎭 Personagens - Página {self.pagina_atual + 1}/{self.max_paginas}",
            color=0x00ff00,
        )
        embed.description = "\n".join([f"{p['nome']} ({p['especie']})" for p in personagens_pagina])

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.message = await self.ctx.send(embed=embed, view=self)

    @ui.button(label="⏪", style=discord.ButtonStyle.primary)
    async def anterior(self, interaction: Interaction, button: ui.Button):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            await self.send_pagina(interaction)

    @ui.button(label="⏩", style=discord.ButtonStyle.primary)
    async def proximo(self, interaction: Interaction, button: ui.Button):
        if self.pagina_atual < self.max_paginas - 1:
            self.pagina_atual += 1
            await self.send_pagina(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
