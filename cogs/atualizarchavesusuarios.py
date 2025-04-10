import os
import logging
import json
from discord.ext import commands
from server_data import carregar_dados_guild, salvar_dados_guild

logger = logging.getLogger(__name__)

class AtualizarUsuariosCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizado = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.atualizado:
            await self.atualizar_usuarios()
            self.atualizado = True
            logger.info("Atualização de usuários concluída.")

    async def atualizar_usuarios(self):
        base_dir = "resources/servidores"
        if not os.path.exists(base_dir):
            logger.info("Diretório de servidores não existe, nada a atualizar.")
            return

        # Itera por cada arquivo de dados dos servidores
        for filename in os.listdir(base_dir):
            if not filename.endswith(".json"):
                continue
            guild_id = filename[:-5]  # remove a extensão ".json"
            try:
                dados = carregar_dados_guild(guild_id)
                usuarios = dados.get("usuarios", {})
                alterado = False
                for user_id, user_data in usuarios.items():
                    if "resgatou_personagem" not in user_data:
                        user_data["resgatou_personagem"] = True
                        alterado = True
                if alterado:
                    salvar_dados_guild(guild_id, dados)
                    logger.info(f"Atualizado 'resgatou_personagem' para a guild {guild_id}.")
            except Exception as e:
                logger.error(f"Erro ao atualizar guild {guild_id}: {e}")

async def setup(bot):
    await bot.add_cog(AtualizarUsuariosCog(bot))
