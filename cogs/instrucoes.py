import discord
from discord.ext import commands

class InstrucoesView(discord.ui.View):
    def __init__(self, paginas, ctx):
        super().__init__(timeout=120)
        self.paginas = paginas
        self.ctx = ctx
        self.pagina_atual = 0
        self.max_paginas = len(paginas)
    
    async def send_pagina(self, interaction: discord.Interaction = None):
        embed = discord.Embed(
            title=f"📚 Manual do Bot - Página {self.pagina_atual + 1}/{self.max_paginas}",
            description=self.paginas[self.pagina_atual],
            color=discord.Color.blurple()
        )
        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.message = await self.ctx.send(embed=embed, view=self)
    
    @discord.ui.button(label="⏪", style=discord.ButtonStyle.primary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            await self.send_pagina(interaction)
    
    @discord.ui.button(label="⏩", style=discord.ButtonStyle.primary)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.pagina_atual < self.max_paginas - 1:
            self.pagina_atual += 1
            await self.send_pagina(interaction)
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, "message"):
            await self.message.edit(view=self)

class Instrucoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="instrucoes", help="Exibe o manual deste bot e suas principais configurações.")
    async def instrucoes(self, ctx):
        # Defina as páginas do manual
        paginas = [
            "**Página 1: Introdução**\n"
            "Bem-vindo ao Manual do Bot!\n"
            "Este bot foi desenvolvido para gerenciar personagens, enviar dicas, sorte e muito mais.\n"
            "Use os comandos para interagir e explorar as funcionalidades.",

            "**Página 2: Comandos Principais**\n"
            "`!!r` - Resgata um personagem desaparecido.\n"
            "`!!meus` - Exibe os personagens salvos por você.\n"
            "`!!salvos` - Exibe todos os personagens salvos.\n"
            "`!!ranking` - Exibe o ranking de salvadores de personagens.\n"
            "`!!instrucoes` - Exibe este manual.",

            "**Página 3: Configurações**\n"
            "Você pode configurar os canais para dicas e sorte com os comandos:\n"
            "`!!canal dicas` ou `!!canal sorte`.\n"
            "Além disso, os tempos de dicas, impedimento e sorte podem ser ajustados com o comando `!!tempo`.",

            "**Página 4: Comandos Extras**\n"
            "`!!criador` - Mensagem especial do criador.\n"
            "`!!amor` - Envia uma mensagem carinhosa.\n"
            "Use `!!help` para visualizar todos os comandos disponíveis.",

            "**Página 5: Considerações Finais**\n"
            "Lembre-se de seguir as regras do servidor e aproveitar a experiência.\n"
            "Para suporte adicional, entre em contato com os administradores do servidor."
        ]

        view = InstrucoesView(paginas, ctx)
        await view.send_pagina()

async def setup(bot):
    await bot.add_cog(Instrucoes(bot))
