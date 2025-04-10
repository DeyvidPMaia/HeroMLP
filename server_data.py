#server_data.py 24/03/2025 00:00 (atualizado para novo caminho)

import os
import json
import logging
from funcoes import carregar_personagens  # Certifique-se de que essa função está disponível
import functools
import asyncio
import logging


logger = logging.getLogger(__name__)

def caminho_dados_guild(guild_id):
    return f"resources/servidores/{guild_id}.json"

def carregar_dados_guild(guild_id):
    caminho = caminho_dados_guild(guild_id)
    
    # Se o arquivo não existe, cria um novo com valores padrão
    if not os.path.exists(caminho):
        print(f"[INFO] Criando novo arquivo de dados para a guild {guild_id}.")
        dados_iniciais = criar_dados_iniciais()
        salvar_dados_guild(guild_id, dados_iniciais)
        return dados_iniciais

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"[ERRO] Arquivo {caminho} corrompido. Criando um novo.")
        dados_iniciais = criar_dados_iniciais()
        salvar_dados_guild(guild_id, dados_iniciais)
        return dados_iniciais
    except Exception as e:
        print(f"[ERRO] Falha ao carregar dados da guild {guild_id}: {e}")
        return criar_dados_iniciais()  # Retorna um dicionário padrão para evitar erros no código

def criar_dados_iniciais():
    return {
        "personagens": carregar_personagens(),
        "personagens_salvos": [],
        "contador_personagens_salvos": {},
        "personagens_por_usuario": {},
        "tempo_impedimento": 3600,
        "personagem_escondido": [],
        "usuarios": {},
        "lar_do_unicornio": []
    }

def salvar_dados_guild(guild_id, dados):
    caminho = caminho_dados_guild(guild_id)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    # Criar backup antes de salvar
    if os.path.exists(caminho):
        backup_caminho = f"{caminho}.bak"
        os.replace(caminho, backup_caminho)

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERRO] Falha ao salvar dados da guild {guild_id}: {e}")


def evento_esquecimento():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            # Verifica se o comando está sendo executado em um servidor
            if ctx.guild is None:
                return await func(self, ctx, *args, **kwargs)
            # Carrega os dados do servidor
            dados = carregar_dados_guild(str(ctx.guild.id))
            # Se o campo 'evento_esquecimento_ocorrendo' for True, bloqueia o comando
            if dados.get("evento_esquecimento_ocorrendo", False):
                await ctx.send("❌ **Evento de esquecimento em curso. Espere até que as trevas se dissipem.**")
                return
            # Caso contrário, executa normalmente
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator

def caminho_estatisticas_guild(guild_id):  # Adicionei essa função que estava implícita
    return f"resources/servidores/{guild_id}/estatisticas/ponymemories_estatisticas.json"

def carregar_estatisticas_guild(guild_id):
    caminho = caminho_estatisticas_guild(guild_id)
    
    # Se o arquivo não existe, cria um novo com valores padrão
    if not os.path.exists(caminho):
        logger.info(f"Criando novo arquivo de estatísticas para a guild {guild_id}.")
        estatisticas_iniciais = {"estatisticas_meus_usuarios": {}}
        salvar_estatisticas_guild(guild_id, estatisticas_iniciais)
        return estatisticas_iniciais

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Arquivo {caminho} corrompido. Criando um novo.")
        estatisticas_iniciais = {"usuarios": {}}
        salvar_estatisticas_guild(guild_id, estatisticas_iniciais)
        return estatisticas_iniciais
    except Exception as e:
        logger.error(f"Falha ao carregar estatísticas da guild {guild_id}: {e}")
        return {"usuarios": {}}

def salvar_estatisticas_guild(guild_id, estatisticas):
    caminho = caminho_estatisticas_guild(guild_id)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    # Criar backup antes de salvar
    if os.path.exists(caminho):
        backup_caminho = f"{caminho}.bak"
        os.replace(caminho, backup_caminho)

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(estatisticas, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Falha ao salvar estatísticas da guild {guild_id}: {e}")
        # Tenta restaurar o backup em caso de falha
        if os.path.exists(backup_caminho):
            os.replace(backup_caminho, caminho)
        raise  # Relevanta o erro para ser capturado por salvar_estatisticas_seguro

async def salvar_estatisticas_seguro(guild_id: str, estatisticas: dict):
    """
    Salva as estatísticas da guild de forma segura, logando erros sem propagá-los.
    """
    try:
        salvar_estatisticas_guild(guild_id, estatisticas)
        logger.debug(f"Estatísticas salvas com sucesso para a guild {guild_id}")
    except Exception as e:
        logger.error(f"Erro ao salvar estatísticas da guild {guild_id}: {e}")


def caminho_estatisticas_usuario(guild_id: str, user_id: str) -> str:
    """Retorna o caminho do arquivo de estatísticas para um usuário."""
    return f"resources/servidores/{guild_id}/estatisticas/{user_id}/Estatisticas.json"

def carregar_estatisticas_usuario(guild_id: str, user_id: str) -> dict:
    """Carrega as estatísticas de um usuário."""
    caminho = caminho_estatisticas_usuario(guild_id, user_id)
    
    if not os.path.exists(caminho):
        logger.info(f"Criando novo arquivo de estatísticas para {user_id} na guild {guild_id}.")
        estatisticas_iniciais = {}
        salvar_estatisticas_usuario(guild_id, user_id, estatisticas_iniciais)
        return estatisticas_iniciais

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Arquivo {caminho} corrompido. Criando um novo.")
        estatisticas_iniciais = {}
        salvar_estatisticas_usuario(guild_id, user_id, estatisticas_iniciais)
        return estatisticas_iniciais
    except Exception as e:
        logger.error(f"Falha ao carregar estatísticas de {user_id} na guild {guild_id}: {e}")
        return {}

def salvar_estatisticas_usuario(guild_id: str, user_id: str, estatisticas: dict):
    """Salva as estatísticas de um usuário."""
    caminho = caminho_estatisticas_usuario(guild_id, user_id)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    # Backup antes de salvar
    if os.path.exists(caminho):
        backup_caminho = f"{caminho}.bak"
        os.replace(caminho, backup_caminho)

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(estatisticas, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Falha ao salvar estatísticas de {user_id} na guild {guild_id}: {e}")
        if os.path.exists(backup_caminho):
            os.replace(backup_caminho, caminho)
        raise

async def salvar_estatisticas_seguro_usuario(guild_id: str, user_id: str, estatisticas: dict):
    """Salva as estatísticas de forma segura, logando erros sem propagá-los."""
    try:
        salvar_estatisticas_usuario(guild_id, user_id, estatisticas)
        logger.debug(f"Estatísticas de {user_id} salvas com sucesso na guild {guild_id}")
    except Exception as e:
        logger.error(f"Erro ao salvar estatísticas de {user_id} na guild {guild_id}: {e}")

def require_resgate(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        # Carrega os dados da guild
        dados = carregar_dados_guild(guild_id)
        usuarios = dados.get("usuarios", {})
        user_data = usuarios.get(user_id, {})
        
        # Se o usuário não tiver resgatado nenhum personagem ainda, envia a mensagem de erro
        if not user_data.get("resgatou_personagem", False):
            await ctx.send("Você precisa já ter resgatado ao menos um personagem para usar este comando")
            return
        
        return await func(self, ctx, *args, **kwargs)
    return wrapper


def caminho_dados_recompensa_exibir(guild_id: str) -> str:
    """Retorna o caminho do arquivo de dados de recompensa para exibir."""
    return f"resources/servidores/{guild_id}/dados_recompensa_exibir.json"

def carregar_dados_recompensa_exibir(guild_id: str) -> dict:
    """Carrega os dados de recompensa de exibição para a guild."""
    caminho = caminho_dados_recompensa_exibir(guild_id)
    
    # Se o arquivo não existe, cria um novo com valores padrão
    if not os.path.exists(caminho):
        logger.info(f"Criando novo arquivo de dados de recompensa exibir para a guild {guild_id}.")
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
        logger.error(f"Falha ao carregar dados de recompensa exibir da guild {guild_id}: {e}")
        return {}
#novas funcões para exibir
def salvar_dados_recompensa_exibir(guild_id: str, dados: dict):
    """Salva os dados de recompensa de exibição para a guild."""
    caminho = caminho_dados_recompensa_exibir(guild_id)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    # Criar backup antes de salvar
    if os.path.exists(caminho):
        backup_caminho = f"{caminho}.bak"
        os.replace(caminho, backup_caminho)

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Falha ao salvar dados de recompensa exibir da guild {guild_id}: {e}")
        # Tenta restaurar o backup em caso de falha
        if os.path.exists(backup_caminho):
            os.replace(backup_caminho, caminho)
        raise  # Relevanta o erro para ser capturado por salvar_dados_seguro

async def salvar_dados_recompensa_exibir_seguro(guild_id: str, dados: dict):
    """Salva os dados de recompensa de exibição de forma segura, logando erros sem propagá-los."""
    try:
        salvar_dados_recompensa_exibir(guild_id, dados)
        logger.debug(f"Dados de recompensa exibir salvos com sucesso para a guild {guild_id}")
    except Exception as e:
        logger.error(f"Erro ao salvar dados de recompensa exibir da guild {guild_id}: {e}")