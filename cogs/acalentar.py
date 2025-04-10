import discord
from discord import Embed
from discord.ext import commands
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_guild, salvar_estatisticas_seguro, require_resgate, evento_esquecimento
import random
import asyncio
import time
from funcoes import maintenance_off, no_dm
from biscoitosorte import biscoito_sorte  # Importando a função biscoito_sorte

chaves_iniciais = {
    "uso_comando_acalentar": 0,
    "contribuicoes_totais_acalentar": 0,
    "doacoes_enviadas_acalentar": 0,
    "doacoes_recebidas_acalentar": 0,
    "premios_recebidos_acalentar": 0,
    "sorteios_vencidos_acalentar": 0
}

class Acalentar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chaves_iniciais = chaves_iniciais

    @commands.command(name="acalentar", help="Contribua com corações para a Bolsa do Acalentar. Uso: !!acalentar <quantidade> [@usuário opcional] ou !!acalentar para ver sua contribuição")
    @maintenance_off()
    @evento_esquecimento()
    @no_dm()
    @require_resgate
    async def acalentar(self, ctx, *, args: str = None):
        guild_id = str(ctx.guild.id)
        doador_id = str(ctx.author.id)
        dados = carregar_dados_guild(guild_id)

        # Verifica se a bolsa está indisponível para doações
        bolsa = dados.get("bolsa_acalentar")
        if bolsa and "disabled_until" in bolsa:
            if time.time() < bolsa["disabled_until"]:
                restante = int(bolsa["disabled_until"] - time.time())
                minutos = restante // 60
                segundos = restante % 60
                await ctx.send(f"❌ **A Bolsa do Acalentar está indisponível para novas doações. Por favor, aguarde {minutos} minuto(s) e {segundos} segundo(s).**")
                return

        # Inicializa e garante as estatísticas
        estatisticas = carregar_estatisticas_guild(guild_id)
        inserir_chaves_iniciais = estatisticas.setdefault("estatisticas_dos_usuarios", {}).setdefault(doador_id, {})
        inserir_chaves_iniciais.update({k: v for k, v in chaves_iniciais.items() if k not in inserir_chaves_iniciais})
        estatisticas.setdefault("acalentar", {
            "personagens_revelados_acalentar": 0,
            "biscoitos_sorteados_acalentar": 0,
            "sorteios_realizados_acalentar": 0,
            "coracoes_premios_bolsa_acalentar": 0,
            "coracoes_sorteio_acalentar": 0
        })
        estatisticas.setdefault("estatisticas_meus_personagens", {})
        estatisticas["estatisticas_dos_usuarios"][doador_id]["uso_comando_acalentar"] += 1

        # Inicializa a bolsa se não existir
        chaves_bolsa = {"total_corações": 0, "contribuidores": {}, "fator_extra": 0}
        if "bolsa_acalentar" not in dados:
            fator_extra = random.randint(0, 50)
            dados["bolsa_acalentar"] = {}
        bolsa = dados["bolsa_acalentar"]
        if "fator_extra" not in bolsa:
            bolsa["fator_extra"] = 0
        alvo = 300 + bolsa["fator_extra"]
        for k, v in chaves_bolsa.items():
            if k not in bolsa:
                bolsa[k] = v
                


        # Cálculo da cor do embed com transição suave
        total_atual = bolsa["total_corações"]
        if total_atual < (alvo - 15):
            f = total_atual / (alvo - 15)
            r = int(255 * f)
            g = int(255 * f)
            b = 255 - int(255 * f)
            embed_color = (r << 16) + (g << 8) + b
        elif total_atual < alvo:
            f2 = (total_atual - (alvo - 15)) / 15
            r = 255
            g = int(255 * (1 - f2))
            b = 0
            embed_color = (r << 16) + (g << 8) + b
        else:
            embed_color = 0xFF0000

        # Caso o usuário use apenas !!acalentar sem argumentos, exibe a contribuição atual
        if not args:
            user_contribution = bolsa["contribuidores"].get(doador_id, {"corações": 0, "numeros": []})
            num_contribuidores = len(bolsa["contribuidores"])
            hidden_count = len(dados.get("personagem_escondido", []))
            embed = Embed(
                title="Bolsa do Acalentar",
                description="Envie boas energias para nossos amigos em Equestria, contribuindo com corações. Cada usuário pode contribuir com até 50 corações.",
                color=embed_color
            )
            embed.add_field(name="Sua Contribuição", value=f"{user_contribution['corações']} corações", inline=False)
            embed.add_field(name="Contribuidores", value=f"{num_contribuidores} usuários", inline=False)
            # Exibe os personagens escondidos no rodapé
            embed.set_footer(text=f"Personagens Escondidos: {hidden_count}")
            await ctx.send(embed=embed)
            await salvar_estatisticas_seguro(guild_id, estatisticas)
            return

        # Separar os argumentos (quantidade e beneficiário)
        partes = args.split()
        quantidade = None
        beneficiario = None

        for parte in partes:
            if parte.isdigit():
                quantidade = int(parte)
            elif parte.startswith("<@") and parte.endswith(">"):
                try:
                    beneficiario = await commands.MemberConverter().convert(ctx, parte)
                except commands.MemberNotFound:
                    await ctx.send("❌ **Usuário mencionado não encontrado.**")
                    await salvar_estatisticas_seguro(guild_id, estatisticas)
                    return

        # Verificar se a quantidade foi fornecida
        if quantidade is None:
            await ctx.send("❌ **Você precisa informar a quantidade de corações (um número entre 1 e 50).**")
            await salvar_estatisticas_seguro(guild_id, estatisticas)
            return

        beneficiario_id = str(beneficiario.id) if beneficiario else doador_id  # Se não houver beneficiário, usa o doador

        # Apenas usuários que já resgataram um personagem podem receber doações
        usuarios = dados.setdefault("usuarios", {})
        beneficiario_data = usuarios.setdefault(beneficiario_id, {
            "coracao": 0,
            "quantidade_amor": 0,
            "trevo": 0,
            "changeling": [],
            "quantidade_recompensa": 0,
            "ultimo_reset_recompensa": 0,
            "receber_dm": False,
            "resgatou_personagem": False
        })
        if not beneficiario_data.get("resgatou_personagem", False):
            await ctx.send(f"❌ **<@{beneficiario_id}> ainda não resgatou nenhum personagem e, portanto, não pode receber doações.**")
            await salvar_estatisticas_seguro(guild_id, estatisticas)
            return

        # Verificar quantidade válida
        if quantidade <= 0 or quantidade > 50:
            await ctx.send("❌ **Quantidade inválida! Use entre 1 e 50 corações.**")
            await salvar_estatisticas_seguro(guild_id, estatisticas)
            return

        # Verificar corações do doador
        doador_data = usuarios.setdefault(doador_id, {
            "coracao": 0,
            "quantidade_amor": 0,
            "trevo": 0,
            "changeling": [],
            "quantidade_recompensa": 0,
            "ultimo_reset_recompensa": 0,
            "receber_dm": False,
            "resgatou_personagem": False
        })
        if doador_data["coracao"] < quantidade:
            await ctx.send("❌ **Você não tem corações suficientes!**")
            await salvar_estatisticas_seguro(guild_id, estatisticas)
            return

        # Verificar limite por beneficiário na bolsa
        beneficiario_contribution = bolsa["contribuidores"].get(beneficiario_id, {"corações": 0, "numeros": []})
        if beneficiario_contribution["corações"] + quantidade > 50:
            await ctx.send(f"❌ **<@{beneficiario_id}> só pode receber até 50 corações por bolsa! Já recebeu {beneficiario_contribution['corações']} corações.**")
            await salvar_estatisticas_seguro(guild_id, estatisticas)
            return

        # Deduzir corações do doador
        doador_data["coracao"] -= quantidade

        # Adicionar contribuição ao beneficiário
        total_antes = bolsa["total_corações"]
        bolsa["total_corações"] += quantidade
        beneficiario_contribution["corações"] = beneficiario_contribution.get("corações", 0) + quantidade
        bolsa["contribuidores"][beneficiario_id] = beneficiario_contribution

        # Atualizar estatísticas do usuário
        estatisticas["estatisticas_dos_usuarios"][doador_id]["contribuicoes_totais_acalentar"] += quantidade
        if beneficiario_id != doador_id:
            estatisticas["estatisticas_dos_usuarios"][doador_id]["doacoes_enviadas_acalentar"] += quantidade

            inserir_chaves_beneficiario = estatisticas["estatisticas_dos_usuarios"].setdefault(beneficiario_id, {})
            inserir_chaves_beneficiario.update({k: v for k, v in chaves_iniciais.items() if k not in inserir_chaves_beneficiario})
            estatisticas["estatisticas_dos_usuarios"][beneficiario_id]["doacoes_recebidas_acalentar"] += quantidade

        # Atualiza novamente a cor do embed com base no novo total
        total_atual = bolsa["total_corações"]
        if total_atual < (alvo - 15):
            f = total_atual / (alvo - 15)
            r = int(255 * f)
            g = int(255 * f)
            b = 255 - int(255 * f)
            embed_color = (r << 16) + (g << 8) + b
        elif total_atual < alvo:
            f2 = (total_atual - (alvo - 15)) / 15
            r = 255
            g = int(255 * (1 - f2))
            b = 0
            embed_color = (r << 16) + (g << 8) + b
        else:
            embed_color = 0xFF0000

        # Cria embed de resposta e adiciona o rodapé com os personagens escondidos
        hidden_count = len(dados.get("personagem_escondido", []))
        embed = Embed(
            title="Bolsa do Acalentar",
            description="Envie boas energias para nossos amigos em Equestria, contribuindo com corações. Cada usuário pode contribuir com até 50 corações.",
            color=embed_color
        )
        if beneficiario_id == doador_id:
            embed.add_field(name="Sua Contribuição", value=f"{beneficiario_contribution['corações']} corações", inline=False)
        else:
            embed.add_field(name="Doação", value=f"<@{doador_id}> doou {quantidade} corações para <@{beneficiario_id}>!", inline=False)
            embed.add_field(name=f"Contribuição de <@{beneficiario_id}>", value=f"{beneficiario_contribution['corações']} corações", inline=False)
        embed.set_footer(text=f"Personagens Escondidos: {hidden_count}")
        await ctx.send(embed=embed)

        # Verificar se a bolsa encheu e premiar o doador
        if bolsa["total_corações"] >= alvo:
            premio = random.randint(10, 25)
            doador_data["coracao"] += premio
            estatisticas["estatisticas_dos_usuarios"][doador_id]["premios_recebidos_acalentar"] += premio
            estatisticas["acalentar"]["coracoes_premios_bolsa_acalentar"] += premio
            await ctx.send(f"🎁 **<@{doador_id}> encheu a Bolsa do Acalentar e ganhou {premio} corações como prêmio especial!**")

        salvar_dados_guild(guild_id, dados)
        await salvar_estatisticas_seguro(guild_id, estatisticas)

        # Verificar se a bolsa encheu para realizar o sorteio (usando o novo alvo)
        if bolsa["total_corações"] >= alvo:
            # Movimentar personagens escondidos para "personagens"
            hidden = dados.get("personagem_escondido", [])
            if hidden:
                # Se houver 5 ou menos, mover todos; se mais, escolher 5 aleatórios
                if len(hidden) <= 5:
                    for personagem in hidden:
                        # Se já existir um personagem com mesmo nome em "personagens", substitui-o
                        personagens = dados.setdefault("personagens", [])
                        personagens = [p for p in personagens if p["nome"] != personagem["nome"]]
                        personagens.append(personagem)
                        dados["personagens"] = personagens
                    dados["personagem_escondido"] = []
                else:
                    escolhidos = random.sample(hidden, 5)
                    for personagem in escolhidos:
                        personagens = dados.setdefault("personagens", [])
                        personagens = [p for p in personagens if p["nome"] != personagem["nome"]]
                        personagens.append(personagem)
                        dados["personagens"] = personagens
                    dados["personagem_escondido"] = [p for p in hidden if p not in escolhidos]
            
            # Mover todos os personagens do "lar_do_unicornio" para "personagens"
            lar = dados.get("lar_do_unicornio", [])
            if lar:
                for personagem in lar:
                    personagens = dados.setdefault("personagens", [])
                    personagens = [p for p in personagens if p["nome"] != personagem["nome"]]
                    personagens.append(personagem)
                    dados["personagens"] = personagens
                dados["lar_do_unicornio"] = []
            salvar_dados_guild(guild_id, dados)

            await self.realizar_sorteio(ctx, guild_id)

    async def realizar_sorteio(self, ctx, guild_id):
        dados = carregar_dados_guild(guild_id)
        bolsa = dados["bolsa_acalentar"]
        contribuidores = bolsa["contribuidores"]
        estatisticas = carregar_estatisticas_guild(guild_id)

        # Atribuir números aos contribuidores
        todos_numeros = list(range(1, 301))  # 1 a 300
        random.shuffle(todos_numeros)
        numero_pos = 0
        for user_id, info in contribuidores.items():
            quantidade = info["corações"]
            info["numeros"] = todos_numeros[numero_pos:numero_pos + quantidade]
            numero_pos += quantidade

        # Sortear o vencedor
        numero_vencedor = random.randint(1, 300)
        vencedor_id = None
        for user_id, info in contribuidores.items():
            if numero_vencedor in info["numeros"]:
                vencedor_id = user_id
                break

        embed = Embed(
            title="🎉 Sorteio da Bolsa do Acalentar!",
            description=f"Obrigado a todos por espalhar amor!",
            color=0x00FF00
        )
        usuario_valido = False
        if vencedor_id:
            try:
                vencedor = await ctx.guild.fetch_member(int(vencedor_id))
                if vencedor:
                    usuario_valido = True
                    embed.add_field(name="Vencedor", value=f"<@{vencedor_id}>", inline=False)
                    embed.add_field(name="Prêmio", value="100 corações", inline=False)
                    # Adicionar corações ao vencedor
                    usuarios = dados["usuarios"]
                    usuario_vencedor = usuarios.setdefault(vencedor_id, {"coracao": 0, "quantidade_amor": 0, "trevo": 0, "changeling": [], "quantidade_recompensa": 0, "ultimo_reset_recompensa": 0, "receber_dm": False, "resgatou_personagem": False})
                    usuario_vencedor["coracao"] += 100
                    inserir_chaves_vencedor = estatisticas["estatisticas_dos_usuarios"].setdefault(vencedor_id, {})
                    inserir_chaves_vencedor.update({k: v for k, v in chaves_iniciais.items() if k not in inserir_chaves_vencedor})
                    estatisticas["estatisticas_dos_usuarios"][vencedor_id]["sorteios_vencidos_acalentar"] += 1
                    estatisticas["acalentar"]["coracoes_sorteio_acalentar"] += 100
            except (discord.NotFound, discord.HTTPException):
                pass

        if not usuario_valido:
            embed.add_field(name="Vencedor", value="O usuário sorteado é inválido", inline=False)
            embed.add_field(name="Prêmio", value="A recompensa foi perdida!", inline=False)

        await ctx.send(embed=embed)

        # Notificar contribuidores por DM (caso a DM não seja possível, continua sem erro)
        server_name = ctx.guild.name
        usuarios = dados.get("usuarios", {})
        for contribuidor_id in contribuidores.keys():
            user_data = usuarios.get(contribuidor_id, {"receber_dm": False})
            if user_data.get("receber_dm", False):
                try:
                    usuario = await self.bot.fetch_user(int(contribuidor_id))
                    if usuario:
                        if contribuidor_id == vencedor_id and usuario_valido:
                            await usuario.send(f"🎉 Você foi sorteado na Bolsa do Acalentar no servidor **{server_name}** e ganhou 100 corações!")
                        else:
                            await usuario.send(f"O sorteio da Bolsa do Acalentar aconteceu no servidor **{server_name}**, mas você não foi sorteado dessa vez.")
                except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                    continue

        # Definir a bolsa como indisponível por 1 hora
        bolsa["disabled_until"] = time.time() + 3600

        # Esvaziar a bolsa e resetar as contribuições (opcional, se preferir manter dados durante o bloqueio, adapte conforme necessário)
        dados["bolsa_acalentar"] = {"total_corações": 0, "contribuidores": {}, "fator_extra": random.randint(0, 50), "disabled_until": bolsa["disabled_until"]}
        salvar_dados_guild(guild_id, dados)

        # Aguardar atraso aleatório para a surpresa
        await asyncio.sleep(random.uniform(1, 30))

        # Verificar personagens disponíveis e carregar dados atualizados
        dados = carregar_dados_guild(guild_id)
        personagens = dados.get("personagens", [])
        if personagens:
            personagem_revelado = random.choice(personagens)
            await ctx.send(f"🌟 Uma energia especial revelou o nome de um pônei em Equestria: **{personagem_revelado['nome']}**!")
            estatisticas["acalentar"]["personagens_revelados_acalentar"] += 1
            nome_original = personagem_revelado["nome"]
            inserir_chaves_personagem = estatisticas["estatisticas_meus_personagens"].setdefault(nome_original, {})
            chaves_iniciais_personagem = {"nome_revelado_acalentar": 0}
            inserir_chaves_personagem.update({k: v for k, v in chaves_iniciais_personagem.items() if k not in inserir_chaves_personagem})
            estatisticas["estatisticas_meus_personagens"][nome_original]["nome_revelado_acalentar"] += 1
        else:
            await biscoito_sorte(ctx.channel, 'acalentar')
            estatisticas["acalentar"]["biscoitos_sorteados_acalentar"] += 1

        estatisticas["acalentar"]["sorteios_realizados_acalentar"] += 1
        await salvar_estatisticas_seguro(guild_id, estatisticas)


async def setup(bot):
    await bot.add_cog(Acalentar(bot))
