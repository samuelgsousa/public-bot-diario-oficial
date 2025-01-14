import csv
from datetime import datetime
import glob
import locale
import os
import shutil
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import pdfplumber
import fitz  # PyMuPDF
from unidecode import unidecode
from SQL_Conections.TJSP.crud_operations_req_pagamentos import get_all_req_not_exported, insert_requisicao, update_exported_status
from painel import VALOR_MINIMO, Precatorio, SessaoExpirada  # Para remover acentos
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import re

# Caminho para onde o arquivo será movido
caminho_download_temp = os.path.join(os.path.dirname(__file__), 'temp_indv_TJSP')
caminho_download = os.path.join(os.path.dirname(__file__), 'data') 

validos = []
invalidos = []

def redefinir_contagem(): #para garantir que os valores não se misturem a cada execução
    global validos, invalidos
    validos = []
    invalidos = []

def esperar_download(diretorio, timeout=60):
    """
    Aguarda o download ser concluído no diretório especificado.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        arquivos = os.listdir(diretorio)
        if any(arquivo.endswith(".crdownload") for arquivo in arquivos):  # Arquivo parcial do Chrome
            sleep(1)
        else:
            return True
    return False

def mover_arquivo_recente(diretorio_download, caminho_destino, inicio_processo):
    """
    Move o arquivo mais recente do diretório de download, considerando apenas arquivos após o início do processo.
    """
    sleep(2)
    print(f"pasta de destino: {caminho_destino}")
    print(f"diretório de download: {diretorio_download}")
    print(f"Início do processo: {inicio_processo}")
    print("")
    # Lista arquivos .pdf modificados após o início do processo
    arquivos = [
        f for f in os.listdir(diretorio_download)
        if f.endswith(".pdf") and os.path.getmtime(os.path.join(diretorio_download, f)) > inicio_processo
    ]
    
    if not arquivos:
        print("Nenhum arquivo recente foi encontrado para mover.")
        return None

    # Encontra o arquivo mais recente
    arquivos_completo = [(os.path.join(diretorio_download, f), os.path.getmtime(os.path.join(diretorio_download, f))) for f in arquivos]
    arquivo_mais_recente = max(arquivos_completo, key=lambda x: x[1])[0]

    # Move o arquivo para o destino
    destino = os.path.join(caminho_destino, os.path.basename(arquivo_mais_recente))
    shutil.move(arquivo_mais_recente, destino)
    print(f"Arquivo {os.path.basename(arquivo_mais_recente)} movido para: {destino}")
    return destino

def baixar_doc(driver):
    sleep(2)

    excluir_arquivos_por_extensao(caminho_download, [".crdownload"]) #limpar antes de iniciar o download, para evitar erros

    inicio_processo = time.time()

    try:
        # Aguarda até que o botão esteja presente e clicável
        selectButton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@id='selecionarButton' and @type='button']"))
        )
        # Clica no botão
        selectButton.click()  # Clica no primeiro botão encontrado
        print("Botão de seleção clicado com sucesso.")

        sleep(2)

        downloadButton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@id='salvarButton' and @type='button']"))
        )
        downloadButton.click()  # Clica no primeiro botão encontrado
        print("Botão de download clicado com sucesso.")

        sleep(2)

        # Aguarda até que o botão de confirmação no popup fique disponível e clicável
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@id='botaoContinuar' and @type='button']"))
        )
        confirm_button.click()
        print("Botão de confirmação clicado com sucesso.")

        sleep(2)

        # Aguardar o download ser concluído
        download_doc_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.ID, "btnDownloadDocumento"))
        )
        download_doc_button.click()
        print("Botão 'Download Documento' clicado com sucesso.")

        # Aguarda o download ser concluído e move o arquivo para o destino
        if esperar_download(caminho_download):
            print("Download concluído. Movendo o arquivo...")
            destino = mover_arquivo_recente(caminho_download, caminho_download_temp, inicio_processo)  # Move o arquivo para o destino
            return destino

    except TimeoutException:
        print("O botão não foi encontrado ou não está clicável no tempo limite. Verificando mensagem de sessão expirada")

        try:
            message = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'validar') and contains(text(), 'acesso')]"))
            )
            if message:
                print("Sessão expirou! Iniciando nova sessão no ESAJ")
                raise SessaoExpirada #retornando erro específico para indicar que a sessão expirou
            
        except SessaoExpirada:
            raise

        except:
            print("Não foi encontrada nenhuma mensagem indicado que a sessão expirou!")

 

def buscar_termo_pdf(caminho_pdf, termo):
    """
    Busca um termo em um PDF, ignorando maiúsculas, minúsculas e acentos.
    
    Args:
        caminho_pdf (str): Caminho para o arquivo PDF.
        termo (str): Termo a ser buscado.
        
    Returns:
        list: Lista de números das páginas que contêm o termo.
    """
    # Normaliza o termo removendo acentos e ignorando maiúsculas/minúsculas
    termo_normalizado = unidecode(termo).lower()
    
    # Abre o PDF
    doc = fitz.open(caminho_pdf)
    
    # Lista para armazenar as páginas com o termo
    paginas_com_termo = []
    
    # Loop pelas páginas do PDF
    for pagina_num in range(len(doc)):
        # Obtém o texto da página
        pagina = doc.load_page(pagina_num)
        texto = pagina.get_text("text")  # Obtém o texto da página
        
        # Normaliza o texto removendo acentos e ignorando maiúsculas/minúsculas
        texto_normalizado = unidecode(texto).lower()
        
        # Verifica se o termo está no texto normalizado da página
        if termo_normalizado in texto_normalizado:
            paginas_com_termo.append(pagina_num + 1)  # Armazena a página (1-indexed)
    
    doc.close()  # Fecha o PDF
    print(f"Páginas com o termo '{termo}': {paginas_com_termo}")
    print("")
    return paginas_com_termo

def excluir_arquivos_por_extensao(pasta, extensoes):
    """
    Exclui arquivos de uma pasta com as extensões especificadas.

    Args:
        pasta (str): Caminho da pasta onde os arquivos serão excluídos.
        extensoes (list): Lista de extensões (com ponto, ex.: ['.pdf', '.crdownload']) a serem excluídas.
    """
    if not os.path.isdir(pasta):
        print(f"[ERRO] A pasta especificada '{pasta}' não existe.")
        return

    arquivos_excluidos = 0
    for extensao in extensoes:
        caminho_arquivos = os.path.join(pasta, f"*{extensao}")
        for arquivo in glob.glob(caminho_arquivos):
            try:
                os.remove(arquivo)
                arquivos_excluidos += 1
                print(f"Arquivo excluído: {arquivo}")
            except OSError as e:
                print(f"[ERRO] Não foi possível excluir o arquivo '{arquivo}': {e}")

    print(f"Total de arquivos excluídos: {arquivos_excluidos}")

def limpar_pastas():
    excluir_arquivos_por_extensao(caminho_download, [".crdownload"])
    excluir_arquivos_por_extensao(caminho_download, [".pdf"])
    excluir_arquivos_por_extensao(caminho_download_temp, [".pdf"])

def add_contagem(prec):
    """
    Lista os precatórios que foram salvos e que não foram salvos
    Utiliza condicionais para garantir que os valores não repitam entre as listas, e que um valor válido não se torne inválido (pois a função é executada duas vezes)
    """
        
    global validos, invalidos

    # Exibir informações para depuração
    #print(f"prec na add_contagem: {prec}")

    # Caso o precatório seja válido
    if prec.valido:
        # Verifica se já existe na lista de inválidos e o remove
        invalidos = [p for p in invalidos if p.num != prec.num]

        # Verifica se já existe na lista de válidos
        if not any(p.num == prec.num for p in validos):
            validos.append(prec)

    # Caso o precatório seja inválido
    else:
        # Verifica se ele já existe na lista de válidos
        if any(p.num == prec.num for p in validos):
            # Não faz nada, pois não se move para inválidos
            return

        # Verifica se já existe na lista de inválidos
        if not any(p.num == prec.num for p in invalidos):
            invalidos.append(prec)

def obter_nao_processados(process_numbers, validos, invalidos):
    # Obter todos os números de precatórios já processados (válidos e inválidos)
    numeros_processados = {prec.num for prec in validos} | {prec.num for prec in invalidos}

    # Retornar os números de process_numbers que não estão em numeros_processados
    return [num for num in process_numbers if num not in numeros_processados]


def verificar_e_salvar_informacoes_csv(informacoes):
    global validos, invalidos

    print(f"{'-' * 40}[As informações são]{'-' * 40}")
    print(informacoes)
    print("")

    valor_prec = converter_valor(informacoes['Valor do Processo'])
    princ_liq = converter_valor(informacoes['Princ. Liq.'])

    informacoes['Valor do Processo'] = valor_prec
    informacoes['Princ. Liq.'] = princ_liq

    print(f"O valor do precatório é {valor_prec}")
    print("")

    if valor_prec < VALOR_MINIMO:
        print(f"Valor menor que {VALOR_MINIMO}, não será salvo!")
        print("")



    else:
        print(f"Valor válido [{valor_prec}]!!!")

        insert_requisicao(informacoes)


        req_to_CSV = get_all_req_not_exported()

        exportar_csv(req_to_CSV)





        # cabecalho = ["Advogado", "Cod. Processo", "CPF Req.", "Requerente", "Valor do Processo", "Ent. Devedora", 
        #             "Adv. Req", "Data do documento", "Data de emissão do termo de declaração", "Princ. Liq.", "Link"]

        # def escrever_csv(arquivo, dados, atualizar=False):
        #     # Abre o arquivo no modo de escrita apropriado
        #     with open(arquivo, mode='w' if atualizar else 'a', newline='', encoding='utf-8-sig') as file:
        #         writer = csv.DictWriter(file, fieldnames=cabecalho, delimiter=';')
        #         # Escreve o cabeçalho apenas se o arquivo estiver vazio
        #         if file.tell() == 0:
        #             writer.writeheader()
        #         # Se dados for uma lista de dicionários, escreve várias linhas; caso contrário, uma única linha
        #         if isinstance(dados, list):
        #             writer.writerows(dados)
        #         else:
        #             writer.writerow(dados)

        


        # arquivo = "caminho/do/arquivo.csv"

        # if os.path.exists(arquivo):
        #     print(f"O arquivo {arquivo} existe.")
        # else:
        #     print(f"O arquivo {arquivo} não existe.")


        # #escrever_csv(arquivo_geral, list(processos_geral.values()), atualizar=True)
        
        # # Carrega processos existentes no arquivo geral para evitar duplicações
        # processos_geral = {}
        # if os.path.isfile(arquivo_geral):
        #     with open(arquivo_geral, mode='r', encoding='utf-8-sig') as file:
        #         reader = list(csv.DictReader(file, delimiter=';'))
        #         for linha in reader:
        #             if "Cod. Processo" in linha and linha["Cod. Processo"].strip():
        #                 processos_geral[linha["Cod. Processo"]] = linha

        # # Verifica se o processo já está no arquivo geral e atualiza se necessário
        # cod_processo = informacoes["Cod. Processo"]
        # if cod_processo and cod_processo in processos_geral:
        #     processos_geral[cod_processo].update(informacoes)
        # else:
        #     processos_geral[cod_processo] = informacoes

        # # Reescreve o CSV geral com os dados atualizados
        # escrever_csv(arquivo_geral, list(processos_geral.values()), atualizar=True)

        # # Carrega processos existentes no arquivo do dia para evitar duplicações
        # processos_dia = {}
        # if os.path.isfile(arquivo_dia):
        #     with open(arquivo_dia, mode='r', encoding='utf-8-sig') as file:
        #         reader = list(csv.DictReader(file, delimiter=';'))
        #         for linha in reader:
        #             if "Cod. Processo" in linha and linha["Cod. Processo"].strip():
        #                 processos_dia[linha["Cod. Processo"]] = linha

        # # Atualiza o processo no arquivo diário se já existe, ou adiciona novo se não
        # if cod_processo and cod_processo in processos_dia:
        #     processos_dia[cod_processo].update(informacoes)
        # else:
        #     processos_dia[cod_processo] = informacoes

        # # Reescreve o CSV do dia com os dados atualizados
        # escrever_csv(arquivo_dia, list(processos_dia.values()), atualizar=True)
        print("Dados salvos com sucesso!!!")


def exportar_csv(dados):

    """
    Exporta dados para um arquivo CSV, renomeando as colunas de acordo com o cabeçalho fornecido.

    Parâmetros:
    - arquivo (str): Caminho do arquivo CSV para exportação.
    
    Retorno:
    - None
    """            

    diretorio = "processos/TJSP"
    os.makedirs(diretorio, exist_ok=True)  # Garante que o diretório exista

            # Define os nomes dos arquivos CSV com o caminho do diretório
    arquivo_geral = os.path.join(diretorio, "processos_geral.csv")
    arquivo_dia = os.path.join(diretorio, f"processos_{datetime.now().strftime('%Y-%m-%d')} - TJSP Diário.csv")

    att_status = [] #Array para armazenar os ids das linhas cujo o status "exportado" será atualizado futuramente

    for dicionario in dados:
        dicionario['cod_processo'] = dicionario['cod_processo'] + '/' + str(dicionario['seq']).zfill(2)
        dicionario['valor_processo'] = formatar_monetario(dicionario['valor_processo'])
        att_status.append(int(dicionario['id'])) 

        #formatar_monetario(valor)

    cabecalho = {
    "nome_req": "Requerente",
    "cpf_req": "CPF - Requerente",
    "cod_processo": "Codigo Processo",
    "advogado": "Advogado",
    "valor_processo": "Valor do Processo",
    "data_doc": "Data do documento",
    "data_emissão_termo_dec": "Data de emissão do termo de declaração",
    "ent_devedora": "Ent. Devedora",
    "princ_liq": "Princ. Liq.",
    "link": "Link"
}
    
    # Renomeia os campos dos dados para corresponder ao cabeçalho amigável
    dados_renomeados = [
        {cabecalho.get(chave, chave): valor for chave, valor in linha.items() if chave in cabecalho}
        for linha in dados
    ]

    def exportar(arquivo):
        """
        Escreve os dados no arquivo CSV
        
        Parâmetros:
        - arquivo (str): Caminho do arquivo CSV para exportação.
        
        Retorno:
        - None
        """
            
            # Define o caminho completo do arquivo
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)  # Cria o diretório se não existir
            caminho_completo = os.path.join(diretorio, arquivo)
        else:
            caminho_completo = arquivo

        
        with open(arquivo, mode='a', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=cabecalho.values(), delimiter=';')

            if file.tell() == 0:  # Adiciona cabeçalho apenas em arquivos novos
                writer.writeheader()
            writer.writerows(dados_renomeados)
            print(f"Arquivo CSV salvo em: {caminho_completo}")


    exportar(arquivo_geral)
    exportar(arquivo_dia)

    print(att_status)
    update_exported_status(att_status) #mudar o status de exportado para true
    print("Arquivo Geral e Diário Atualizados")
    

def voltar_pagina_anterior(driver, max_tentativas, intervalo):
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            driver.back()
            return 
        except Exception as e:
            print(f"[ERRO] FALHA AO VOLTAR PARA A PÁGINA ANTERIOR, TENTANDO NOVAMENTE EM {intervalo} SEGUNDOS | tentativa {tentativa} de {max_tentativas}")
            print(e)
            if tentativa < max_tentativas:
                time.sleep(intervalo)  # Espera antes de tentar novamente
            else:
                print("Número máximo de tentativas atingido. Abortando.")
                raise 



def ir_ate_pagina(driver, pagina, cool_down):

    """
    Função para avançar rapidamente até a página desejada no DJE, utilizada principalmente para retomar a execução em casos de interrupção. 
    Ela otimiza o processo de navegação ao aguardar a renderização completa da página após cada clique no botão "Próximo", eliminando a necessidade de usar um `time.sleep()` fixo, o que torna a execução significativamente mais eficiente.

    **Motivação para o uso do parâmetro `cool_down`**:
    1. Como o número de páginas pode ser muito grande, aplicar um tempo de espera fixo em cada interação tornaria a execução extremamente lenta. Por isso, na primeira execução, o tempo de espera (`cool_down`) é configurado como 0 para acelerar a navegação até as proximidades da página desejada.
    2. No entanto, navegar rapidamente sem um tempo de espera pode causar inconsistências: em algumas situações, a função `get_current_page()` pode ser chamada antes da renderização completa da nova página. Isso pode fazer com que a função ultrapasse a página correta (geralmente avançando uma a mais).

    **Solução**:
    Para lidar com esse problema, a função é executada em duas etapas:
    - **Primeira etapa**: Com `cool_down = 0`, navega rapidamente para aproximar-se da página desejada.
    - **Segunda etapa**: Com `cool_down > 0`, aplica um tempo de espera maior para garantir precisão na navegação e evitar ultrapassagens.

    **Parâmetros**:
    - `driver`: Instância do Selenium WebDriver usada para interagir com o navegador.
    - `pagina` (int): Número da página de destino para onde o script deve avançar (definido na tabela `historico_exec`, coluna `pagina_atual`).
    - `cool_down` (int): Tempo de espera (em segundos) entre clicar no botão e identificar qual página foi renderizada.

    **Retorno**:
    - `None`: Esta função não retorna nenhum valor, apenas garante que a página correta seja acessada.
    """


    def get_current_page():
        """
        Função para identificar qual página está sendo acessada no momento através do elemento de páginação do site do DJE
        """
        pag_atual = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@class='style5']/strong"))
                ).text

        pag_atual = int(pag_atual)

        return pag_atual

    def change_page(direction):
            
        """
        Função para clicar no botão "Próximo" ou "Anterior". Avançando ou Retrocedendo a página, de acordo com a necessidade
        """

        # Aguarda o botão "Próximo" ou "Anterior" estar clicável
        
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(),'{direction}')]"))
        )

        # Tenta clicar no botão "Próximo"
        button.click()

        # Aguarda até que a página seja completamente carregada
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(),'{direction}')]"))
        )

        print(f"Página atual:{pag_atual}")
    
    pag_atual = get_current_page()

    while pag_atual != pagina:
        if pag_atual < pagina:

            try:
                change_page('Próximo')
                time.sleep(cool_down)
                pag_atual = get_current_page()

            except StaleElementReferenceException:
                # Reobtém o botão "Próximo" e tenta novamente
                print("Elemento 'Próximo' foi recriado. Tentando obter novamente...")
                continue

            except TimeoutException:
                print(f"Erro: Timeout ao carregar a página {pag_atual}.")
                break

        if pag_atual > pagina:
            try:
                change_page('Anterior')
                time.sleep(cool_down)
                pag_atual = get_current_page()

            except StaleElementReferenceException:
                # Reobtém o botão "Anterior" e tenta novamente
                print("Elemento 'Anterior' foi recriado. Tentando obter novamente...")
                continue

            except TimeoutException:
                print(f"Erro: Timeout ao carregar a página {pag_atual}.")
                break

def ir_ate_pagina_PJE(driver, pagina, cool_down):

    def get_current_page():
        """
        Função para identificar qual página está sendo acessada no momento através do elemento de páginação do site do PJE
        """
        pag_atual = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-state-active"))
                ).text

        pag_atual = int(pag_atual)

        return pag_atual
    
    def change_page(direction):
        
        """
        Função para clicar no botão "Próximo" ou "Anterior". Avançando ou Retrocedendo a página, de acordo com a necessidade
        """

        # Aguarda o botão "Próximo" ou "Anterior" estar clicável
        
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, direction))
        )

        # Tenta clicar no botão "Próximo"
        button.click()

    pag_atual = get_current_page()

    while pag_atual != pagina:
        if pag_atual < pagina:

            try:
                change_page('.ui-paginator-next')
                time.sleep(cool_down)
                pag_atual = get_current_page()

            except TimeoutException:
                print(f"Erro: Timeout ao carregar a página {pag_atual}.")
                break

        if pag_atual > pagina:
            try:
                change_page('.ui-paginator-prev')
                time.sleep(cool_down)
                pag_atual = get_current_page()

            except TimeoutException:
                print(f"Erro: Timeout ao carregar a página {pag_atual}.")
                break

            # Verificar se há um botão "próxima página" habilitado
    next_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.ui-paginator-next"))
    )

    if "ui-state-disabled" in next_button.get_attribute("class"):
        print("Última página alcançada.")
    else:
        print("Indo para a próxima página...")
        next_button.click()
        time.sleep(5)  # Espera para a próxima página carregar


def converter_valor(valor):
    """
        Função feita para resolver o problema de casas decimais em valores de precatório que vem em formatos inconsistentes.
        As vezes o valor vem como 144.767,45 ou 144,767.45 ou 144.767.45 etc. A função garante que os valores sejam convertidos de forma correta
    """
    # Remove o símbolo de moeda e espaços extras
    valor_limpo = re.sub(r'[^\d.,]', '', valor)

    # Verifica o padrão baseado na última ocorrência de vírgula ou ponto
    if ',' in valor_limpo and '.' in valor_limpo:
        if valor_limpo.rfind(',') > valor_limpo.rfind('.'):
            # Caso com vírgula como decimal e ponto como separador de milhares
            valor_corrigido = valor_limpo.replace('.', '').replace(',', '.')
        else:
            # Caso com ponto como decimal e vírgula como separador de milhares
            valor_corrigido = valor_limpo.replace(',', '')
    else:
        # Caso simples sem misturas
        valor_corrigido = valor_limpo.replace(',', '.')

    # Converte para float
    return float(valor_corrigido)


def formatar_monetario(valor):
    # Configura o locale para português do Brasil
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    return locale.currency(valor, grouping=True)
