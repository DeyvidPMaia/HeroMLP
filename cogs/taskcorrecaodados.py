import discord
from discord.ext import commands
import asyncio
import datetime
import time
from server_data import carregar_dados_guild, salvar_dados_guild
import logging
import random
from funcoes import apenas_moderador  # Importado para o comando restrito

# Configuração do logger
logger = logging.getLogger(__name__)

def get_next_midnight_timestamp() -> float:
    """Retorna o timestamp da próxima meia-noite no horário de Brasília (UTC-3)."""
    tz = datetime.timezone(datetime.timedelta(hours=-3))
    now = datetime.datetime.now(tz)
    midnight = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if midnight <= now:
        midnight += datetime.timedelta(days=1)
    return midnight.timestamp()

def get_next_scheduled_time(base_hour: int, offset: int) -> float:
    """
    Retorna o timestamp do próximo horário agendado para um determinado base_hour
    somado a um offset aleatório (em segundos), considerando o fuso de Brasília (UTC-3).
    """
    tz = datetime.timezone(datetime.timedelta(hours=-3))
    now = datetime.datetime.now(tz)
    scheduled = now.replace(hour=base_hour, minute=0, second=0, microsecond=0) + datetime.timedelta(seconds=offset)
    if scheduled <= now:
        scheduled += datetime.timedelta(days=1)
    return scheduled.timestamp()

class CorrecaoDados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bg_task = None
        logger.info("Cog CorrecaoDados inicializado.")

    @commands.Cog.listener()
    async def on_ready(self):
        """Evento chamado quando o bot está pronto. Inicia a task de correção."""
        logger.info("Evento on_ready disparado em CorrecaoDados. Iniciando task de correção.")
        if not self.bg_task or self.bg_task.done():
            self.bg_task = asyncio.create_task(self.correction_loop())
            logger.info("Task de correção iniciada.")

    async def cog_unload(self):
        """Cancela a task de background ao descarregar o cog."""
        logger.info("Descarregando cog CorrecaoDados.")
        if self.bg_task:
            self.bg_task.cancel()
            try:
                await self.bg_task
                logger.info("Task de correção cancelada com sucesso.")
            except asyncio.CancelledError:
                logger.info("Task de correção cancelada (CancelledError).")

    async def correction_loop(self):
        """Loop que agenda a execução das correções às 23h de Brasília."""
        await self.bot.wait_until_ready()
        logger.info("Loop de correção iniciado, aguardando bot estar pronto.")
        while not self.bot.is_closed():
            now = time.time()
            next_run = get_next_midnight_timestamp()
            sleep_time = next_run - now
            logger.info(f"Próxima execução da correção agendada para {datetime.datetime.fromtimestamp(next_run)} (em {sleep_time:.0f} segundos).")
            await asyncio.sleep(sleep_time)

            logger.info("Executando correções às 23h de Brasília.")
            await self.corrigir_horario_sem_rumo()
            await self.personagem_duplicado()
            await self.tasks_rodando()

    async def corrigir_horario_sem_rumo(self):
        """Verifica e corrige os horários do evento 'Personagem Sem Rumo' para o dia seguinte."""
        logger.info("Iniciando correção de horários do 'Personagem Sem Rumo'.")
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            try:
                dados = carregar_dados_guild(guild_id)
                horarios = dados.get("horario_personagem_sem_rumo", {})
                now = time.time()
                updated = False

                # Verifica e corrige os horários base (8h e 15h)
                for base in ["8", "15"]:
                    if base not in horarios or horarios[base] < now:
                        offset = random.randint(0, 3600)  # Offset aleatório até 1 hora
                        horarios[base] = get_next_scheduled_time(int(base), offset)
                        updated = True
                        logger.info(f"Horário {base}h corrigido para guild {guild_id}: {datetime.datetime.fromtimestamp(horarios[base])}")

                if updated:
                    dados["horario_personagem_sem_rumo"] = horarios
                    salvar_dados_guild(guild_id, dados)
                    logger.info(f"Horários atualizados salvos para guild {guild_id}.")
            except Exception as e:
                logger.error(f"Erro ao corrigir horários na guild {guild_id}: {e}")

    async def personagem_duplicado(self):
        """Verifica se há personagens duplicados nas listas de dados."""
        logger.info("Iniciando verificação de personagens duplicados.")
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            try:
                dados = carregar_dados_guild(guild_id)
                personagens = dados.get("personagens", [])  # Disponíveis
                personagens_salvos = dados.get("personagens_salvos", [])  # Salvados
                personagens_escondidos = dados.get("personagem_escondido", [])  # Perdidos
                lar_do_unicornio = dados.get("lar_do_unicornio", [])  # Lar do Unicórnio

                # Junta todos os personagens em uma lista para verificação
                todos_personagens = personagens + personagens_salvos + personagens_escondidos + lar_do_unicornio

                # Verifica duplicatas
                nomes_vistos = {}
                duplicados = {}
                for p in todos_personagens:
                    nome = p.get("nome", "")
                    if nome in nomes_vistos:
                        duplicados[nome] = duplicados.get(nome, 0) + 1
                    nomes_vistos[nome] = True

                if duplicados:
                    duplicados_str = ", ".join([f"{nome} ({qtd}x)" for nome, qtd in duplicados.items()])
                    logger.warning(f"Guild {guild_id} tem personagens duplicados: {duplicados_str}")
                else:
                    logger.info(f"Nenhum personagem duplicado encontrado na guild {guild_id}.")
            except Exception as e:
                logger.error(f"Erro ao verificar duplicatas na guild {guild_id}: {e}")

    async def tasks_rodando(self):
        """Lista as tasks ativas no bot."""
        logger.info("Iniciando verificação de tasks ativas.")
        tasks_ativas = [task for task in asyncio.all_tasks() if not task.done()]
        if tasks_ativas:
            logger.info(f"Tasks ativas no bot ({len(tasks_ativas)}):")
            for i, task in enumerate(tasks_ativas, 1):
                logger.info(f"Task {i}: {task.get_name()} - {task}")
        else:
            logger.info("Nenhuma task ativa encontrada no bot.")

    @apenas_moderador()
    @commands.command(name="ver_tasks", help="Exibe as tasks atualmente ativas no bot (apenas moderadores).")
    async def ver_tasks(self, ctx):
        """Comando manual para executar a verificação de tasks ativas."""
        logger.info(f"Comando !!ver_tasks executado por {ctx.author} na guild {ctx.guild.id}.")
        await ctx.send("🔍 Verificando tasks ativas. Confira os logs para detalhes.")
        await self.tasks_rodando()

async def setup(bot):
    await bot.add_cog(CorrecaoDados(bot))