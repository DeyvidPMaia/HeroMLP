import discord
from discord.ext import commands
import asyncio
import random
import time
import datetime
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_guild, salvar_estatisticas_seguro
from funcoes import verificar_imagem, sanitize_filename, apenas_moderador
import logging

# Configuração do logger específico para este cog
logger = logging.getLogger(__name__)

# Variável para controlar a exibição de logs
mostra_logs = True  # Defina como False para desativar os logs

def log_info(message):
    """Função auxiliar para logar mensagens apenas se mostra_logs for True."""
    if mostra_logs:
        logger.info(message)

def log_error(message):
    """Função auxiliar para logar erros apenas se mostra_logs for True."""
    if mostra_logs:
        logger.error(message)

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

class PersonagemSemRumo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bg_task = None
        log_info("Cog PersonagemSemRumo inicializado.")

    def merge_dados(self, dados_memoria: dict, dados_disco: dict) -> dict:
        """Mescla os dados em memória com os dados do disco, priorizando alterações locais."""
        resultado = dados_disco.copy()
        for chave in dados_memoria:
            if chave in ["personagens_sem_rumo", "usuarios", "personagens_por_usuario", "personagens_salvos", "personagem_escondido"]:
                if chave in dados_memoria:
                    if isinstance(dados_memoria[chave], dict):
                        resultado[chave] = resultado.get(chave, {}).copy()
                        resultado[chave].update(dados_memoria[chave])
                    elif isinstance(dados_memoria[chave], list):
                        resultado[chave] = dados_memoria[chave].copy()
                    else:
                        resultado[chave] = dados_memoria[chave]
        log_info(f"Dados mesclados para guild. Chaves atualizadas: {list(dados_memoria.keys())}")
        return resultado

    @commands.Cog.listener()
    async def on_ready(self):
        """Evento que é chamado quando o bot está pronto e as guilds estão carregadas."""
        log_info("Evento on_ready disparado. Iniciando limpeza e agendamento.")
        await self.limpar_evento_antigo()
        await self.initialize_schedules()
        self.bg_task = asyncio.create_task(self.task_loop())
        log_info("Task loop iniciada no on_ready.")

    async def cog_unload(self):
        """Método chamado automaticamente ao descarregar o cog.
        Cancela a task de background e remove o evento ativo de cada guild."""
        log_info("Descarregando cog PersonagemSemRumo.")
        if self.bg_task:
            self.bg_task.cancel()
            try:
                await self.bg_task
                log_info("Task de background cancelada com sucesso.")
            except asyncio.CancelledError:
                log_info("Task de background cancelada (CancelledError).")
        for guild in self.bot.guilds:
            try:
                guild_id = str(guild.id)
                dados = carregar_dados_guild(guild_id)
                if "personagens_sem_rumo" in dados:
                    dados.pop("personagens_sem_rumo")
                    salvar_dados_guild(guild_id, dados)
                    log_info(f"Evento removido da guild {guild_id} durante unload.")
            except Exception as e:
                log_error(f"Erro ao limpar evento na guild {guild.id} durante unload: {e}")

    async def limpar_evento_antigo(self):
        log_info("Iniciando limpeza de eventos antigos.")
        for guild in self.bot.guilds:
            try:
                guild_id = str(guild.id)
                dados = carregar_dados_guild(guild_id)
                if "personagens_sem_rumo" in dados:
                    dados.pop("personagens_sem_rumo")
                    salvar_dados_guild(guild_id, dados)
                    log_info(f"Evento antigo removido da guild {guild_id}.")
            except Exception as e:
                log_error(f"Erro ao limpar evento antigo na guild {guild.id}: {e}")

    async def initialize_schedules(self):
        log_info("Inicializando agendamentos para todas as guilds.")
        for guild in self.bot.guilds:
            try:
                guild_id = str(guild.id)
                dados = carregar_dados_guild(guild_id)
                dados.pop("personagens_sem_rumo", None)
                horarios = dados.get("horario_personagem_sem_rumo", {})
                for base in [8, 15]:
                    base_str = str(base)
                    offset = random.randint(0, 2600)
                    new_timestamp = get_next_scheduled_time(base, offset)
                    if base_str not in horarios or horarios[base_str] < time.time():
                        horarios[base_str] = new_timestamp
                dados["horario_personagem_sem_rumo"] = horarios
                salvar_dados_guild(guild_id, dados)
                log_info(f"Agendamento inicializado para guild {guild_id}. Horários: {horarios}")
            except Exception as e:
                log_error(f"Erro inicializando schedule na guild {guild.id}: {e}")

    async def task_loop(self):
        """Task em background que verifica periodicamente se algum horário agendado chegou."""
        await self.bot.wait_until_ready()
        log_info("Task loop iniciado, aguardando bot estar pronto.")
        while not self.bot.is_closed():
            try:
                for guild in self.bot.guilds:
                    guild_id = str(guild.id)
                    dados = carregar_dados_guild(guild_id)
                    if "horario_personagem_sem_rumo" not in dados:
                        dados["horario_personagem_sem_rumo"] = {}
                        for base in [8, 15]:
                            offset = random.randint(0, 3600)
                            dados["horario_personagem_sem_rumo"][str(base)] = get_next_scheduled_time(base, offset)
                        salvar_dados_guild(guild_id, dados)
                        log_info(f"Horários padrão criados para guild {guild_id}.")

                    for key, sched_timestamp in list(dados["horario_personagem_sem_rumo"].items()):
                        now_ts = time.time()
                        if key == "forcado":
                            if now_ts >= sched_timestamp and now_ts < sched_timestamp + 60:
                                log_info(f"Executando evento forçado na guild {guild_id} às {datetime.datetime.fromtimestamp(sched_timestamp)}.")
                                await self.execute_event(guild, key)
                                dados = carregar_dados_guild(guild_id)
                                dados["horario_personagem_sem_rumo"].pop(key)
                                salvar_dados_guild(guild_id, dados)
                            continue
                        if key.isdigit():
                            if now_ts >= sched_timestamp and now_ts < sched_timestamp + 60:
                                log_info(f"Executando evento agendado na guild {guild_id} para hora base {key} às {datetime.datetime.fromtimestamp(sched_timestamp)}.")
                                await self.execute_event(guild, key)
                                base_hour = int(key)
                                new_offset = random.randint(0, 3600)
                                dados = carregar_dados_guild(guild_id)
                                dados["horario_personagem_sem_rumo"][key] = get_next_scheduled_time(base_hour, new_offset)
                                salvar_dados_guild(guild_id, dados)
                                log_info(f"Novo horário agendado para guild {guild_id}: {dados['horario_personagem_sem_rumo'][key]}")
            except Exception as e:
                log_error(f"Erro na task_loop: {e}")
            await asyncio.sleep(30)

    async def execute_event(self, guild: discord.Guild, key: str):
        """Executa o evento de 'personagem sem rumo' para uma guild com ciclos repetidos e merge de dados."""
        try:
            guild_id = str(guild.id)
            dados = carregar_dados_guild(guild_id)
            log_info(f"Iniciando execução do evento para guild {guild_id} com chave {key}.")

            # Verificações iniciais
            if dados.get("personagens_sem_rumo") or len(dados.get("personagem_escondido", [])) >= 50:
                log_info(f"Evento abortado para guild {guild_id}: já existe um evento ativo ou limite de escondidos atingido.")
                return
            if any(p["nome"] == dados.get("personagens_sem_rumo", {}).get("nome", "") for p in dados.get("personagens", [])):
                log_info(f"Evento abortado para guild {guild_id}: personagem já está em 'personagens'.")
                return

            # Escolha do personagem
            current_owner = None
            personagens_por_usuario = dados.get("personagens_por_usuario", {})
            all_personagens = []
            for user_id, personagens in personagens_por_usuario.items():
                for personagem in personagens:
                    all_personagens.append((user_id, personagem))
            if not all_personagens:
                log_info(f"Evento abortado para guild {guild_id}: nenhum personagem disponível.")
                return

            chosen_owner, chosen_personagem = random.choice(all_personagens)
            personagem_name = chosen_personagem["nome"]
            log_info(f"Personagem escolhido para guild {guild_id}: {personagem_name} (dono: {chosen_owner}).")

            dados["personagens_sem_rumo"] = {
                "nome": personagem_name,
                "owner": chosen_owner,
                "hearts": 0
            }
            dados_atualizados = carregar_dados_guild(guild_id)
            dados = self.merge_dados(dados, dados_atualizados)
            salvar_dados_guild(guild_id, dados)

            # Seleção do canal
            channel = None
            if "ID_DO_CANAL_PRINCIPAL" in dados:
                channel = guild.get_channel(int(dados["ID_DO_CANAL_PRINCIPAL"]))
                if channel and not channel.permissions_for(guild.me).send_messages:
                    channel = None
            if channel is None:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break
            if channel is None:
                log_info(f"Evento abortado para guild {guild_id}: nenhum canal disponível para envio.")
                return
            log_info(f"Canal selecionado para guild {guild_id}: {channel.name} (ID: {channel.id}).")

            # Configuração do evento
            total_cycles = 5  # 5
            monitor_time = 5 * 60  # 5 * 60
            required_unique = 5  # 5
            required_hearts = 50  # 50

            achieved = False
            unique_reactors = set()

            image_path = f"resources/poneis/{personagem_name}.png"
            imagem = verificar_imagem(image_path)
            nome_imagem = sanitize_filename(personagem_name)

            # Loop dos ciclos
            for cycle in range(total_cycles):
                dados = carregar_dados_guild(guild_id)
                if "personagens_sem_rumo" not in dados:
                    log_info(f"Evento interrompido na guild {guild_id}: 'personagens_sem_rumo' não encontrado no ciclo {cycle + 1}.")
                    break
                current_hearts = dados["personagens_sem_rumo"]["hearts"]
                hearts_missing = max(0, required_hearts - current_hearts)

                embed = discord.Embed(
                    title=f"{personagem_name} Caminha sem rumo por Equestria ({hearts_missing} corações faltam)",
                    description=f"Ajudem {personagem_name} a encontrar um caminho seguro doando corações! ({len(unique_reactors)}/{required_unique} ajudantes)",
                    color=discord.Color.blue()
                )
                embed.set_image(url=f"attachment://{nome_imagem}.png")

                # Envia o embed com o arquivo em cada ciclo
                message = await channel.send(
                    embed=embed,
                    file=discord.File(imagem, filename=f"{nome_imagem}.png")
                )
                await message.add_reaction("❤️")
                log_info(f"Mensagem do evento enviada na guild {guild_id}, ciclo {cycle + 1}/{total_cycles}.")

                # Monitoramento de reações
                start_time = time.time()
                while time.time() - start_time < monitor_time:
                    try:
                        reaction, user = await self.bot.wait_for(
                            'reaction_add',
                            timeout=monitor_time - (time.time() - start_time),
                            check=lambda reaction, user: reaction.message.id == message.id 
                                and str(reaction.emoji) == "❤️" 
                                and not user.bot
                        )
                    except asyncio.TimeoutError:
                        log_info(f"Timeout atingido no monitoramento de reações na guild {guild_id}, ciclo {cycle + 1}.")
                        break
                    else:
                        user_id_str = str(user.id)
                        if user_id_str in unique_reactors:
                            try:
                                await message.remove_reaction("❤️", user)
                            except Exception:
                                pass
                            continue
                        dados = carregar_dados_guild(guild_id)
                        if "personagens_sem_rumo" not in dados:
                            log_info(f"Evento interrompido na guild {guild_id}: 'personagens_sem_rumo' não encontrado durante monitoramento.")
                            break
                        usuarios = dados.setdefault("usuarios", {})
                        reactor_data = usuarios.setdefault(user_id_str, {"coracao": 0})
                        if reactor_data.get("coracao", 0) >= 10:
                            reactor_data["coracao"] -= 10
                            reactor_data.setdefault("coracoes_doados", 0)
                            reactor_data["coracoes_doados"] += 10
                            dados["personagens_sem_rumo"]["hearts"] += 10
                            dados_atualizados = carregar_dados_guild(guild_id)
                            dados = self.merge_dados(dados, dados_atualizados)
                            salvar_dados_guild(guild_id, dados)
                            await channel.send(f"💖 <@{user.id}> ajudou {personagem_name} doando 10 corações!")
                            log_info(f"Usuário {user_id_str} doou 10 corações na guild {guild_id}.")
                        else:
                            try:
                                await message.remove_reaction("❤️", user)
                            except Exception:
                                pass
                        dados = carregar_dados_guild(guild_id)
                        if "personagens_sem_rumo" not in dados:
                            log_info(f"Evento interrompido na guild {guild_id}: 'personagens_sem_rumo' não encontrado após reação.")
                            break
                        current_hearts = dados["personagens_sem_rumo"]["hearts"]
                        hearts_missing = max(0, required_hearts - current_hearts)
                        embed.title = f"{personagem_name} Caminha sem rumo por Equestria ({hearts_missing} corações faltam)"
                        embed.description = f"Ajudem {personagem_name} a encontrar um caminho seguro doando corações! ({len(unique_reactors)}/{required_unique} ajudantes)"
                        try:
                            await message.edit(embed=embed)
                        except Exception as e:
                            log_error(f"Erro ao atualizar embed na guild {guild_id}: {e}")
                        unique_reactors.add(user_id_str)
                        log_info(f"Reator único adicionado na guild {guild_id}: {user_id_str}. Total: {len(unique_reactors)}.")

                # Verificação de sucesso
                dados = carregar_dados_guild(guild_id)
                if "personagens_sem_rumo" not in dados:
                    log_info(f"Evento interrompido na guild {guild_id}: 'personagens_sem_rumo' não encontrado após monitoramento.")
                    break
                if dados["personagens_sem_rumo"]["hearts"] >= required_hearts or len(unique_reactors) >= required_unique:
                    achieved = True
                    dados.pop("personagens_sem_rumo")
                    dados_atualizados = carregar_dados_guild(guild_id)
                    dados = self.merge_dados(dados, dados_atualizados)
                    salvar_dados_guild(guild_id, dados)
                    await message.delete()
                    await channel.send(f"🎉 **{personagem_name} encontrou um caminho seguro!**")
                    log_info(f"Evento concluído com sucesso na guild {guild_id}: {personagem_name} salvo.")
                    # ... (atualização de estatísticas para sucesso permanece igual)
                    break

                if cycle < total_cycles - 1:
                    await message.delete()
                    await asyncio.sleep(monitor_time)
                    dados = carregar_dados_guild(guild_id)

            # Caso de fracasso
            if not achieved:
                dados = carregar_dados_guild(guild_id)

                if "personagens_sem_rumo" in dados:  # Verifica antes de prosseguir
                    usuarios = dados.setdefault("usuarios", {})
                    for uid in unique_reactors:
                        reactor_data = usuarios.setdefault(uid, {"coracao": 0})
                        reactor_data["coracao"] += 10
                        reactor_data.setdefault("coracoes_devolvidos", 0)
                        reactor_data["coracoes_devolvidos"] += 10
                    
                    dados_atualizados = carregar_dados_guild(guild_id)
                    dados = self.merge_dados(dados, dados_atualizados)
                    
                    estatisticas = carregar_estatisticas_guild(guild_id)
                    evento_stats = estatisticas.setdefault("evento_personagem_sem_rumo", {"total_sem_rumo": 0, "total_escondido": 0})
                    evento_stats.setdefault("coracoes_devolvidos_totais", 0)
                    evento_stats["coracoes_devolvidos_totais"] += 10 * len(unique_reactors)
                    log_info(f"Corações devolvidos na guild {guild_id}: {10 * len(unique_reactors)}.")

                    current_owner = None
                    personagens_por_usuario = dados.get("personagens_por_usuario", {})
                    for uid, plist in personagens_por_usuario.items():
                        for p in plist:
                            if p["nome"] == personagem_name:
                                current_owner = uid
                                break
                        if current_owner:
                            break
                    if current_owner:
                        owner_list = personagens_por_usuario.get(current_owner, [])
                        owner_list = [p for p in owner_list if p["nome"] != personagem_name]
                        dados["personagens_por_usuario"][current_owner] = owner_list
                        dados["personagens_salvos"] = [p for p in dados["personagens_salvos"] if p["nome"] != personagem_name]
                        dados.setdefault("personagem_escondido", [])
                        dados["personagem_escondido"] = [p for p in dados["personagem_escondido"] if p["nome"] != personagem_name]
                        dados["personagem_escondido"].append(chosen_personagem)
                        dados.pop("personagens_sem_rumo", None)
                        dados_atualizados = carregar_dados_guild(guild_id)
                        dados = self.merge_dados(dados, dados_atualizados)
                        salvar_dados_guild(guild_id, dados)
                        await channel.send(f"❌ **{personagem_name} não encontrou um lugar seguro e se escondeu. Os corações doados foram reembolsados aos ajudantes.**")
                        log_info(f"Evento falhou na guild {guild_id}: {personagem_name} agora está escondido.")

                    # Atualização de estatísticas para o caso de fracasso
                    estatisticas = carregar_estatisticas_guild(guild_id)
                    bot_stats = estatisticas.setdefault("estatisticas_meus_personagens", {})
                    char_stats = bot_stats.setdefault(personagem_name, {})
                    # Garantir que as chaves existam com valores padrão
                    char_stats.setdefault("personagem_sem_rumo", 0)
                    char_stats.setdefault("ja_esteve_escondido", 0)
                    char_stats["personagem_sem_rumo"] += 1
                    char_stats["ja_esteve_escondido"] += 1

                    evento_stats = estatisticas.setdefault("evento_personagem_sem_rumo", {"total_sem_rumo": 0, "total_escondido": 0})
                    evento_stats["total_sem_rumo"] += 1
                    evento_stats["total_escondido"] += 1

                    owner_id_for_stats = current_owner if current_owner else chosen_owner
                    usuarios_stats = estatisticas.setdefault("estatisticas_dos_usuarios", {})
                    user_stats = usuarios_stats.setdefault(owner_id_for_stats, {})
                    user_char_stats = user_stats.setdefault("estatisticas_meus_personagens", {}).setdefault(personagem_name, {})
                    # Garantir que as chaves existam com valores padrão para o usuário também
                    user_char_stats.setdefault("personagem_sem_rumo", 0)
                    user_char_stats.setdefault("ja_esteve_escondido", 0)
                    user_char_stats["personagem_sem_rumo"] += 1
                    user_char_stats["ja_esteve_escondido"] += 1

                    await salvar_estatisticas_seguro(guild_id, estatisticas)
                    log_info(f"Estatísticas atualizadas para guild {guild_id} (fracasso).")

        except Exception as e:
            import traceback
            log_error(f"Erro em execute_event na guild {guild_id}: {str(e)}\nTraceback: {traceback.format_exc()}")

    @apenas_moderador()
    @commands.command(name="semrumo_manual", hidden=True, help="Força o agendamento do evento de personagem sem rumo para 5 minutos a partir de agora.")
    async def forcar_semrumo(self, ctx):
        guild = ctx.guild
        guild_id = str(guild.id)
        dados = carregar_dados_guild(guild_id)
        if "horario_personagem_sem_rumo" not in dados:
            dados["horario_personagem_sem_rumo"] = {}
        # Define o timestamp para 5 minutos após a execução
        forced_timestamp = time.time() + 120  # 2 minutos (120)
        dados["horario_personagem_sem_rumo"]["forcado"] = forced_timestamp
        salvar_dados_guild(guild_id, dados)
        await ctx.send("⏳ Evento de personagem sem rumo agendado para 2 minutos a partir de agora.")
        log_info(f"Evento manual agendado para guild {guild_id} em {datetime.datetime.fromtimestamp(forced_timestamp)}.")

async def setup(bot):
    await bot.add_cog(PersonagemSemRumo(bot))