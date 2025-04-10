# mensagenssorte.py (na raiz do projeto)
import discord
import random
import asyncio
from biscoitosorte import biscoito_sorte  # Importando a nova função
import globals
from server_data import carregar_dados_guild

async def enviar_sorte_automatico(bot, guild_id):
    """
    Envia automaticamente o biscoito da sorte a cada intervalo definido no JSON do servidor.
    """
    while True:
        dados = carregar_dados_guild(guild_id)
        tempo_sorte = dados.get("tempo_sorte", globals.tempo_sorte)
        await asyncio.sleep(tempo_sorte + random.randint(0, int(tempo_sorte / 3)))

        # Recarrega os dados para garantir que as informações estejam atualizadas
        dados = carregar_dados_guild(guild_id)
        
        canal_id = dados.get("ID_DO_CANAL_SORTE")
        if canal_id is None:
            print(f"[SORTE] Canal para sorte não configurado na guild {guild_id}. Pulando envio.")
            continue

        canal = bot.get_channel(canal_id)
        if canal is None:
            print(f"[SORTE] Canal com ID {canal_id} não encontrado na guild {guild_id}.")
            continue

        await biscoito_sorte(canal, 'sorte_automatico')  # Usando a função refatorada