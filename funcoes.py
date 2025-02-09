# funcoes.py

import json
import discord
from discord.ext import commands
import os
import random
import json
import random
import asyncio
import globals


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


# Variável global para o modo de teste
modo_de_teste = False

# Função para verificar se o usuário tem permissão de moderador
def apenas_moderador():
    async def predicado(ctx):
        if modo_de_teste:  # Se o modo de teste estiver ativado, qualquer usuário pode usar o comando
            return True

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



'''se der erro quando subir pra algum lugar, o erro ta nesse os aqui VVV'''

def verificar_imagem(imagem):
    if os.path.isfile(imagem):
        return imagem
    else:
        return "resources/poneis/semimagem.png"
    
def sortear_naoencontrado():
    # Caminho da pasta onde estão as imagens
    caminho_pasta = "resources/poneis/Naoencontrado"  # Substitua pelo caminho correto

    # Lista todos os arquivos na pasta e filtra para manter apenas arquivos de imagem
    imagens = [arquivo for arquivo in os.listdir(caminho_pasta) if arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

    # Verifica se há imagens na pasta
    if imagens:
        imagem_sorteada = random.choice(imagens)
        return (f"resources/poneis/Naoencontrado/" + imagem_sorteada)
    else:
        return "resources/poneis/semimagem.png"


def carregar_token():
    caminho_env = os.path.join(os.path.dirname(os.getcwd()), ".env")

    if os.path.exists(caminho_env):
        with open(caminho_env, "r") as f:
            return(f.read())
    else:
        print("Arquivo .env não encontrado ou sem permissão.")