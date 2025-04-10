# tasks.py 22/03/2025 23:45 (corrigido cancelamento da tarefa personagem_perdido)

import discord
from discord.ext import tasks, commands
from utils import personagem_perdido
import logging
import random
from server_data import carregar_dados_guild, salvar_dados_guild
import os
import json
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class PerdidoTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.personagem_perdido_loop.start()
        logger.info("Cog PerdidoTasks inicializado.")

    def cog_unload(self):
        """Chamado automaticamente ao descarregar o cog."""
        logger.info("Iniciando parada da task personagem_perdido ao descarregar o cog.")
        self.personagem_perdido_loop.cancel()
        logger.info("Task personagem_perdido_loop cancelada com sucesso.")

    @tasks.loop(seconds=60.0)
    async def personagem_perdido_loop(self):
        if self.personagem_perdido_loop.is_being_cancelled():
            logger.debug("Task personagem_perdido_loop está sendo cancelada, pulando execução.")
            return

        tempo_atual = discord.utils.utcnow().timestamp()
        logger.debug(f"Verificando personagem_perdido_loop às {tempo_atual}")

        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            dados_guild = carregar_dados_guild(guild_id)
            if not dados_guild:
                logger.warning(f"Dados não carregados para a guilda {guild_id}")
                continue

            tempo_intervalo = dados_guild.get("tempo_personagem_perdido", 3600)
            ultimo_evento = dados_guild.get("ultimo_personagem_perdido", 0)
            proximo_evento = ultimo_evento + tempo_intervalo

            logger.debug(f"Guild {guild_id}: ultimo_evento={ultimo_evento}, proximo_evento={proximo_evento}, tempo_atual={tempo_atual}")

            if tempo_atual >= proximo_evento:
                logger.info(f"Executando personagem_perdido na guilda {guild.name} ({guild_id})")
                try:
                    backup_dir = "resources/servidores/backups"
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                        logger.info(f"Pasta de backups criada: {backup_dir}")

                    timestamp = datetime.utcfromtimestamp(tempo_atual).strftime("%Y%m%d_%H%M%S")
                    backup_path = os.path.join(backup_dir, f"{guild_id}_backup_{timestamp}.json")
                    with open(backup_path, "w", encoding="utf-8") as f:
                        json.dump(dados_guild, f, ensure_ascii=False, indent=4)
                    logger.info(f"Backup criado para {guild_id} em {backup_path}")

                    backups = [f for f in os.listdir(backup_dir) if f.startswith(f"{guild_id}_backup_") and f.endswith(".json")]
                    backups.sort()
                    if len(backups) > 5:
                        backups_a_excluir = backups[:-5]
                        for backup in backups_a_excluir:
                            try:
                                os.remove(os.path.join(backup_dir, backup))
                                logger.debug(f"Backup antigo excluído: {backup}")
                            except OSError as e:
                                logger.warning(f"Erro ao excluir backup {backup}: {e}")
                                
                    # Executa personagem_perdido
                    embeds = await personagem_perdido(guild, "perdido_automatico", quantidade=random.randint(1, 2), usar_trevo=True, dm=True, cor_chamado=discord.Colour.yellow())
                    if embeds:
                        canal_log = dados_guild.get("ID_DO_CANAL_PRINCIPAL")
                        if canal_log:
                            canal = self.bot.get_channel(canal_log)
                            if canal and canal.permissions_for(guild.me).send_messages:
                                if isinstance(embeds, list):
                                    for emb in embeds:
                                        await canal.send(embed=emb)
                                else:
                                    await canal.send(embed=embeds)
                                logger.info(f"Mensagem enviada ao canal {canal_log} em {guild_id}")
                            else:
                                logger.warning(f"Canal {canal_log} inválido ou sem permissão em {guild_id}")
                        else:
                            logger.info(f"Nenhum canal_logs configurado para {guild_id}")


                    dados_guild = carregar_dados_guild(guild_id) # Garante dados atualizados
                    dados_guild["ultimo_personagem_perdido"] = tempo_atual
                    salvar_dados_guild(guild_id, dados_guild)
                    logger.debug(f"Timestamp atualizado para {tempo_atual} em {guild_id}")
                except Exception as e:
                    logger.error(f"Erro ao executar personagem_perdido ou gerenciar backups em {guild_id}: {e}")

    @personagem_perdido_loop.before_loop
    async def before_personagem_perdido_loop(self):
        await self.bot.wait_until_ready()
        logger.info("Task personagem_perdido pronta para iniciar.")

async def setup(bot):
    await bot.add_cog(PerdidoTasks(bot))