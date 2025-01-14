import pdfplumber
import json
import re
import csv
import os
from datetime import datetime

from painel import VALOR_MINIMO
from utils import verificar_e_salvar_informacoes_csv

def inverter_texto(texto):
    palavras = texto.split(' ')
    palavras_invertidas = [palavra[::-1] for palavra in palavras]
    texto_invertido = ' '.join(palavras_invertidas)
    return texto_invertido

def encontrar_data(texto):
    match = re.search(r'autos\nem\s*(\d{2}/\d{2}/\d{4})', texto)
    if match:
        data = match.group(1)
        return data
    else:
        return None

def extrair_informacoes_pdf_por_paginas(caminho_pdf, url_precatorio, paginas_para_analisar, num_final_prec):
    """
    Extrai informações de páginas específicas de um PDF.
    
    Args:
        caminho_pdf (str): Caminho para o PDF completo.
        url_precatorio (str): URL associada ao precatório.
        paginas_para_analisar (list): Lista de números das páginas a serem analisadas.
    """

    print("Extraíndo dados das páginas que contém 'ofício requisitório'")

    informacoes = {
        "Advogado": "-",
        "Cod. Processo": "-",
        "CPF Req.": "-",
        "Requerente": "-",
        "Valor do Processo": "-",
        "Ent. Devedora": "-",
        "Adv. Req": "-",
        "Data do documento": "-",
        "Data de emissão do termo de declaração": "-",
        "Princ. Liq.": "-",
        "Link": url_precatorio,  # Incluindo o link do precatório
        "Seq": num_final_prec #Número sequencial do precatório
    }

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina_num in paginas_para_analisar:
            try:
                pagina = pdf.pages[pagina_num - 1]  # Ajuste para índice 0-baseado
                texto = pagina.extract_text()
                if not texto:
                    continue

                # Preenchimento progressivo dos dados ao longo das páginas
                termo_chave = texto.find("sotua")
                if termo_chave != -1 and informacoes["Data de emissão do termo de declaração"] == "-":
                    texto_relevante = texto[:termo_chave+5]
                    texto_corrigido = inverter_texto(texto_relevante)
                    data_emissao = encontrar_data(texto_corrigido)
                    informacoes["Data de emissão do termo de declaração"] = data_emissao if data_emissao else "-"

                if "Advogados(s):" in texto and informacoes["Advogado"] == "-":
                    informacoes["Advogado"] = re.split(r' OAB:', texto.split("Advogados(s):")[1])[0].strip()
                
                if "Processo nº:" in texto and informacoes["Cod. Processo"] == "-":
                    informacoes["Cod. Processo"] = (texto.split("Processo nº:")[1].split("\n")[0].strip())

                if "CPF/CNPJ/RNE:" in texto and "Credor nº.: 1" in texto and informacoes["CPF Req."] == "-":
                    informacoes["CPF Req."] = texto.split("CPF/CNPJ/RNE:")[1].split("\n")[0].strip()

                if "Credor(s):" in texto and informacoes["Requerente"] == "-":
                    informacoes["Requerente"] = texto.split("Credor(s):")[1].split("\n")[0].strip()

                if "Valor global da requisição:" in texto and informacoes["Valor do Processo"] == "-":
                    valor = re.findall(r"R\$\s?[\d.,]+", texto)
                    informacoes["Valor do Processo"] = valor[0] if valor else "-"

                if "Devedor:" in texto and informacoes["Ent. Devedora"] == "-":
                    informacoes["Ent. Devedora"] = texto.split("Devedor:")[1].split("\n")[0].strip()

                match_data_documento = re.search(r'(\d{2})\sde\s(\w+)\sde\s(\d{4})', texto)
                if match_data_documento and informacoes["Data do documento"] == "-":
                    dia = match_data_documento.group(1)
                    mes_nome = match_data_documento.group(2).lower()
                    ano = match_data_documento.group(3)
                    meses = {
                        "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
                        "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
                        "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
                    }
                    mes = meses.get(mes_nome)
                    if mes:
                        informacoes["Data do documento"] = f"{dia}/{mes}/{ano}"

                if "Principal/Indenização:" in texto and informacoes["Princ. Liq."] == "-":
                    principal_liquido = re.findall(r"R\$\s?[\d.,]+", texto.split("Principal/Indenização:")[1])
                    informacoes["Princ. Liq."] = principal_liquido[0] if principal_liquido else "-"

                if "https://" in texto and informacoes["Link"] == url_precatorio:
                    link_inicial = texto.find("https://")
                    link_final = texto.find(" ", link_inicial)
                    if link_final == -1:
                        link_final = len(texto)
                    informacoes["Link"] = texto[link_inicial:link_final].strip()

            except IndexError:
                print(f"[ERRO] Página {pagina_num} não existe no PDF.")
                continue

    # Verifica se as informações foram preenchidas corretamente antes de salvar,
    # ignorando os campos "Link" e "Adv. Req"
    if all(value not in ["-", None] for key, value in informacoes.items() if key not in ["Link", "Adv. Req"]):
        print("Extração completa para 'ofício requisitório', verificando dados")
        verificar_e_salvar_informacoes_csv(informacoes)
    else:
        print("Informações incompletas, não serão salvas.")
        # print(json.dumps(informacoes, indent=4, ensure_ascii=False))

    # try:
    #     os.remove(caminho_pdf)
    #     print(f"Arquivo {caminho_pdf} deletado com sucesso.")
    # except OSError as e:
    #     print(f"[ERRO] Não foi possível deletar o arquivo {caminho_pdf}: {e}")


# def salvarinformacoes_csv(informacoes):
#     diretorio = "processos/TJSP"
#     os.makedirs(diretorio, exist_ok=True)

#     arquivo_geral = os.path.join(diretorio, "processos_geral.csv")
#     arquivo_dia = os.path.join(diretorio, f"processos_{datetime.now().strftime('%Y-%m-%d')} - TJSP Diário.csv")

#     cabecalho = ["Advogado", "Cod. Processo", "CPF Req.", "Requerente", "Valor do Processo", "Ent. Devedora", 
#                  "Adv. Req", "Data do documento", "Data de emissão do termo de declaração", "Princ. Liq.", "Link"]

#     def escrever_csv(arquivo, dados, atualizar=False):
#         with open(arquivo, mode='w' if atualizar else 'a', newline='', encoding='utf-8-sig') as file:
#             writer = csv.DictWriter(file, fieldnames=cabecalho, delimiter=';')
#             if file.tell() == 0:
#                 writer.writeheader()
#             if isinstance(dados, list):
#                 writer.writerows(dados)
#             else:
#                 writer.writerow(dados)

#     processos_geral = {}
#     if os.path.isfile(arquivo_geral):
#         with open(arquivo_geral, mode='r', encoding='utf-8-sig') as file:
#             reader = list(csv.DictReader(file, delimiter=';'))
#             for linha in reader:
#                 if "Cod. Processo" in linha and linha["Cod. Processo"].strip():
#                     processos_geral[linha["Cod. Processo"]] = linha

#     cod_processo = informacoes["Cod. Processo"]
#     if cod_processo and cod_processo in processos_geral:
#         processos_geral[cod_processo].update(informacoes)
#     else:
#         processos_geral[cod_processo] = informacoes

#     escrever_csv(arquivo_geral, list(processos_geral.values()), atualizar=True)

#     processos_dia = {}
#     if os.path.isfile(arquivo_dia):
#         with open(arquivo_dia, mode='r', encoding='utf-8-sig') as file:
#             reader = list(csv.DictReader(file, delimiter=';'))
#             for linha in reader:
#                 if "Cod. Processo" in linha and linha["Cod. Processo"].strip():
#                     processos_dia[linha["Cod. Processo"]] = linha

#     if cod_processo and cod_processo in processos_dia:
#         processos_dia[cod_processo].update(informacoes)
#     else:
#         processos_dia[cod_processo] = informacoes

#     escrever_csv(arquivo_dia, list(processos_dia.values()), atualizar=True)

# Exemplo de uso
# caminho_pdf = "data/oficio.pdf"
# url_precatorio = "https://esaj.tjsp.jus.br/cpopg/show.do?localPesquisa.cdLocal=53&processo.codigo=1H000HPKW0001&processo.foro=53"
# extrair_informacoes_pdf(caminho_pdf, url_precatorio)