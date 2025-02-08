import json

with open('resources/dados.json') as a:
    dados = json.load(a)


print(dados['personagens_por_usuario'])

for usuario, campos in dados['personagens_por_usuario'].items():
    for a in campos:
        print(a['nome'], a['especie'])