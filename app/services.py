import os
import re
import json
import csv
import cv2
import requests
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
from requests.auth import HTTPBasicAuth
from .config import TWILIO_SID, TWILIO_AUTH, AZURE_ENDPOINT, AZURE_KEY


def converter_pdf_para_imagem(caminho_arquivo: str) -> str | None:
    """Verifica se um arquivo é PDF e o converte para uma imagem JPG."""
    caminho_path = Path(caminho_arquivo)
    if caminho_path.suffix.lower() != '.pdf':
        print(f"ℹ️ Arquivo '{caminho_path.name}' não é PDF. Nenhuma conversão necessária.")
        return caminho_arquivo
    caminho_imagem_saida = caminho_path.with_suffix('.jpg')
    print(f"⏳ Convertendo PDF '{caminho_path.name}' para imagem...")
    try:
        paginas = convert_from_path(caminho_arquivo, dpi=300, first_page=1, last_page=1)
        if paginas:
            paginas[0].save(caminho_imagem_saida, 'JPEG')
            print(f"✅ PDF convertido com sucesso para '{caminho_imagem_saida.name}'")
            return str(caminho_imagem_saida)
        else:
            raise PDFPageCountError("O arquivo PDF está vazio ou não contém páginas válidas.")
    except Exception as e:
        print(f"❌ Falha ao converter o PDF '{caminho_path.name}'. Erro: {e}")
        return None


def carregar_principios_ativos():
    """Carrega a lista de princípios ativos a partir de um arquivo CSV."""
    # O caminho é relativo à localização deste arquivo de serviço
    caminho = Path(__file__).resolve().parent / 'principios_ativos.csv'
    principios = set()
    try:
        with open(caminho, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if row and row[0]:
                    principios.add(row[0].strip().lower())
    except Exception as e:
        print(f"Erro ao carregar CSV 'principios_ativos.csv': {e}")
    return principios


PRINCIPIOS_ATIVOS = carregar_principios_ativos()


def buscar_openfda(nome: str) -> str:
    """Consulta a API do OpenFDA como um fallback para nomes de medicamentos."""
    try:
        q = nome.replace(" ", "+")
        url = f"https://api.fda.gov/drug/label.json?search=generic_name:{q}&limit=1"
        resp = requests.get(url)
        if resp.status_code == 200:
            res = resp.json().get("results", [])
            if res:
                return res[0].get("openfda", {}).get("brand_name", [None])[0] or res[0].get("generic_name")
    except:
        pass
    return None


def _limpar_nomes_medicamentos(lista_bruta: list) -> list:
    medicamentos = list(set(m.strip() for m in lista_bruta))
    a_remover = set()
    for med_a in medicamentos:
        for med_b in medicamentos:
            if med_a != med_b and med_b in med_a:
                a_remover.add(med_a)
    return [m for m in medicamentos if m not in a_remover]


def encontrar_todos_os_medicamentos(texto: str) -> list:
    medicamentos_encontrados = []

    unidades = "(?:g/ml|g|mg|mcg|ml|ui|%)"
    padrao_numero = r"\d+(?:[.,]\d+)?"
    blacklist = r"(?!Aplicar|Tomar|Usar|Dias|Iniciar|Término|Após|Mar|Das)"

    for p in PRINCIPIOS_ATIVOS:
        regex_principio = rf"({re.escape(p)}\s+{padrao_numero}\s?{unidades})\b"
        matches = re.findall(regex_principio, texto, re.IGNORECASE)
        medicamentos_encontrados.extend(matches)

    regex_fallback = rf"\b{blacklist}([A-Z][a-zçãõáéíúâê\-]+(?:\s+[A-Za-zçãõáéíúâê\-]+)?\s+{padrao_numero}\s?{unidades})\b"
    matches_fallback = re.findall(regex_fallback, texto, re.IGNORECASE)
    medicamentos_encontrados.extend(matches_fallback)

    if not medicamentos_encontrados:
        return []

    medicamentos_limpos = _limpar_nomes_medicamentos(medicamentos_encontrados)
    return [med.title() for med in medicamentos_limpos]


def extrair_quantidade_total(nome_medicamento: str, texto_completo: str) -> str:
    try:
        texto_apos_medicamento_match = re.search(re.escape(nome_medicamento), texto_completo, re.IGNORECASE)
        if not texto_apos_medicamento_match:
            return "Não identificado"

        texto_relevante = texto_completo[texto_apos_medicamento_match.end():]
        padrao_forma = r"(comprimido|cápsula|gota)s?"

        padrao_posologia = rf"\s*[-–—:]*\s*(\d+)\s*{padrao_forma}.*?(\d+)\s*x.*?(\d+)\s*dias"
        match = re.search(padrao_posologia, texto_relevante, re.IGNORECASE)
        if match:
            quantidade, forma, vezes_dia, dias = match.groups()
            total = int(quantidade) * int(vezes_dia) * int(dias)
            return f"{total} {forma}s"

        padrao_simples = rf"\s*[-–—:]*\s*(\d+)\s*{padrao_forma}.*?(\d+)\s*dias"
        match_simples = re.search(padrao_simples, texto_relevante, re.IGNORECASE)
        if match_simples:
            quantidade, forma, dias = match_simples.groups()
            total = int(quantidade) * int(dias)
            return f"{total} {forma}s"
    except Exception:
        pass
    return "Não identificado"


def salvar_arquivo(media_url: str, sender: str) -> str:
    os.makedirs("receitas", exist_ok=True)
    nome_base = sender.replace(":", "_")
    try:
        resp = requests.get(media_url, auth=HTTPBasicAuth(TWILIO_SID, TWILIO_AUTH), stream=True)
        content_type = resp.headers.get("Content-Type", "")
        print(f"💎 Tipo de mídia: {content_type}")
        if "image" in content_type:
            extensao = content_type.split("/")[-1]
        elif "pdf" in content_type:
            extensao = "pdf"
        else:
            print("❌ Erro: conteúdo não suportado ou inválido.")
            return None
        file_path = f"receitas/{nome_base}.{extensao}"
        with open(file_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        print(f"📂 Arquivo salvo em {file_path}")
        return file_path
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return None


def preprocessar_imagem(image_path: str) -> str:
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise Exception("Não foi possível carregar a imagem via OpenCV.")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
        enhanced = cv2.convertScaleAbs(denoised, alpha=1.5, beta=0)
        thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
        processed_path = image_path.rsplit(".", 1)[0] + "_processed.jpg"
        cv2.imwrite(processed_path, thresh)
        print(f"✅ Imagem pré-processada salva em {processed_path}")
        return processed_path
    except Exception as e:
        print(f"❌ Erro no pré-processamento de imagem: {e}")
        return image_path


def corrigir_erros_ocr(texto: str) -> str:
    correcoes = {
        # Correções de palavras inteiras
        r"\bDiplrona\b": "Dipirona", r"\bMana\b": "Maria", r"\bPAC[\'’`]ENTE\b": "PACIENTE",
        r"\blx\b": "1x", r"\benas\b": "dias", r"\bAh[IÍ]il\b": "Abril",
        r"\bcomprim[EI]do\b": "comprimido", r"\bcomprimldo\b": "comprimido",
        r"\bAtorvastat[ji]na\b": "Atorvastatina",
        r"\.\)\s*oãc": "João",
        r"\bAtorvastatlna\b": "Atorvastatina",

        # Correções de dosagens e unidades com erro de OCR
        r"(\d+)[CO]Dmg": r"\100mg",  # Ex: 3CDmg -> 300mg
        r"@\s?mg": "300mg",  # ATUALIZAÇÃO: Converte @mg (erro comum para 300mg)
        r"\bIg!ml\b": "1g/ml",
        r"(\d+)\s+(\d+)%": r"\1.\2%",

        # Correções de números e tempo
        r"\bIO\s+dias": "10 dias",

        # Limpeza geral
        r"[_—]+": "",
        r"\s{2,}": " ",
    }
    for padrao, sub in correcoes.items():
        texto = re.sub(padrao, sub, texto, flags=re.IGNORECASE)
    return texto


def extrair_dados_json_azure(texto: str) -> dict:
    """Orquestra a extração de todas as informações da receita e formata em JSON."""
    nome = re.search(r"(?i)paciente[:\s\-]*([^\n]+)", texto)
    cpf = re.search(r"\d{3}[\.\s_]?\d{3}[\.\s_]?\d{3}[-\s_]?\d{2}", texto)
    crm = re.search(r"CRM[-\s:]*([A-Z]{2}-?\s*\d+)", texto, re.IGNORECASE)
    data = re.search(r"\d{1,2}\s+de\s+\w+\s+de\s+\d{4}", texto)

    nomes_medicamentos = encontrar_todos_os_medicamentos(texto)
    medicamentos_finais = []

    for nome_med in nomes_medicamentos:
        quantidade = extrair_quantidade_total(nome_med, texto)
        medicamentos_finais.append({
            "nome": nome_med.title(),
            "quantidade": quantidade
        })

    return {
        "nome": nome.group(1).strip() if nome else "Não identificado",
        "cpf": cpf.group(0).replace("_", ".") if cpf else None,
        "medicamentos": medicamentos_finais,
        "data_receita": data.group(0) if data else None,
        "crm_medico": crm.group(1).replace("-", "").strip() if crm else None
    }


def extrair_texto_azure(file_path: str) -> str:
    try:
        caminho_imagem = converter_pdf_para_imagem(file_path)
        if not caminho_imagem:
            return json.dumps({"erro": "Falha na conversão do PDF para imagem."}, indent=2, ensure_ascii=False)

        # CORREÇÃO DE BUG: Usa o caminho da imagem convertida, não o original.
        processed_path = preprocessar_imagem(caminho_imagem)

        with open(processed_path, "rb") as image_file:
            image_data = image_file.read()

        ocr_url = f"{AZURE_ENDPOINT}vision/v3.2/ocr?language=pt&detectOrientation=true"
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_KEY,
            "Content-Type": "application/octet-stream"
        }
        response = requests.post(ocr_url, headers=headers, data=image_data)
        response.raise_for_status()
        result = response.json()

        linhas = []
        for region in result.get("regions", []):
            for line in region.get("lines", []):
                texto_linha = " ".join([word["text"] for word in line.get("words", [])])
                linhas.append(texto_linha)

        texto_extraido = "\n".join(linhas)
        texto_corrigido = corrigir_erros_ocr(texto_extraido)
        print("✅ Texto extraído e corrigido:")
        print(texto_corrigido)

        dados_json = extrair_dados_json_azure(texto_corrigido)
        return json.dumps(dados_json, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"❌ Erro na extração com Azure: {e}")
        return json.dumps({"erro": f"Falha ao processar com Azure: {e}"}, indent=2, ensure_ascii=False)