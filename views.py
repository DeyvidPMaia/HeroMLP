# views.py - Classes genéricas para botões reutilizáveis (ajustado para múltiplas seleções contínuas)
import discord
from discord.ui import Button, View

class PaginatedSelectionView(View):
    def __init__(self, ctx, user, items, title, description, color, items_per_page=10):
        super().__init__(timeout=None)  # Timeout gerenciado pelo loja.py
        self.ctx = ctx
        self.user = user
        self.items = items
        self.title = title
        self.description = description
        self.color = color
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page
        self.result = None
        self.add_buttons()

    def add_buttons(self):
        self.clear_items()
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.items))
        
        for i, item in enumerate(self.items[start:end], start=1):
            button = Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"select_{i-1 + start}")
            button.callback = self.select_callback
            self.add_item(button)

        if self.total_pages > 1:
            prev_button = Button(label="◀️ Anterior", style=discord.ButtonStyle.secondary, custom_id="prev", disabled=self.current_page == 0)
            prev_button.callback = self.prev_callback
            self.add_item(prev_button)

            next_button = Button(label="Próximo ▶️", style=discord.ButtonStyle.secondary, custom_id="next", disabled=self.current_page == self.total_pages - 1)
            next_button.callback = self.next_callback
            self.add_item(next_button)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Apenas o usuário que iniciou a seleção pode escolher.", ephemeral=True)
            return
        idx = int(interaction.data["custom_id"].split("_")[1])
        self.result = self.items[idx]
        await interaction.response.defer()  # Apenas reconhece a interação, sem editar ainda

    async def prev_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Apenas o usuário que iniciou a seleção pode navegar.", ephemeral=True)
            return
        self.current_page -= 1
        await self.update_message(interaction)

    async def next_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Apenas o usuário que iniciou a seleção pode navegar.", ephemeral=True)
            return
        self.current_page += 1
        await self.update_message(interaction)

    async def update_message(self, interaction):
        embed = self.get_embed()
        self.add_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_embed(self):
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.items))
        lista = "\n".join([f"**{i + 1}. {item['nome']}** ({item['especie']})" 
                           for i, item in enumerate(self.items[start:end])])
        embed = discord.Embed(
            title=self.title,
            description=f"{self.user.mention}, {self.description}\n\n{lista}\n\nPágina {self.current_page + 1}/{self.total_pages}",
            color=self.color
        )
        return embed

class ConfirmationView(View):
    def __init__(self, ctx, users, title, description, color):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.users = users
        self.confirmations = set()
        self.cancelled = False
        self.title = title
        self.description = description
        self.color = color
        self.add_buttons()

    def add_buttons(self):
        accept_button = Button(label="Aceitar", style=discord.ButtonStyle.success, custom_id="accept")
        accept_button.callback = self.accept_callback
        self.add_item(accept_button)

        cancel_button = Button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="cancel")
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)

    async def accept_callback(self, interaction: discord.Interaction):
        if interaction.user not in self.users:
            await interaction.response.send_message("Apenas os usuários envolvidos podem interagir.", ephemeral=True)
            return
        self.confirmations.add(interaction.user)
        if len(self.confirmations) == len(self.users):
            self.stop()
        await interaction.response.edit_message(content=f"{interaction.user.name} aceitou!", embed=self.get_embed(), view=self)

    async def cancel_callback(self, interaction: discord.Interaction):
        if interaction.user not in self.users:
            await interaction.response.send_message("Apenas os usuários envolvidos podem interagir.", ephemeral=True)
            return
        self.cancelled = True
        self.stop()
        await interaction.response.edit_message(content=f"❌ Cancelado por {interaction.user.name}.", embed=None, view=None)

    def get_embed(self):
        return discord.Embed(title=self.title, description=self.description, color=self.color)

    async def on_timeout(self):
        await self.ctx.send("⏰ Tempo de confirmação expirado. Operação cancelada.")
        self.cancelled = True
        self.stop()


class PaginatedView(View):
    def __init__(self, ctx, user, items, title, description, color, items_per_page=10):
        super().__init__(timeout=60.0)  # Timeout de 60 segundos
        self.ctx = ctx
        self.user = user
        self.items = items
        self.title = title
        self.description = description
        self.color = color
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page
        self.message = None  # Para armazenar a mensagem enviada
        self.add_buttons()

    def add_buttons(self):
        self.clear_items()
        if self.total_pages > 1:
            # Botão para a primeira página
            first_button = Button(label="⏮️", style=discord.ButtonStyle.secondary, custom_id="first", disabled=self.current_page == 0)
            first_button.callback = self.first_callback
            self.add_item(first_button)
            
            # Botão para página anterior
            prev_button = Button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="prev", disabled=self.current_page == 0)
            prev_button.callback = self.prev_callback
            self.add_item(prev_button)
            
            # Botão para próxima página
            next_button = Button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="next", disabled=self.current_page == self.total_pages - 1)
            next_button.callback = self.next_callback
            self.add_item(next_button)
            
            # Botão para a última página
            last_button = Button(label="⏭️", style=discord.ButtonStyle.secondary, custom_id="last", disabled=self.current_page == self.total_pages - 1)
            last_button.callback = self.last_callback
            self.add_item(last_button)

    async def first_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Apenas o usuário que iniciou a visualização pode navegar.", ephemeral=True)
            return
        self.current_page = 0
        await self.update_message(interaction)

    async def last_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Apenas o usuário que iniciou a visualização pode navegar.", ephemeral=True)
            return
        self.current_page = self.total_pages - 1
        await self.update_message(interaction)

    async def prev_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Apenas o usuário que iniciou a visualização pode navegar.", ephemeral=True)
            return
        self.current_page -= 1
        await self.update_message(interaction)

    async def next_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Apenas o usuário que iniciou a visualização pode navegar.", ephemeral=True)
            return
        self.current_page += 1
        await self.update_message(interaction)

    async def update_message(self, interaction):
        embed = self.get_embed()
        self.add_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_embed(self):
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.items))
        lista = "\n".join(self.items[start:end])
        embed = discord.Embed(
            title=self.title,
            description=f"{self.description}\n\n{lista}\n\nPágina {self.current_page + 1}/{self.total_pages}",
            color=self.color
        )
        return embed

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)
        else:
            await self.ctx.send("⏰ Tempo de navegação expirado.")


class ExibirViewBotoes(discord.ui.View):
    def __init__(
        self,
        *,
        heart_callback=None,
        butterfly_callback=None,
        trash_callback=None,
        timeout: int = 300,
        mode: str = "normal"  # pode ser "normal", "changelings" ou "manager"
    ):
        """
        :param heart_callback: Função assíncrona chamada quando o botão de coração é clicado.
        :param butterfly_callback: Função assíncrona chamada quando o botão de borboleta é clicado.
        :param trash_callback: Função assíncrona chamada quando o botão de lixeira (changelings) é clicado.
        :param timeout: Tempo (em segundos) até expirar a view.
        :param mode: Modo de exibição da view ("normal", "changelings", "manager").
        """
        super().__init__(timeout=timeout)
        self.unique_heart_users = set()
        self.heart_callback = heart_callback
        self.butterfly_callback = butterfly_callback
        self.trash_callback = trash_callback
        self.mode = mode
        self.message = None  # Adicionado para armazenar a mensagem

        # Botões padrão para todos os modos:
        if self.mode == "normal":
            self.add_item(HeartButton(callback_func=self.heart_callback))
            self.add_item(ButterflyButton(callback_func=self.butterfly_callback))
            self.add_item(PlanetButton())
            self.add_item(NotepadButton())

        # Botão extra para exibição de changelings (exclusão) 
        if self.mode == "changelings":
            self.add_item(TrashButton(callback_func=self.trash_callback))
        # Botão extra para gerenciadores (ação negativa, por enquanto desabilitado)
        if self.mode == "manager":
            self.add_item(NegativeButton())

    def disable_all(self):
        """Desabilita todos os botões e encerra a view."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        self.stop()

    async def on_timeout(self):
        """Desativa os botões visualmente ao final do timeout."""
        self.disable_all()
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.errors.NotFound:
                pass  # Mensagem foi deletada
            except Exception as e:
                logger.error(f"Erro ao editar mensagem no timeout: {e}")

# Botões customizados (sem alterações)
class HeartButton(discord.ui.Button):
    def __init__(self, callback_func):
        super().__init__(emoji="❤️", style=discord.ButtonStyle.primary)
        self.callback_func = callback_func

    async def callback(self, interaction: discord.Interaction):
        if self.callback_func:
            await self.callback_func(interaction)
        else:
            await interaction.response.send_message("Ação de coração não implementada.", ephemeral=True)

class ButterflyButton(discord.ui.Button):
    def __init__(self, callback_func):
        super().__init__(emoji="🦋", style=discord.ButtonStyle.primary)
        self.callback_func = callback_func

    async def callback(self, interaction: discord.Interaction):
        if self.callback_func:
            await self.callback_func(interaction)
        else:
            await interaction.response.send_message("Ação de borboleta não implementada.", ephemeral=True)

class PlanetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🌍", style=discord.ButtonStyle.secondary, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ação de planeta está desabilitada.", ephemeral=True)

class NotepadButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="📝", style=discord.ButtonStyle.secondary, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ação de anotação está desabilitada.", ephemeral=True)

class TrashButton(discord.ui.Button):
    def __init__(self, callback_func):
        super().__init__(emoji="🗑️", style=discord.ButtonStyle.danger)
        self.callback_func = callback_func

    async def callback(self, interaction: discord.Interaction):
        if self.callback_func:
            await self.callback_func(interaction)
        else:
            await interaction.response.send_message("Ação de exclusão não implementada.", ephemeral=True)

class NegativeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="❌", style=discord.ButtonStyle.secondary, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ação negativa está desabilitada.", ephemeral=True)

