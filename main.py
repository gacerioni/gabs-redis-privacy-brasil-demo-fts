"""
Privacy Brasil demo: creators search with synonyms, fuzzy, stemming, phonetic, and alias field.
Run:  python demo_privacy_brasil_search.py
Requires: pip install redis
Start Redis Stack: docker run -p 6379:6379 redis/redis-stack:latest
"""

import json
from redis import Redis

R = Redis(host="localhost", port=6379, decode_responses=True)

INDEX = "idx:creators"
PREFIX = "creator:"

def reset():
    try:
        R.execute_command("FT.DROPINDEX", INDEX, "DD")
    except Exception:
        pass
    keys = R.keys(f"{PREFIX}*")
    if keys:
        R.delete(*keys)

def seed_data():
    creators = [
        {"id": "andressa-urach", "name": "Andressa Urach",
         "tags": ["brasil", "influencer", "tv"],
         "bio_pt": "Criadora de conteúdo e apresentadora. Conhecida em reality shows.",
         # Multi-word alias stored here so it is searchable (synonym groups do not expand phrases)
         "aka": ["miss bumbum"]},

        {"id": "joao-silva", "name": "João Silva", "tags": ["brasil", "podcaster"],
         "bio_pt": "Apresentador e criador de entrevistas semanais."},
        {"id": "maria-oliveira", "name": "Maria Oliveira", "tags": ["vlog", "moda"],
         "bio_pt": "Criadora brasileira com foco em moda e beleza."},
        {"id": "carlos-pereira", "name": "Carlos Pereira", "tags": ["tech"],
         "bio_pt": "Faz tutoriais de tecnologia e programação."},
        {"id": "ana-souza", "name": "Ana Souza", "tags": ["culinaria"],
         "bio_pt": "Receitas práticas e apresentações de cozinha ao vivo."},
        {"id": "pedro-lima", "name": "Pedro Lima", "tags": ["games"],
         "bio_pt": "Lives de jogos e análise de lançamentos."},
        {"id": "luiza-costa", "name": "Luiza Costa", "tags": ["viagem"],
         "bio_pt": "Vlogs de viagem e guias de destinos brasileiros."},
        {"id": "rafael-gomes", "name": "Rafael Gomes", "tags": ["musica"],
         "bio_pt": "Cantor e compositor, apresentações semanais."},
        {"id": "bianca-fernandes", "name": "Bianca Fernandes", "tags": ["beleza"],
         "bio_pt": "Dicas de skincare e resenhas de produtos."},
        {"id": "thiago-rocha", "name": "Thiago Rocha", "tags": ["humor"],
         "bio_pt": "Esquetes curtas e stand-up."},
        {"id": "camila-cardoso", "name": "Camila Cardoso", "tags": ["educacao"],
         "bio_pt": "Aulas de matemática e apresentações didáticas."},
        {"id": "gabriel-torres", "name": "Gabriel Torres", "tags": ["tech", "ai"],
         "bio_pt": "Conteúdo sobre IA e engenharia de dados."},
        {"id": "lara-almeida", "name": "Lara Almeida", "tags": ["fitness"],
         "bio_pt": "Treinos funcionais, apresentando variações para iniciantes."},
        {"id": "vinicius-ribeiro", "name": "Vinícius Ribeiro", "tags": ["filmes"],
         "bio_pt": "Críticas de cinema e análises de trailers."},
        {"id": "natalia-martins", "name": "Natália Martins", "tags": ["arte"],
         "bio_pt": "Apresenta técnicas de pintura e ilustração."},
        {"id": "rodrigo-santos", "name": "Rodrigo Santos", "tags": ["negocios"],
         "bio_pt": "Empreendedorismo e cases de startups brasileiras."},
        {"id": "aline-barbosa", "name": "Aline Barbosa", "tags": ["bem-estar"],
         "bio_pt": "Meditação guiada e respiração."},
        {"id": "henrique-lopes", "name": "Henrique Lopes", "tags": ["esportes"],
         "bio_pt": "Cobertura de futebol e apresentações pós-jogo."},
        {"id": "paula-araujo", "name": "Paula Araújo", "tags": ["livros"],
         "bio_pt": "Clube do livro com resenhas semanais."},
        {"id": "andrea-campos", "name": "Andrea Campos", "tags": ["fotografia"],
         "bio_pt": "Demonstra edições e composição fotográfica."},
        {"id": "julio-azevedo", "name": "Júlio Azevedo", "tags": ["historia"],
         "bio_pt": "Curiosidades históricas e apresentações curtas."},
        {"id": "tati-melo", "name": "Tati Melo", "tags": ["make"],
         "bio_pt": "Tutoriais de maquiagem acessível."},
        {"id": "felipe-dias", "name": "Felipe Dias", "tags": ["podcast", "negocios"],
         "bio_pt": "Entrevistas com fundadores e investidores."},
        {"id": "sofia-nunes", "name": "Sofia Nunes", "tags": ["infantil"],
         "bio_pt": "Conteúdo educativo para crianças."},
        {"id": "marcos-teixeira", "name": "Marcos Teixeira", "tags": ["carros"],
         "bio_pt": "Análises de carros e test drives."},
    ]

    for c in creators:
        key = f"{PREFIX}{c['id']}"
        payload = {
            "name": c["name"],
            "tags": c["tags"],
            "bio_pt": c["bio_pt"],
            "customer": "Privacy Brasil",
        }
        if "aka" in c:
            payload["aka"] = c["aka"]
        else:
            payload["aka"] = []  # keep shape consistent

        R.execute_command("JSON.SET", key, "$", json.dumps(payload))

def create_index():
    # Build with raw FT.CREATE so we can pass LANGUAGE + PHONETIC + JSON paths cleanly.
    try:
        R.execute_command(
            "FT.CREATE", INDEX,
            "ON", "JSON",
            "PREFIX", "1", PREFIX,
            "LANGUAGE", "portuguese",
            "SCHEMA",
            "$.name", "AS", "name", "TEXT", "PHONETIC", "dm:pt", "WEIGHT", "5.0",
            "$.bio_pt", "AS", "bio", "TEXT",
            "$.tags[*]", "AS", "tags", "TAG",
            "$.customer", "AS", "customer", "TAG",
            "$.aka[*]", "AS", "aka", "TEXT"  # multi-word aliases / nicknames
        )
    except Exception as e:
        if "Index already exists" not in str(e):
            raise

def add_synonyms():
    # Synonym groups expand **single tokens only**. Keep single-token variants here.
    # (Multi-word alias like "miss bumbum" is handled via the `aka` field above.)
    terms = [
        "andressa", "urach",
        "andresa", "andréssa", "uraque", "andressa-urach", "rabeta", "maluca"
    ]
    R.execute_command("FT.SYNUPDATE", INDEX, "syn:andressa", *terms)

def ft_search(query_str, sortby=None, asc=True):
    # RAW FT.SEARCH with LANGUAGE portuguese; return select fields
    cmd = [
        "FT.SEARCH", INDEX, query_str,
        "LANGUAGE", "portuguese",
    ]
    if sortby:
        cmd += ["SORTBY", sortby, "ASC" if asc else "DESC"]
    cmd += ["RETURN", "4", "name", "tags", "bio", "customer"]
    resp = R.execute_command(*cmd)
    total = resp[0] if resp else 0
    items = []
    i = 1
    while i < len(resp):
        key = resp[i]
        fields = resp[i+1]
        doc = {"id": key}
        for j in range(0, len(fields), 2):
            doc[fields[j]] = fields[j+1]
        items.append(doc)
        i += 2
    return total, items

def search_examples():
    tests = [
        ("Exact name", r'@name:"Andressa Urach" @customer:{Privacy\ Brasil}'),
        ("Alias field (term 'miss bumbum')", '@aka:"miss bumbum"'),
        ("Fuzzy LD=1 on name ('%andresa%')", '@name:(%andresa%)'),
        ("Fuzzy LD=2 on surname ('%%uratch%%')", '@name:(%%uratch%%)'),
        ("Phonetic on ('Andresa Oraki' ~ 'Andressa Urach')", '@name:(Andresa Oraki)'),
        ("Portuguese stemming on bio ('@bio:apresentações')", '@bio:(apresentações)'),
        ("Synonym group (term 'uraque')", '@name:(uraque)'),
        ("Synonym group (term 'andresa')", '@name:(andresa)'),
        ("Synonym group (term 'rabeta')", '@name:(rabeta)'),
        ("Synonym group (term 'maluca')", '@name:(maluca)'),

    ]
    for label, q in tests:
        print("\n=== " + label + " ===")
        total, items = ft_search(q)
        print(f"Total: {total}")
        for d in items:
            print(f"- {d['id']} | name={d.get('name')} | tags={d.get('tags')} | customer={d.get('customer')}")

def main():
    reset()
    seed_data()
    create_index()
    add_synonyms()
    search_examples()
    dumped = R.execute_command("FT.SYNDUMP", INDEX)
    print("\nSYNDUMP:", dumped)

if __name__ == "__main__":
    main()