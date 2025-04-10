# funcoes.py 24/03/2025 10:00 atualizado funcao de normalização(função de log para perdido)

import json
import discord
from discord.ext import commands
import os
import random
import asyncio
import globals
import functools
import unicodedata
import re
from datetime import datetime
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

imagens_naoencontrado = []

def backup_dados_guild(guild_id: str, dados: dict):
    """Cria um backup dos dados da guild, mantendo apenas os 5 mais recentes."""
    pasta_backup = f"resources/servidores/{guild_id}/backups/"
    os.makedirs(pasta_backup, exist_ok=True)
    
    # Gera o nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_backup = f"{pasta_backup}arquivo_backup_{timestamp}.json"
    
    # Salva o backup
    with open(caminho_backup, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    
    # Lista todos os backups
    backups = [f for f in os.listdir(pasta_backup) if f.startswith("arquivo_backup_") and f.endswith(".json")]
    backups.sort()  # Ordena por nome (timestamp)
    
    # Remove os mais antigos se houver mais de 5
    while len(backups) > 5:
        os.remove(os.path.join(pasta_backup, backups.pop(0)))

def carregar_estado():
    try:
        with open("resources/dados.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            personagens_disponiveis = dados.get("personagens", [])
            personagens_salvos = dados.get("personagens_salvos", [])
            contador_personagens_salvos = dados.get("contador_personagens_salvos", {})
            personagens_por_usuario = dados.get("personagens_por_usuario", {})
            return personagens_disponiveis, personagens_salvos, contador_personagens_salvos, personagens_por_usuario
    except (FileNotFoundError, json.JSONDecodeError):
        personagens = carregar_personagens()
        return personagens.copy(), [], {}, {}


# Função para carregar personagens a partir de um arquivo JSON
def carregar_personagens():
    try:
        #padrão é 'todospersonagens', carregando de dados não reinicia
        with open("resources/todospersonagens.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            personagens = dados.get("personagens", [])
            if all("nome" in p and "especie" in p for p in personagens):
                return personagens
            else:
                print("Erro: Estrutura de dados inválida no arquivo JSON.")
                return []
    except FileNotFoundError:
        print("Erro: O arquivo 'resources/personagens.json' não foi encontrado.")
        return []
    except json.JSONDecodeError:
        print("Erro: Não foi possível decodificar o JSON em 'resources/personagens.json'.")
        return []

# Função para salvar os dados no arquivo JSON
def salvar_dados(personagens_disponiveis, personagens_salvos, contador_personagens_salvos, personagens_por_usuario):
    try:
        dados = {
            "personagens": personagens_disponiveis,
            "personagens_salvos": personagens_salvos,
            "contador_personagens_salvos": contador_personagens_salvos,
            "personagens_por_usuario": personagens_por_usuario
        }
        with open("resources/dados.json", "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")


# Função para verificar se o usuário tem permissão de moderador
def apenas_moderador():
    async def predicado(ctx):

        # Verifica se o usuário tem permissão de administrador
        if ctx.author.guild_permissions.administrator:
            return True

        # Verifica se o usuário possui o cargo "magoMLP"
        cargo_mago = discord.utils.get(ctx.author.roles, name="MagoMLP")
        if cargo_mago:
            return True

        return False  # Não tem permissão

    def decorator(func):
        func.admin_only = True  # Marca a função como restrita a administradores ou "magoMLP"
        return commands.check(predicado)(func)

    return decorator

def verificar_imagem(imagem):
    if os.path.isfile(imagem):
        return imagem
    else:
        #semimagem.png chamando uma função
        return "resources/poneis/semimagem.png"
    

def carregar_imagens_naoencontrado():
    """Carrega as imagens da pasta 'naoencontrado' uma vez no início."""
    global imagens_naoencontrado
    caminho_pasta = "resources/poneis/naoencontrado"
    imagens_naoencontrado = [
        os.path.join(caminho_pasta, arquivo).replace(os.sep, "/")  # Substitui separador nativo por "/"
        for arquivo in os.listdir(caminho_pasta)
        if arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
    ]
    if not imagens_naoencontrado:
        imagens_naoencontrado = ["resources/poneis/semimagem.png"]

def sortear_naoencontrado():
    """Sorteia uma imagem da lista pré-carregada."""
    return random.choice(imagens_naoencontrado)


def no_dm():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if ctx.guild is None:  # Se for DM
                await ctx.send("❌ Este comando não funciona via DM.")
                return
            return await func(self, ctx, *args, **kwargs)  # Executa normalmente no servidor
        return wrapper
    return decorator

def maintenance_off():
    """
    Decorator que permite a execução do comando somente se o modo de manutenção estiver desativado.
    Se o modo estiver ativo, envia uma mensagem informando e bloqueia a execução do comando.
    """
    async def predicate(ctx):
        if globals.maintenance_mode:
            await ctx.send("⚙️ O bot está em modo de manutenção. Tente novamente mais tarde.")
            return False
        return True
    return commands.check(predicate)



def normalize(name: str) -> str:
    """Normaliza o nome removendo espaços, acentos, pontos, apóstrofos, parentêses e hífens, e convertendo para minúsculas."""
    # Remove acentos
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    # Remove espaços, pontos, apóstrofos, parenteses e hífens
    name = name.lower().replace(" ", "").replace(".", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "")
    return name


def carregar_token():
    caminho_env = os.path.join(os.path.dirname(os.getcwd()), ".env")

    if os.path.exists(caminho_env):
        with open(caminho_env, "r") as f:
            return(f.read())
    else:
        print("Arquivo .env não encontrado ou sem permissão.")


def sanitize_filename(nome):
    """Remove ou substitui caracteres especiais de um nome para uso em arquivos."""
    # Converte para minúsculas e substitui espaços por underscores
    nome = nome.lower().replace(" ", "_")
    # Remove ou substitui caracteres especiais (apóstrofos, acentos, etc.)
    nome = re.sub(r"[^a-z0-9_]", "", nome)  # Mantém apenas letras, números e underscores
    return nome



def log_relatorio_personagem_perdido(guild_id: str, chamado_por: str, mensagem: str):
    """Armazena informações de debug em um arquivo txt, substituindo o anterior."""
    caminho = f"resources/servidores/{guild_id}/relatorios/relatorio_personagem_perdido.txt"
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    
    hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conteudo = (
        f"Relatório de personagem_perdido\n"
        f"Guild ID: {guild_id}\n"
        f"Chamado por: {chamado_por}\n"
        f"Hora da chamada: {hora_atual}\n"
        f"Detalhes:\n{mensagem}\n"
    )
    
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def get_next_scheduled_time(base_hour: int, offset: int, tz_offset: int = -3) -> float:
    """
    Retorna o timestamp do próximo horário agendado para um determinado base_hour
    somado a um offset em segundos, considerando um fuso horário customizado.
    
    Parâmetros:
    - base_hour: int - a hora base do evento (0-23).
    - offset: int - offset em segundos a ser adicionado ao horário base.
    - tz_offset: int - offset do fuso horário em relação ao UTC (padrão -3 para Brasília).
    
    Retorna:
    - float: timestamp do próximo horário agendado.
    """
    tz = datetime.timezone(datetime.timedelta(hours=tz_offset))
    now = datetime.datetime.now(tz)
    scheduled = now.replace(hour=base_hour, minute=0, second=0, microsecond=0) + datetime.timedelta(seconds=offset)
    if scheduled <= now:
        scheduled += datetime.timedelta(days=1)
    return scheduled.timestamp()


#funcoes novas para exibir

def caminho_dados_recompensa_exibir(guild_id: str) -> str:
    """Retorna o caminho do arquivo dados_recompensa_exibir.json para uma guilda."""
    return f"resources/servidores/{guild_id}/dados_recompensa_exibir.json"

def carregar_dados_recompensa_exibir(guild_id: str) -> dict:
    """Carrega os dados de recompensa de exibição para uma guilda."""
    caminho = caminho_dados_recompensa_exibir(guild_id)
    
    # Se o arquivo não existe, cria um novo com um dicionário vazio
    if not os.path.exists(caminho):
        logger.info(f"Criando novo arquivo de dados_recompensa_exibir para a guild {guild_id}.")
        dados_iniciais = {}
        salvar_dados_recompensa_exibir(guild_id, dados_iniciais)
        return dados_iniciais

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Arquivo {caminho} corrompido. Criando um novo.")
        dados_iniciais = {}
        salvar_dados_recompensa_exibir(guild_id, dados_iniciais)
        return dados_iniciais
    except Exception as e:
        logger.error(f"Falha ao carregar dados_recompensa_exibir da guild {guild_id}: {e}")
        return {}

def salvar_dados_recompensa_exibir(guild_id: str, dados: dict):
    """Salva os dados de recompensa de exibição para uma guilda."""
    caminho = caminho_dados_recompensa_exibir(guild_id)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    # Criar backup antes de salvar
    if os.path.exists(caminho):
        backup_caminho = f"{caminho}.bak"
        os.replace(caminho, backup_caminho)

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        logger.debug(f"Dados de recompensa de exibição salvos com sucesso para a guild {guild_id}")
    except Exception as e:
        logger.error(f"Falha ao salvar dados_recompensa_exibir da guild {guild_id}: {e}")
        # Tenta restaurar o backup em caso de falha
        if os.path.exists(backup_caminho):
            os.replace(backup_caminho, caminho)
        raise

async def salvar_dados_recompensa_exibir_seguro(guild_id: str, dados: dict):
    """Salva os dados de recompensa de exibição de forma segura, logando erros sem propagá-los."""
    try:
        salvar_dados_recompensa_exibir(guild_id, dados)
    except Exception as e:
        logger.error(f"Erro ao salvar dados_recompensa_exibir da guild {guild_id}: {e}")

def adicionar_reacao_coracao(guild_id: str, nome_personagem: str, user_id: str) -> int:
    """Adiciona um usuário à lista de reações de coração para um personagem e retorna o número atual de reações únicas."""
    dados = carregar_dados_recompensa_exibir(guild_id)
    # Normaliza o nome do personagem para consistência
    nome_normalizado = normalize(nome_personagem)
    # Inicializa a lista de usuários se não existir
    if nome_normalizado not in dados:
        dados[nome_normalizado] = []
    # Adiciona o usuário se ainda não reagiu
    if user_id not in dados[nome_normalizado]:
        dados[nome_normalizado].append(user_id)
    salvar_dados_recompensa_exibir(guild_id, dados)
    return len(dados[nome_normalizado])

def limpar_reacoes_coracao(guild_id: str, nome_personagem: str):
    """Limpa todas as reações de coração de um personagem após a recompensa ser concedida."""
    dados = carregar_dados_recompensa_exibir(guild_id)
    nome_normalizado = normalize(nome_personagem)
    if nome_normalizado in dados:
        dados[nome_normalizado] = []  # Reseta a lista de reações
        salvar_dados_recompensa_exibir(guild_id, dados)

def obter_quantidade_reacoes(guild_id: str, nome_personagem: str) -> int:
    """Retorna a quantidade de reações de coração únicas para um personagem."""
    dados = carregar_dados_recompensa_exibir(guild_id)
    nome_normalizado = normalize(nome_personagem)
    return len(dados.get(nome_normalizado, []))
