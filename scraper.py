import urllib.request
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

FILE_PATH = "megasena.json"
BASE_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    max_retries = 3
    for _ in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            time.sleep(1)
    return None

def main():
    # Load existing data
    data = []
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
            
    # Find highest existing
    existing_concursos = {item['concurso']: item for item in data}
    highest = max(existing_concursos.keys()) if existing_concursos else 0

    print(f"Buscando o concurso mais recente...")
    latest_data = fetch_json(BASE_URL)
    if not latest_data:
        print("Erro ao tentar ler o concurso mais recente.")
        return
        
    latest_num = latest_data.get('numero')
    print(f"Último concurso sorteado: {latest_num}")
    
    missing = [i for i in range(1, latest_num + 1) if i not in existing_concursos]
    if not missing:
        print("A base de dados já está 100% atualizada!")
        return
        
    print(f"Faltam {len(missing)} concursos. Baixando...")
    
    # Fetch missing
    def fetch_missing(i):
        res = fetch_json(f"{BASE_URL}/{i}")
        if res and 'numero' in res and 'listaDezenas' in res:
            return {"concurso": res['numero'], "dezenas": res['listaDezenas']}
        return None

    new_items = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_i = {executor.submit(fetch_missing, i): i for i in missing}
        total = len(missing)
        done = 0
        for future in as_completed(future_to_i):
            done += 1
            res = future.result()
            if res:
                new_items.append(res)
            if done % 100 == 0:
                print(f"Progresso: {done}/{total} baixados...")

    for item in new_items:
        existing_concursos[item['concurso']] = item
        
    # Rebuild sorted list
    final_data = [existing_concursos[k] for k in sorted(existing_concursos.keys())]
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"Salvo {len(final_data)} resultados totais no arquivo '{FILE_PATH}'.")

if __name__ == "__main__":
    main()
