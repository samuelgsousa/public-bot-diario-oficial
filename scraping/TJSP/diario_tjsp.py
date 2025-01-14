import requests
import pdfplumber
import os
import csv
import time
import re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from SQL_Conections.TJSP.crud_operations_historico import get_last_exec, insert_historic, update_historic
from SQL_Conections.TJSP.crud_operations_process import insert_process
from SQL_Conections.TJSP.connect import get_db_connection
from utils import ir_ate_pagina
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def start_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Use headless mode se desejar
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')  # Abre o navegador maximizado

    prefs = {
        "download.default_directory": os.path.join(os.getcwd(), 'data'),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,  # Garante que o diretório seja atualizado mesmo que seja diferente do padrão
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,  # Desabilita pop-ups de download
        "profile.default_content_setting_values.automatic_downloads": 1  # Permite downloads múltiplos
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    return driver

# Função para baixar o PDF e buscar o número do processo
def buscar_numero_processo_pdf(link_pdf):
    try:
        print(f"Baixando o PDF do link: {link_pdf}")
        response = requests.get(link_pdf)
        nome_arquivo = 'temp.pdf'

        with open(nome_arquivo, 'wb') as f:
            f.write(response.content)

        print(f"Abrindo o PDF {nome_arquivo} para leitura...")
        with pdfplumber.open(nome_arquivo) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                # Procurar por números de processo que sigam o padrão de 20 dígitos com formatação específica
                match = re.search(r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}', texto)
                if match:
                    processo = match.group(0)
                    print(f"Número do processo encontrado: {processo}")
                    pdf.close()
                    f.close()
                    os.remove(nome_arquivo)  # Remove o arquivo temporário
                    return processo

        os.remove(nome_arquivo)  # Remove o arquivo temporário se não encontrar processo
        print("Número do processo não encontrado no PDF.")
    except Exception as e:
        print(f"[ERRO] Erro ao buscar número do processo no PDF: {e}")
    return None

# Função para buscar o link real do PDF após abrir o visualizador
def obter_link_real_do_pdf(driver, result):
    try:
        # Verifica se o elemento com 'popup' no onclick existe
        elementos_popup = result.find_elements(By.XPATH, ".//a[contains(@onclick, 'popup')]")

        if elementos_popup:
            # Pegando o script "popup" do atributo 'onclick'
            popup_script = elementos_popup[0].get_attribute('onclick')

            # Extraindo a URL do PDF do script "popup"
            match = re.search(r"popup\('(.+?)'\)", popup_script)
            if match:
                relative_url = match.group(1)  # Extraímos a URL relativa do PDF
                link_pdf = f"https://dje.tjsp.jus.br{relative_url.replace('consultaSimples.do', 'getPaginaDoDiario.do')}"
                print(f"Link direto do PDF: {link_pdf}")
                return link_pdf
        else:
            # Tenta outra estratégia caso o 'popup' não seja encontrado
            link_elementos = result.find_elements(By.XPATH, ".//a[@title='Visualizar']")
            if link_elementos:
                link_pdf = link_elementos[0].get_attribute('href')
                if link_pdf:
                    print(f"Link direto do PDF (fallback): {link_pdf}")
                    return link_pdf
            else:
                print("Elemento com link do PDF não encontrado.")
                return None
    except Exception as e:
        print(f"[ERRO] Erro ao obter o link real do PDF: {e}")
        return None
    
def search_diario_tjsp(driver, keyword, data_inicio, data_fim, historico):
    print(f"Acessando o site DJE - TJSP com a palavra-chave: {keyword} e data: {data_inicio} a {data_fim}")
    
    if historico and len(historico) > 0:
        print("Retomando busca no DJE")
        page = historico['pagina_atual']
        print(f"Continuando na página {page}")
    else:
        page = 1  # Página inicial
    
    # Acessar a URL com consulta avançada
    driver.get('https://dje.tjsp.jus.br/cdje/consultaAvancada.do#buscaavancada')
    time.sleep(2)

    # Localizar o campo de busca e inserir a palavra-chave
    search_input = driver.find_element(By.ID, 'procura')
    search_input.send_keys(keyword)

    # Remover o atributo readonly dos campos de data
    driver.execute_script("document.getElementById('dtInicioString').removeAttribute('readonly')")
    driver.execute_script("document.getElementById('dtFimString').removeAttribute('readonly')")

    # Inserir as datas de início e fim
    data_inicio_input = driver.find_element(By.ID, 'dtInicioString')
    data_fim_input = driver.find_element(By.ID, 'dtFimString')

    data_inicio_input.clear()
    data_inicio_input.send_keys(data_inicio)

    data_fim_input.clear()
    data_fim_input.send_keys(data_fim)

    # Iniciar a busca
    search_input.send_keys(Keys.RETURN)
    time.sleep(5)  # Aguardar o carregamento da página


    ir_ate_pagina(driver, page, 0) #executando inicialmente com um tempo de espera baixo entre a páginação para chegar rápido até o destino

    time.sleep(2)

    ir_ate_pagina(driver, page, 2) #executando novamente com um tempo de espera maior para garantir a precisão


    connection = get_db_connection()
    
    while True:
        print(f"Capturando os resultados da página {page}...")

        # Coletar os resultados na página atual
        try:
            results = driver.find_elements(By.CLASS_NAME, 'ementaClass')

            for result in results:
                print(f"Resultado encontrado: {result.text}")
                
                try:
                    # Obter o link real do PDF diretamente do resultado
                    link_real_pdf = obter_link_real_do_pdf(driver, result)

                    if link_real_pdf:
                        # Baixar o PDF diretamente e buscar o número do processo
                        process_number = buscar_numero_processo_pdf(link_real_pdf)
                        
                        #ADICIONAR A BANCO DE DADOS, lista de processos
                        if process_number:

                            insert_process(connection, process_number, data_inicio, data_fim)
                            #process_numbers.append(process_number)  # Armazenar o número do processo
                except NoSuchElementException:
                    print(f"PDF não encontrado no resultado: {result.text}")
        except Exception as e:
            print(f"[ERRO] Erro ao capturar resultados: {e}")

        # Tentar navegar para a próxima página
        try:
            next_button = driver.find_element(By.XPATH, "//a[contains(text(),'Próximo')]")
            next_button.click()
            time.sleep(5)  # Aguardar o carregamento da próxima página
            page += 1
            update_historic(historico['id'], 'pagina_atual', page)

            # if page > 3: #testar rápidamente
            #      connection.close()
            #      break

        except NoSuchElementException:
            print(f"Paginação concluída. Nenhuma página 'Próximo' encontrada.")
            connection.close()
            update_historic(historico['id'], 'paginacao_conc', True)
            break
        # Break para debug
        # break
    connection.close()
   # return process_numbers

# Função para salvar o CSV na estrutura correta
def salvar_csv_completo_incremental(process_number, nome_arquivo='processos_tjsp_completa_estrutura.csv'):
    columns = [
        "Advogado", "Cod. Processo", "CPF Req.", "Requerente", "Valor do Processo",
        "Ent. Devedora", "Adv. Req", "Data do documento", "Data de emissão do termo de declaração",
        "Princ. Liq.", "Link"
    ]
    
    # Verifica se o arquivo existe, se não existir, cria com o cabeçalho
    write_header = not os.path.exists(nome_arquivo)
    
    with open(nome_arquivo, mode='a', newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(columns)  # Escreve o cabeçalho uma vez
        row = [""] * len(columns)  # Cria uma linha vazia
        row[1] = process_number  # Preenche apenas o número do processo
        writer.writerow(row)
    
    print(f"Processo {process_number} salvo em {nome_arquivo}")

# Código principal
if __name__ == "__main__":
    palavra_chave = "Ofício requisitório"
    driver = start_driver()
    data_inicio_str = "2024/10/18"
    data_fim_str = "2024/10/18"

    print("Iniciando a busca no DJE - TJSP...")
    process_numbers = search_diario_tjsp(driver, palavra_chave, data_inicio_str, data_fim_str)
    
    if process_numbers:
        salvar_csv_completo_incremental(process_numbers)
    else:
        print("Nenhum número de processo encontrado.")
    
    driver.quit()