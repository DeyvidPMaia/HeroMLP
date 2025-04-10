# evento_esquecimento.py 02/04/2025 00:00 (sem modo de teste, mantendo função fake, com trava para evitar duplicação)

import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, time, timedelta
from server_data import carregar_dados_guild, salvar_dados_guild
from utils import personagem_perdido
import logging
import random
import os

logger = logging.getLogger(__name__)

# Dicionário global de locks por guilda para evitar execuções concorrentes
guild_locks = {}

def get_guild_lock(guild_id: str) -> asyncio.Lock:
    if guild_id not in guild_locks:
        guild_locks[guild_id] = asyncio.Lock()
    return guild_locks[guild_id]

class EventoEsquecimento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Horário de execução configurável (hora, minuto) - ajustável para testes
        self.HORARIO_EXECUCAO = time(20, 0)  # Padrão: 20:00 (8 PM), altere aqui para testes
        self.ultima_execucao = {}  # {guild_id: data da última execução}
        self.ultimos_avisos = {}   # {guild_id: {tempo: data}}
        self.bloqueio_avisado = {}  # {guild_id: bool} para rastrear se o bloqueio já foi avisado
        self.exibir_log_esquecimento = True
        self.imagens_esquecimento = []
        self.imagens_esquecidos = []
        self.carregar_imagens_esquecimento()
        self.evento_esquecimento.start()

    def cog_unload(self):
        self.evento_esquecimento.cancel()

    def log(self, level, message):
        """Loga mensagens apenas se exibir_log_esquecimento for True."""
        if self.exibir_log_esquecimento:
            getattr(logger, level)(message)

    def carregar_imagens_esquecimento(self):
        """Carrega imagens da pasta 'resources/esquecimento/' com prefixos específicos."""
        pasta_normal = "resources/esquecimento/"
        
        if not os.path.exists(pasta_normal):
            os.makedirs(pasta_normal, exist_ok=True)
            self.log("warning", f"Pasta {pasta_normal} não existia e foi criada. Adicione imagens com prefixo 'esquecimento' ou 'esquecidos' (ex.: esquecimento_01.png)!")
        
        self.imagens_esquecimento = [
            os.path.join(pasta_normal, arquivo)
            for arquivo in os.listdir(pasta_normal)
            if arquivo.startswith("esquecimento") and arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        self.imagens_esquecidos = [
            os.path.join(pasta_normal, arquivo)
            for arquivo in os.listdir(pasta_normal)
            if arquivo.startswith("esquecidos") and arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        
        if not self.imagens_esquecimento:
            self.imagens_esquecimento = ["resources/poneis/semimagem.png"]
        if not self.imagens_esquecidos:
            self.imagens_esquecidos = ["resources/poneis/semimagem.png"]

    def sortear_imagem(self, tipo="esquecimento"):
        """Sorteia uma imagem da lista correspondente."""
        if tipo == "esquecimento":
            return random.choice(self.imagens_esquecimento)
        elif tipo == "esquecidos":
            return random.choice(self.imagens_esquecidos)
        return "resources/poneis/semimagem.png"

    def calcular_quantidade_perdida(self, dados_guild):
        """
        Calcula a quantidade de personagens a serem perdidos com base na razão entre
        personagens salvos e disponíveis, ajustada dinamicamente ao total inicial.
        """
        personagens_salvos = len(dados_guild.get("personagens_salvos", []))
        personagens_disponiveis = len(dados_guild.get("personagens", []))
        total_inicial = personagens_salvos + personagens_disponiveis

        if total_inicial == 0 or personagens_salvos == 0:
            return 0, None

        quantidade_fixa = dados_guild.get("quantidade_fixa_esquecimento", False)
        if quantidade_fixa:
            return 10, None

        fracao_salvos = personagens_salvos / total_inicial
        if fracao_salvos < 0.125:
            fracao_perda = 1 / 4
        elif fracao_salvos < 0.25:
            fracao_perda = 1 / 5
        elif fracao_salvos < 0.375:
            fracao_perda = 1 / 6
        elif fracao_salvos < 0.5:
            fracao_perda = 1 / 7
        else:
            fracao_perda = 1 / 8

        quantidade = max(1, int(personagens_salvos * fracao_perda))
        if personagens_disponiveis <= 50:
            quantidade = min(quantidade, 10)

        return quantidade, f"1/{int(1 / fracao_perda)}"

    def get_guild_time(self, guild_id):
        """Retorna o horário ajustado ao fuso horário da guild (em horas de deslocamento de UTC)."""
        dados = carregar_dados_guild(guild_id)
        if "fuso_horario" not in dados:
            dados["fuso_horario"] = -3
            salvar_dados_guild(guild_id, dados)
        fuso_horario = dados["fuso_horario"]
        return datetime.utcnow() + timedelta(hours=fuso_horario)

    async def enviar_aviso(self, canal, tempo_restante, guild_id):
        """Envia um aviso com o tempo restante."""
        imagem = self.sortear_imagem("esquecimento")
        embed = discord.Embed(
            title="Aviso do Evento de Esquecimento",
            description=f"O evento de esquecimento ocorrerá em {tempo_restante}.",
            color=discord.Color.orange()
        )
        embed.set_image(url=f"attachment://{os.path.basename(imagem)}")
        await canal.send(embed=embed, file=discord.File(imagem))

    async def gerenciar_bloqueio(self, guild_id, canal, agora, horario_alvo):
        """Gerencia evento_esquecimento_ocorrendo integrado à verificação do evento."""
        dados = carregar_dados_guild(guild_id)
        inicio_bloqueio = horario_alvo - timedelta(minutes=5)  # 5 minutos antes
        fim_bloqueio = horario_alvo + timedelta(minutes=5)     # 5 minutos depois
        bloqueio_ativo = dados.get("evento_esquecimento_ocorrendo", False)

        if not canal:
            self.log("warning", f"Canal principal não configurado ou inacessível para guild {guild_id}")
            return

        if guild_id not in self.bloqueio_avisado:
            self.bloqueio_avisado[guild_id] = False

        # Ativa o bloqueio se dentro do intervalo e ainda não avisado
        if inicio_bloqueio <= agora < fim_bloqueio and not bloqueio_ativo and not self.bloqueio_avisado[guild_id]:
            try:
                dados["evento_esquecimento_ocorrendo"] = True
                salvar_dados_guild(guild_id, dados)
                self.log("info", f"Bloqueio ativado para guild {guild_id} às {agora}")
                await canal.send("⚠️ **As trevas estão se aproximando... Alguns comandos estão bloqueados por 10 minutos.**")
            except Exception as e:
                self.log("error", f"Falha ao salvar bloqueio para guild {guild_id}: {e}")
            self.bloqueio_avisado[guild_id] = True

        # Desativa o bloqueio se fora do intervalo e ainda ativo
        elif agora >= fim_bloqueio and bloqueio_ativo:
            try:
                dados["evento_esquecimento_ocorrendo"] = False
                salvar_dados_guild(guild_id, dados)
                self.log("info", f"Bloqueio desativado para guild {guild_id} às {agora}")
                await canal.send("✅ **As trevas se dissiparam. Os comandos estão liberados novamente.**")
            except Exception as e:
                self.log("error", f"Falha ao desativar bloqueio para guild {guild_id}: {e}")
            self.bloqueio_avisado[guild_id] = False

    async def personagem_perdido_fake(self, guild, chamado_por, quantidade, usar_trevo=True, dm=True):
        """Função fake para testes futuros, mantida para referência."""
        embed = discord.Embed(
            title="Simulação de Esquecimento",
            description=f"Simulando perda de {quantidade} personagens.",
            color=discord.Color.purple()
        )
        self.log("info", f"Simulação de personagem_perdido_fake para guild {guild.id}: quantidade={quantidade}, usar_trevo={usar_trevo}, dm={dm}")
        return [embed]

    @tasks.loop(minutes=1)
    async def evento_esquecimento(self):
        """Executa avisos, bloqueio de comandos e o evento de esquecimento no horário configurado."""
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            agora = self.get_guild_time(guild_id)
            horario_alvo = datetime.combine(agora.date(), self.HORARIO_EXECUCAO)
            dados = carregar_dados_guild(guild_id)
            canal_principal_id = dados.get("ID_DO_CANAL_PRINCIPAL")
            canal = guild.get_channel(int(canal_principal_id)) if canal_principal_id else None

            if not canal or not canal.permissions_for(guild.me).send_messages:
                continue

            # Gerencia o bloqueio integrado à verificação do evento
            await self.gerenciar_bloqueio(guild_id, canal, agora, horario_alvo)

            # Calcula tempos para avisos
            diff_segundos = (horario_alvo - agora).total_seconds()
            minutos_restantes = round(diff_segundos / 60)

            if guild_id not in self.ultimos_avisos:
                self.ultimos_avisos[guild_id] = {}

            avisos = [
                (60, "1 hora"),
                (30, "30 minutos"),
                (10, "10 minutos")
            ]
            for minutos_alvo, texto_tempo in avisos:
                if minutos_restantes == minutos_alvo:
                    ultima_vez = self.ultimos_avisos[guild_id].get(minutos_alvo)
                    if not ultima_vez or (agora - ultima_vez).total_seconds() > 300:
                        await self.enviar_aviso(canal, texto_tempo, guild_id)
                        self.ultimos_avisos[guild_id][minutos_alvo] = agora

            # Verifica se é hora do evento (com margem de 1 minuto)
            if abs(diff_segundos) < 60:
                lock = get_guild_lock(guild_id)  # Obtém a trava para a guilda
                async with lock:  # Garante exclusividade na execução
                    ultima_execucao = self.ultima_execucao.get(guild_id)
                    if ultima_execucao and ultima_execucao.date() == agora.date():
                        continue

                    self.ultima_execucao[guild_id] = agora
                    quantidade, fracao = self.calcular_quantidade_perdida(dados)

                    if quantidade == 0:
                        self.log("info", f"Nenhum personagem disponível para o evento de esquecimento na guild {guild_id} às {agora}")
                        continue

                    self.log("info", f"Agendando evento de esquecimento para guild {guild_id} às {agora} com {quantidade} personagens.")
                    await asyncio.sleep(random.uniform(0, 60))

                    imagem_esquecidos = self.sortear_imagem("esquecidos")
                    if fracao:
                        mensagem = f"{fracao} dos nossos amigos foram esquecidos"
                    else:
                        mensagem = f"{quantidade} dos nossos amigos foram esquecidos"
                    embed_informativo = discord.Embed(
                        title="Evento de Esquecimento",
                        description=mensagem,
                        color=discord.Color.red()
                    )
                    embeds = await personagem_perdido(
                        guild=guild,
                        chamado_por="evento_esquecimento",
                        quantidade=quantidade,
                        usar_trevo=True,
                        dm=True,
                        cor_chamado=discord.Colour.red()
                    )

                    embed_informativo.set_image(url=f"attachment://{os.path.basename(imagem_esquecidos)}")
                    await canal.send(embed=embed_informativo, file=discord.File(imagem_esquecidos))
                    if embeds is None:
                        self.log("error", f"Falha ao executar personagem_perdido para guild {guild_id}")
                        await canal.send("⚠️ **Erro ao processar o evento de esquecimento. Tente novamente mais tarde.**")
                        continue
                    if embeds:
                        self.log("info", f"Embeds gerados para guild {guild_id}: {len(embeds)} embeds")
                        for embed in embeds:
                            await canal.send(embed=embed)

    @evento_esquecimento.before_loop
    async def before_evento_esquecimento(self):
        """Sincroniza o início da task com o próximo minuto."""
        await self.bot.wait_until_ready()
        agora = datetime.utcnow()
        segundos_restantes = 60 - agora.second
        await asyncio.sleep(segundos_restantes)

async def setup(bot):
    cog = EventoEsquecimento(bot)
    for guild in bot.guilds:
        guild_id = str(guild.id)
        dados = carregar_dados_guild(guild_id)
        canal_id = dados.get("ID_DO_CANAL_PRINCIPAL")
        if canal_id:
            canal = guild.get_channel(int(canal_id))
            if not canal or not canal.permissions_for(guild.me).send_messages:
                cog.log("warning", f"Sem permissão para enviar mensagens no canal principal da guild {guild.name} ({guild_id})")
    await bot.add_cog(cog)