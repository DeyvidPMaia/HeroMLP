import discord
from discord.ext import commands
from funcoes import maintenance_off

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
    @maintenance_off()
    async def instrucoes(self, ctx):
        # Defina as páginas do manual
        paginas = [
            "**Página 1: Introdução**\n"
            "Bem-vindo ao Manual do PonyMemories! Este bot foi desenvolvido para resgatar personagens do esquecimento e proporcionar uma experiência interativa e divertida. Use os comandos para explorar todas as funcionalidades disponíveis.",

            "**Página 2: Comandos de Resgate e Visualização**\n"
            "- `!!r` - Resgata um personagem desaparecido.\n"
            "- `!!meus` - Exibe seus personagens salvos ou changelings.\n"
            "- `!!salvos` - Exibe todos os personagens salvos.\n"
            "- `!!exibir` - Exibe um personagem seu. Administradores podem exibir qualquer personagem.\n"
            "- `!!ranking` - Exibe o ranking de salvadores de personagens.",

            "**Página 3: Conquistas**\n"
            "- `!!conquistas` - Lista todas as conquistas disponíveis.\n"
            "- `!!conquistei` - Exibe suas conquistas atuais.\n"
            "As conquistas são desbloqueadas ao completar objetivos específicos, como resgatar certos personagens ou grupos deles.",

            "**Página 4: Troca de Personagens**\n"
            "- `!!trocar <ID ou @usuário>` - Inicia um processo interativo para trocar personagens com outro usuário.\n"
            "  - Escolha seu personagem e o personagem do outro usuário usando reações.\n"
            "  - Ambos devem confirmar a troca.",

            "**Página 5: Loja**\n"
            "- `!!loja` - Exibe a loja para comprar itens usando corações.\n"
            "  - Reaja com emojis para selecionar e comprar itens.\n"
            "- `!!loja <nome_item>` - Compra um item diretamente com confirmação por reação.",

            "**Página 6: Configurações**\n"
            "- `!!canal dicas` - Configura o canal para dicas.\n"
            "- `!!canal sorte` - Configura o canal para o biscoito da sorte.\n"
            "- `!!tempo` - Ajusta os tempos de dicas, impedimento e sorte.",

            "**Página 7: Comandos Extras**\n"
            "- `!!criador` - Exibe uma mensagem especial do criador.\n"
            "- `!!amor` - Envia uma mensagem carinhosa.\n"
            "- `!!help` - Exibe todos os comandos disponíveis.",

            "**Página 9: Considerações Finais**\n"
            "Lembre-se de seguir as regras do servidor e aproveitar a experiência. Para suporte adicional, entre em contato com os administradores do servidor."
        ]

        view = InstrucoesView(paginas, ctx)
        await view.send_pagina()

async def setup(bot):
    await bot.add_cog(Instrucoes(bot))