#paginacaoPersonagens.py

from discord import Embed, Interaction, ui
import discord
from discord.ext import commands

class PaginacaoPersonagens(ui.View):
    def __init__(self, personagens, ctx, page_size=25):
        super().__init__(timeout=60)
        self.personagens = personagens
        self.ctx = ctx
        self.page_size = page_size
        self.pagina_atual = 0
        # Garante que haja pelo menos uma página, mesmo que a lista esteja vazia
        if len(personagens) == 0:
            self.max_paginas = 1
        else:
            self.max_paginas = (len(personagens) - 1) // self.page_size + 1

    async def send_pagina(self, interaction: Interaction = None):
        # Atualiza os estados dos botões conforme a página atual
        self._update_buttons()

        inicio = self.pagina_atual * self.page_size
        fim = inicio + self.page_size
        personagens_pagina = self.personagens[inicio:fim]

        # Cria o embed para a página atual
        embed = Embed(
            title=f"🎭 Personagens - Página {self.pagina_atual + 1}/{self.max_paginas}",
            color=0x00ff00,
        )
        if personagens_pagina:
            embed.description = "\n".join([f"{p['nome']} ({p['especie']})" for p in personagens_pagina])
        else:
            embed.description = "Nenhum personagem encontrado."

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.message = await self.ctx.send(embed=embed, view=self)

    def _update_buttons(self):
        # Atualiza o estado dos botões conforme a página atual
        self.anterior.disabled = self.pagina_atual <= 0
        self.proximo.disabled = self.pagina_atual >= self.max_paginas - 1

    @ui.button(label="⏪", style=discord.ButtonStyle.primary)
    async def anterior(self, interaction: Interaction, button: ui.Button):
        # Permite apenas o usuário que iniciou a paginação utilizar o botão
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Apenas o usuário que iniciou a paginação pode navegar.", ephemeral=True)
            return

        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            await self.send_pagina(interaction)

    @ui.button(label="⏩", style=discord.ButtonStyle.primary)
    async def proximo(self, interaction: Interaction, button: ui.Button):
        # Permite apenas o usuário que iniciou a paginação utilizar o botão
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Apenas o usuário que iniciou a paginação pode navegar.", ephemeral=True)
            return

        if self.pagina_atual < self.max_paginas - 1:
            self.pagina_atual += 1
            await self.send_pagina(interaction)

    async def on_timeout(self):
        # Ao expirar o tempo de interação, desabilita todos os botões
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass
