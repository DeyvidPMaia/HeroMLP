import discord
from discord.ext import commands

class HistoriaView(discord.ui.View):
    def __init__(self, pages: list):
        super().__init__(timeout=None)
        self.pages = pages
        self.current = 0

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current > 0:
            self.current -= 1
            await interaction.response.edit_message(embed=self.pages[self.current], view=self)
        else:
            # Confirma a interação se já estiver na primeira página
            await interaction.response.defer()

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.secondary)
    async def proxima(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current < len(self.pages) - 1:
            self.current += 1
            await interaction.response.edit_message(embed=self.pages[self.current], view=self)
        else:
            # Confirma a interação se já estiver na última página
            await interaction.response.defer()

class HistoriaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="historia", 
        help="Exibe a lore deste Bot."
    )
    async def historia(self, ctx: commands.Context):
        pages = []

        # Para todas as páginas, usamos o mesmo arquivo como imagem de fundo:
        image_url = "attachment://folha.png"

        # Página 1
        embed1 = discord.Embed(
            title="História do Bot - Capítulo I: O Despertar",
            description=(
                "Em tempos antigos, uma magia esquecida e sombria começou a se agitar, "
                "despertando de seu sono milenar."
            ),
            color=discord.Color.dark_blue()
        )
        embed1.set_footer(text="Página 1/10")
        embed1.set_image(url=image_url)
        pages.append(embed1)

        # Página 2
        embed2 = discord.Embed(
            title="História do Bot - Capítulo II: A Magia Maligna",
            description=(
                "Essa magia não era comum: sua essência era maligna e contaminava "
                "tudo ao seu redor com um poder obscuro."
            ),
            color=discord.Color.dark_purple()
        )
        embed2.set_footer(text="Página 2/10")
        embed2.set_image(url=image_url)
        pages.append(embed2)

        # Página 3
        embed3 = discord.Embed(
            title="História do Bot - Capítulo III: O Esquecimento",
            description=(
                "Conforme a magia se espalhava, ela trouxe um esquecimento devastador. "
                "Lembranças começaram a desaparecer, mergulhando Equestria em um vazio profundo."
            ),
            color=discord.Color.blurple()
        )
        embed3.set_footer(text="Página 3/10")
        embed3.set_image(url=image_url)
        pages.append(embed3)

        # Página 4
        embed4 = discord.Embed(
            title="História do Bot - Capítulo IV: O Preço da Memória",
            description=(
                "Os amigos de Equestria, antes cheios de vida e lembranças, começaram a ser esquecidos. "
                "Com o esquecimento, suas existências se desvaneciam lentamente."
            ),
            color=discord.Color.dark_gold()
        )
        embed4.set_footer(text="Página 4/10")
        embed4.set_image(url=image_url)
        pages.append(embed4)

        # Página 5
        embed5 = discord.Embed(
            title="História do Bot - Capítulo V: A Escuridão se Aproxima",
            description=(
                "O mundo se tornou um lugar sombrio, onde a ausência de memória ameaçava apagar para sempre "
                "os rostos e nomes queridos."
            ),
            color=discord.Color.from_rgb(50, 50, 50)
        )
        embed5.set_footer(text="Página 5/10")
        embed5.set_image(url=image_url)
        pages.append(embed5)

        # Página 6
        embed6 = discord.Embed(
            title="História do Bot - Capítulo VI: Um Sussurro de Esperança",
            description=(
                "Em meio à escuridão, rumores começaram a circular: existia um meio de resgatar "
                "aqueles que estavam se perdendo na névoa do esquecimento."
            ),
            color=discord.Color.green()
        )
        embed6.set_footer(text="Página 6/10")
        embed6.set_image(url=image_url)
        pages.append(embed6)

        # Página 7
        embed7 = discord.Embed(
            title="História do Bot - Capítulo VII: O Chamado para o Resgate",
            description=(
                "Dizia-se que um comando poderoso, o `!!r`, possuía a capacidade de reverter "
                "o esquecimento e restaurar as lembranças perdidas."
            ),
            color=discord.Color.teal()
        )
        embed7.set_footer(text="Página 7/10")
        embed7.set_image(url=image_url)
        pages.append(embed7)

        # Página 8
        embed8 = discord.Embed(
            title="História do Bot - Capítulo VIII: Desafios na Jornada",
            description=(
                "Mas a magia antiga não se renderia facilmente. Cada resgate enfrentava desafios, "
                "pois o esquecimento era uma força implacável."
            ),
            color=discord.Color.orange()
        )
        embed8.set_footer(text="Página 8/10")
        embed8.set_image(url=image_url)
        pages.append(embed8)

        # Página 9
        embed9 = discord.Embed(
            title="História do Bot - Capítulo IX: A Batalha Contra o Esquecimento",
            description=(
                "Heróis e guardiões se uniram para lutar contra a escuridão, determinados a preservar "
                "as memórias e a existência dos que ainda restavam."
            ),
            color=discord.Color.red()
        )
        embed9.set_footer(text="Página 9/10")
        embed9.set_image(url=image_url)
        pages.append(embed9)

        # Página 10
        embed10 = discord.Embed(
            title="História do Bot - Capítulo X: O Convite para o Resgate",
            description=(
                "A responsabilidade está em suas mãos! Use o comando `!!r` e ajude a restaurar "
                "os amigos de Equestria antes que sejam apagados para sempre."
            ),
            color=discord.Color.purple()
        )
        embed10.set_footer(text="Página 10/10")
        embed10.set_image(url=image_url)
        pages.append(embed10)

        view = HistoriaView(pages)
        # Envia o primeiro embed junto com o arquivo folha.png
        await ctx.send(embed=pages[0], view=view, file=discord.File("resources/folha.png", filename="folha.png"))

async def setup(bot: commands.Bot):
    await bot.add_cog(HistoriaCog(bot))
