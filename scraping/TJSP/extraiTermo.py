import pdfplumber
import json
import csv
import os
from datetime import datetime
import os
from painel import VALOR_MINIMO
from utils import verificar_e_salvar_informacoes_csv


def extrair_informacoes_pdf_por_paginas(caminho_pdf, url_precatorio, paginas_para_analisar, num_final_prec):
    """
    Extrai informações de páginas específicas de um PDF.

    Args:
        caminho_pdf (str): Caminho para o PDF completo.
        url_precatorio (str): URL associada ao precatório.
        paginas_para_analisar (list): Lista de números das páginas a serem analisadas.
    """

    print("Extraíndo dados das páginas que contém 'termo de declaração'")

    # Dicionário para armazenar as informações extraídas
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
                pagina = pdf.pages[pagina_num - 1]  # Converter número da página para índice (0-based)
                texto = pagina.extract_text()
                if not texto:
                    continue

                # Extração das informações específicas do termo de declaração
                if "Nome:" in texto and informacoes["Advogado"] == "-":
                    informacoes["Advogado"] = texto.split("Nome:")[1].split("\n")[0].strip()

                if "Número de processo:" in texto and informacoes["Cod. Processo"] == "-":
                    informacoes["Cod. Processo"] = (texto.split("Número de processo:")[1].split("\n")[0].strip())

                if "CPF:" in texto and informacoes["CPF Req."] == "-":
                    informacoes["CPF Req."] = texto.split("CPF:")[1].split("\n")[0].strip()

                if "Requerente:" in texto and informacoes["Requerente"] == "-":
                    informacoes["Requerente"] = texto.split("Requerente:")[1].split("\n")[0].strip()

                if "Requisitado:" in texto and informacoes["Valor do Processo"] == "-":
                    informacoes["Valor do Processo"] = texto.split("Requisitado:")[1].split("\n")[0].strip()

                if "Entidade devedora:" in texto and informacoes["Ent. Devedora"] == "-":
                    informacoes["Ent. Devedora"] = texto.split("Entidade devedora:")[1].split("\n")[0].strip()

                if "Nome:" in texto and informacoes["Adv. Req"] == "-":
                    informacoes["Adv. Req"] = texto.split("Nome:")[1].split("\n")[0].strip()

                if "Emitido em:" in texto:
                    data_emissao = texto.split("Emitido em:")[1].split("\n")[0].strip()
                    informacoes["Data do documento"] = data_emissao
                    informacoes["Data de emissão do termo de declaração"] = data_emissao

                if "Principal líquido:" in texto and informacoes["Princ. Liq."] == "-":
                    informacoes["Princ. Liq."] = texto.split("Principal líquido:")[1].split("\n")[0].strip()

            except IndexError:
                print(f"[ERRO] Página {pagina_num} não existe no PDF.")
                continue

    # Verifica se todas as informações foram preenchidas antes de salvar
    if all(value not in ["-", None] for key, value in informacoes.items() if key != "Link"):
        print("Extração completa para 'termo de declaração', verificando dados")
        verificar_e_salvar_informacoes_csv(informacoes)
    else:
        print("Informações incompletas, não serão salvas.")

    # Remove o arquivo PDF após a extração
    # try:
    #     os.remove(caminho_pdf)
    #     print(f"Arquivo {caminho_pdf} deletado com sucesso.")
    # except OSError as e:
    #     print(f"[ERRO] Não foi possível deletar o arquivo {caminho_pdf}: {e}")
    

# def salvar_informacoes_csv(informacoes):
#     # Define o diretório onde os arquivos CSV serão salvos
#     diretorio = "processos/TJSP"
#     os.makedirs(diretorio, exist_ok=True)  # Garante que o diretório exista

#     # Define os nomes dos arquivos CSV com o caminho do diretório
#     arquivo_geral = os.path.join(diretorio, "processos_geral.csv")
#     arquivo_dia = os.path.join(diretorio, f"processos_{datetime.now().strftime('%Y-%m-%d')} - TJSP Diário.csv")

#     cabecalho = ["Advogado", "Cod. Processo", "CPF Req.", "Requerente", "Valor do Processo", "Ent. Devedora", 
#                  "Adv. Req", "Data do documento", "Data de emissão do termo de declaração", "Princ. Liq.", "Link"]

#     def escrever_csv(arquivo, dados, atualizar=False):
#         # Abre o arquivo no modo de escrita apropriado
#         with open(arquivo, mode='w' if atualizar else 'a', newline='', encoding='utf-8-sig') as file:
#             writer = csv.DictWriter(file, fieldnames=cabecalho, delimiter=';')
#             # Escreve o cabeçalho apenas se o arquivo estiver vazio
#             if file.tell() == 0:
#                 writer.writeheader()
#             # Se dados for uma lista de dicionários, escreve várias linhas; caso contrário, uma única linha
#             if isinstance(dados, list):
#                 writer.writerows(dados)
#             else:
#                 writer.writerow(dados)

#     # Carrega processos existentes no arquivo geral para evitar duplicações
#     processos_geral = {}
#     if os.path.isfile(arquivo_geral):
#         with open(arquivo_geral, mode='r', encoding='utf-8-sig') as file:
#             reader = list(csv.DictReader(file, delimiter=';'))
#             for linha in reader:
#                 if "Cod. Processo" in linha and linha["Cod. Processo"].strip():
#                     processos_geral[linha["Cod. Processo"]] = linha

#     # Verifica se o processo já está no arquivo geral e atualiza se necessário
#     cod_processo = informacoes["Cod. Processo"]
#     if cod_processo and cod_processo in processos_geral:
#         processos_geral[cod_processo].update(informacoes)
#     else:
#         processos_geral[cod_processo] = informacoes

#     # Reescreve o CSV geral com os dados atualizados
#     escrever_csv(arquivo_geral, list(processos_geral.values()), atualizar=True)

#     # Carrega processos existentes no arquivo do dia para evitar duplicações
#     processos_dia = {}
#     if os.path.isfile(arquivo_dia):
#         with open(arquivo_dia, mode='r', encoding='utf-8-sig') as file:
#             reader = list(csv.DictReader(file, delimiter=';'))
#             for linha in reader:
#                 if "Cod. Processo" in linha and linha["Cod. Processo"].strip():
#                     processos_dia[linha["Cod. Processo"]] = linha

#     # Atualiza o processo no arquivo diário se já existe, ou adiciona novo se não
#     if cod_processo and cod_processo in processos_dia:
#         processos_dia[cod_processo].update(informacoes)
#     else:
#         processos_dia[cod_processo] = informacoes

#     # Reescreve o CSV do dia com os dados atualizados
#     escrever_csv(arquivo_dia, list(processos_dia.values()), atualizar=True)

# Exemplo de uso
# caminho_pdf = "data/doc_166092150.pdf"
# url_precatorio = "https://esaj.tjsp.jus.br/cpopg/show.do?localPesquisa.cdLocal=53&processo.codigo=1H000HPKW0001&processo.foro=53"
# extrair_informacoes_pdf(caminho_pdf, url_precatorio)