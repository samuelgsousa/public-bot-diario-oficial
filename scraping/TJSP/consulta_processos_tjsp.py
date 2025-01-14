from datetime import date
import re
import time
import os
from SQL_Conections.TJSP.crud_operations_contas import update_conta, verificar_conta_disponivel
from painel import SENHA, USUARIO, LimiteConsultas, NenhumaConta, SessaoExpirada
import pdfplumber
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from SQL_Conections.TJSP.crud_operations_process import get_last_req, update_process
from utils import baixar_doc, buscar_termo_pdf, voltar_pagina_anterior
from utils import limpar_pastas

# Importando módulos separados para processamento (executando pelo app.py)
from . import extraiTermo
from . import extraiOficio

# # Se for executar manual, tem que importar aqui
# import extraiTermo
# import extraiOficio


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

def login_tjsp(driver, usuario, senha):

    #botao sair xpath: "//a[contains(text(),'Sair')]"



    print("Acessando o site de login do TJSP...")
    driver.get('https://esaj.tjsp.jus.br/sajcas/login')

    time.sleep(2)
    
    #Verifica se uma sessão está iniciada no momento e encerra. Não faz nada se não houver
    try: 
        botao_sair = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Sair')]"))
            )
        
        print("encerrando sessão atual")

        # Clica no link localizado
        botao_sair.click()

        print("Redirecionando para a página de login novamente")
        driver.get('https://esaj.tjsp.jus.br/sajcas/login')
        time.sleep(5)
    except:
        ...

    input_usuario = driver.find_element(By.ID, 'usernameForm')
    input_usuario.send_keys(usuario)
    input_senha = driver.find_element(By.ID, 'passwordForm')
    input_senha.send_keys(senha)
    input_senha.send_keys(Keys.RETURN)
    time.sleep(3)

def verificar_mensagem_erro(driver):
    try:
        mensagem_erro = driver.find_element(By.ID, 'mensagemRetorno').text
        if "Não existem informações disponíveis" in mensagem_erro or "tipo de pesquisa informado é inválido" in mensagem_erro:
            print(f"Consulta inválida: {mensagem_erro}")
            return True
    except:
        return False



def download_pdf(driver):
    try:
        # Alterna para o iframe onde o visualizador de PDF está presente
        iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, 'documento'))
        )
        driver.switch_to.frame(iframe)

        # Espera até que o botão de download esteja presente, visível e clicável dentro do iframe
        download_button = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//*[@id='download']"))
        )

        # Verifica se o botão está presente e visível
        if download_button.is_displayed():
            print("Botão de download encontrado. Tentando clicar...")
            driver.execute_script("arguments[0].click();", download_button)

            # Caminho para a pasta de downloads
            download_dir = os.path.join(os.getcwd(), 'data')
            
            # Espera até que o arquivo seja baixado na pasta 'data'
            timeout = 60  # Timeout em segundos
            end_time = time.time() + timeout
            downloaded_file = None

            while time.time() < end_time:
                # Procura por arquivos na pasta de download
                files = os.listdir(download_dir)
                pdf_files = [f for f in files if f.endswith('.pdf')]
                
                if pdf_files:
                    downloaded_file = pdf_files[0]  # Assume que o primeiro PDF encontrado é o que foi baixado
                    break
                time.sleep(1)

            if downloaded_file:
                # Renomeia o arquivo baixado para 'documento.pdf'
                old_path = os.path.join(download_dir, downloaded_file)
                new_path = os.path.join(download_dir, 'documento.pdf')
                os.rename(old_path, new_path)
                print("PDF baixado e renomeado com sucesso.")
                return new_path
            else:
                print("[ERRO] O PDF não foi encontrado no caminho esperado.")
                return None
        else:
            print("[ERRO] O botão de download não está visível.")
            return None

    except TimeoutException:
        print("[ERRO] Botão de download não foi encontrado ou não é clicável.")
        return None
    except NoSuchElementException:
        print("[ERRO] Botão de download não encontrado.")
        return None
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado: {e}")
        return None
    finally:
        # Retorna ao contexto principal da página após tentar a operação
        driver.switch_to.default_content()

def processar_documentos(driver, url_precatorio, num_final_prec):
    try:
       # documentos = driver.find_elements(By.XPATH, "//li[contains(@class, 'jstree-leaf')]//a[contains(@class, 'jstree-anchor')]")
        
        caminho_pdf = baixar_doc(driver)
        #buscar_palavra_chave_PDF(caminho_pdf)

        paginas_com_cessao = buscar_termo_pdf(caminho_pdf, "cessão de crédito")

        if paginas_com_cessao:
            print('TERMO: "cessão de crédito" encontrado no documento!!! Precatório já foi vendido, não será adicionado')
            
        else:
            paginas_com_termo_declaracao = buscar_termo_pdf(caminho_pdf, "termo de declaração")
            #print(f"Páginas com termo de declaração: {paginas_com_termo_declaracao}")

            paginas_com_oficio = buscar_termo_pdf(caminho_pdf, "ofício requisitório")
            #print(f"Páginas com ofício requisitório: {paginas_com_oficio}")

            if len(paginas_com_termo_declaracao) > 0:
                extraiTermo.extrair_informacoes_pdf_por_paginas(caminho_pdf, url_precatorio, paginas_com_termo_declaracao, num_final_prec)
            else:
                print("Nenhuma página com 'termo de declaração' ")

            if len(paginas_com_oficio) > 0:
                extraiOficio.extrair_informacoes_pdf_por_paginas(caminho_pdf, url_precatorio, paginas_com_oficio, num_final_prec)
            else:
                print("Nenhuma página com 'ofício requisitório' ")
                
            #     time.sleep(1)

            print("Todos os termos foram processados no documento.")


        try:
            os.remove(caminho_pdf)
            print(f"Arquivo {caminho_pdf} deletado com sucesso.")
        except OSError as e:
            print(f"[ERRO] Não foi possível deletar o arquivo {caminho_pdf}: {e}")
        
        limpar_pastas()
        return True
    
    except SessaoExpirada:
        raise
    
    except Exception as e:
        print(f"[ERRO] Falha ao processar documentos: {e}")
        limpar_pastas()
        
        return False
    # Fechando a aba atual
    
def abrir_autos(driver, wait):
    # Localiza e clica no link que abre a sub-janela
    link_autos = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'linkPasta')))
    print(f"Link para 'Visualizar autos' encontrado.")

    original_handles = driver.window_handles

    driver.execute_script("arguments[0].click();", link_autos)

    try:
        # Aguarda que uma nova janela seja aberta
        new_window_handle = WebDriverWait(driver, 10).until(
            lambda d: next((handle for handle in d.window_handles if handle not in original_handles), None)
        )

        return new_window_handle

    except:
        print("Nova janela não foi aberta! Verificando se o limite de consultas foi atingido")
        try:
            limite = EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'limite diário')]")) #não é necessáro adicionar tempo de espera, pois se a janela não carregar em 10 segudos, o popup vai
            #limite = EC.presence_of_element_located((By.XPATH, "//*"))
            
            if limite:
                raise LimiteConsultas #Sobe o erro indicando limite de consultas atingido
            else:
                print("Não foi encontrada nenhuma mensagem sobre o limite de consultas! Em caso de dúvidas, verifique os XPaths")
        
        except LimiteConsultas:
            raise LimiteConsultas
        
        except:
            print("Não foi encontrada nenhuma mensagem sobre o limite de consultas! Em caso de dúvidas, verifique os XPaths")
        
def iniciar_nova_sessao(driver, aba_original, guia_precatorio):
    driver.switch_to.window(aba_original)                            
    driver.switch_to.window(guia_precatorio)

    driver.execute_script("window.open('');")
    time.sleep(1)

    # Mudar para a nova guia
    driver.switch_to.window(driver.window_handles[-1])
    
    conta = verificar_conta_disponivel() #Pega a conta que não atingiu o limite diário

    if conta is None: 
        driver.close()
        driver.switch_to.window(guia_precatorio)
        driver.close()
        driver.switch_to.window(aba_original)
        driver.close()
        raise NenhumaConta


    login_tjsp(driver, conta['usuario'], conta['senha'])

    # Voltar para a guia original
    driver.close()
    driver.switch_to.window(guia_precatorio)
    # Fechar a nova guia
    # Recarregar a página
    driver.refresh()
    time.sleep(2)

def consultar_processo(driver, numero_processo_completo):
    print(f"Consultando o processo: {numero_processo_completo}")
    driver.get('https://esaj.tjsp.jus.br/cpopg/open.do')

    numero_digito_ano = numero_processo_completo[:17]
    numero_foro = numero_processo_completo[-4:]

    campo_numero_digito_ano = driver.find_element(By.ID, 'numeroDigitoAnoUnificado')
    campo_foro = driver.find_element(By.ID, 'foroNumeroUnificado')

    campo_numero_digito_ano.clear()
    campo_numero_digito_ano.send_keys(numero_digito_ano)
    campo_foro.clear()
    campo_foro.send_keys(numero_foro)

    campo_foro.send_keys(Keys.RETURN)
    time.sleep(5)

    if verificar_mensagem_erro(driver):
        update_process(numero_processo_completo, 'processado', True)
        return None
    try:
        wait = WebDriverWait(driver, 10)
        # Obtém todos os links de Requisições de Pagamento do precatório
        link_precatorios = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class, 'incidente') and contains(text(), 'Precatório')]")))
        print(f'{len(link_precatorios)} Requisições de Pagamento foram encontradas nesse processo')

        update_process(numero_processo_completo, 'num_req', len(link_precatorios)) #Atualizar número total do processo do momento

        print("Processando Requisições...")

        aba_original = driver.current_window_handle
        
        start_index = get_last_req(numero_processo_completo)
        print(f"A última requisição processada para este precatório foi a de índice: {start_index}")

        if start_index > len(link_precatorios):
            print("Todos as requisições para este precatório já foram processadas! Passando para o próximo")
            update_process(numero_processo_completo, 'processado', True) #atualizando status de processamento
        else:
            for i, link in enumerate(link_precatorios[start_index - 1:], start=start_index):
                try:
                # Abre cada link em uma nova guia
                #Pegar número do precatório
                    numeros = re.findall(r'\d+', link.text)
                    num_formatado = str(int(numeros[0])).zfill(2)

                    #print(f"número inteiro: {num_formatado}")

                    driver.execute_script("window.open(arguments[0].href, '_blank');", link)

                    time.sleep(2)  # Atraso para garantir que a nova guia tenha carregado

                    print(f'Processando Requisição de Pagamento [{i} / {len(link_precatorios)}]')

                    guia_precatorio = driver.window_handles[-1]  # Última guia aberta
                    driver.switch_to.window(guia_precatorio)

                    time.sleep(2)
                    url_precatorio = driver.current_url
                    print(f"URL da página após clicar em 'Precatório': {url_precatorio}")

                    MAX_TENTATIVAS = 3  # Número máximo de tentativas por requisição
                    tentativas = 0      # Contador de tentativas
                    processado_com_sucesso = False # Flag para controlar o processamento bem-sucedido

                    while tentativas < MAX_TENTATIVAS and not processado_com_sucesso: #Esse loop serve para tentar novamente apenas em caso dos erros específicos SessaoExpirada e LimiteConsultas
                        try:
                            tentativas += 1  # Incrementa o número de tentativas
                            #print(f"Tentativa {tentativas} de {MAX_TENTATIVAS}...")

                            # Abre a nova janela
                            new_window_handle = abrir_autos(driver, wait)
                            driver.switch_to.window(new_window_handle)

                            # Processa os documentos
                            time.sleep(4)
                            processar_documentos(driver, url_precatorio, num_formatado)
                            
                            # Se chegou até aqui, processou com sucesso
                            processado_com_sucesso = True
                            print("Processamento concluído com sucesso!")

                        except SessaoExpirada: #Esse erro ocorre na função de baixar_doc que está em processar_documentos
                            print("[ERRO] Sessão expirada. Tentando reiniciar...")
                            driver.close()  # Fecha a janela aberta
                            
                            # Inicia nova sessão e tenta novamente
                            iniciar_nova_sessao(driver, aba_original, guia_precatorio)

                        except LimiteConsultas:
                            print("[ERRO] Limite de consultas atingido. Trocando de conta...")
                            hoje = date.today()

                            # Atualiza conta atual e busca uma nova
                            conta = verificar_conta_disponivel()
                            update_conta(conta['id'], 'limite_atingido', True)
                            update_conta(conta['id'], 'data_limite', hoje)

                            # Inicia nova sessão com a próxima conta disponível
                            iniciar_nova_sessao(driver, aba_original, guia_precatorio)

                        except NenhumaConta:
                            raise

                        except Exception as e:
                            print(f"[ERRO] Falha inesperada na tentativa {tentativas}: {e}")
                            processado_com_sucesso = True
            
                    #limpando abas e voltando para a guia original do processo
                    if len(driver.window_handles) > 1:
                        driver.close()
                    
                    todas_janelas = driver.window_handles
                    for janela in todas_janelas:
                        if janela != aba_original:
                            driver.switch_to.window(janela)
                            driver.close()

                    # Retorna para a aba original
                    driver.switch_to.window(aba_original)

                    # Finaliza o processamento e atualiza o status
                    if processado_com_sucesso:
                        update_process(numero_processo_completo, 'last_req', i + 1)
                        print("Atualização de requisição feita com sucesso.")
                    else:
                        print(f"[FALHA] Não foi possível processar após {MAX_TENTATIVAS} tentativas.")


                    update_process(numero_processo_completo, 'last_req', i+1 ) #atualizando última requisição processada

                    if i >= len(link_precatorios):
                        print("Processamento de precatório concluído! Passando para o próximo")
                        update_process(numero_processo_completo, 'processado', True) #atualizando status de processamento
            
                except NenhumaConta:
                    raise
                except Exception as e:
                    print(f'[ERRO] Falha ao processar Requisição [{i} / {len(link_precatorios)}]: {e}')
                    update_process(numero_processo_completo, 'last_req', i+1 ) #atualizando última requisição processada

                    if i >= len(link_precatorios):
                        print("Todos as requisições para este precatório já foram processadas! Passando para o próximo")
                        #update_process(numero_processo_completo, None, None, True) #atualizando status de processamento
    except NenhumaConta:
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar o processamento dos precatórios: {e}") #ocorre geralmente quando não é um precatório
        update_process(numero_processo_completo, 'processado', True)
    except TimeoutException:
        print("[ERRO] Tempo excedido ao esperar pelos links 'Precatório' ou 'Visualizar autos'.")
        update_process(numero_processo_completo, 'processado', True)
    except NoSuchElementException:
        print("[ERRO] Link 'Precatório' ou 'Visualizar autos' não encontrado.")
        update_process(numero_processo_completo, 'processado', True)
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao tentar acessar o link: {e}")
        driver.save_screenshot('screenshot.png')
        print("[DEBUG] Screenshot salva como 'screenshot.png'. Verifique a imagem para analisar o estado da página.")
        update_process(numero_processo_completo, 'processado', True)
    except:
        update_process(numero_processo_completo, 'processado', True)

def consultar_processo_individual(usuario, senha, lst_numeros_processo):
    #PUXAR PROCESSOS DO BANCO DE DADOS AQUI
    driver = start_driver()
    login_tjsp(driver, usuario, senha)
    for numero in lst_numeros_processo:
        try:
            consultar_processo(driver, numero)
            print("Consulta do processo concluída.")

        except NenhumaConta:
            raise

        except Exception as e:
            print(f"[ERRO] Ocorreu um erro ao consultar processo: {e}")
        except TimeoutException as ex:
            print(f"[ERRO] Sessão desconectada. Reconectando...")
            driver = start_driver()
            login_tjsp(driver, usuario, senha)
            consultar_processo(driver, numero)


    driver.quit()

if __name__ == "__main__":
    usuario = "XXXXXXXXXXXX"
    senha = "XXXXXX"
    lista_processos = [
        # "0003026-11.2023.8.26.0451",
        "0001251-05.2021.8.26.0071"
    ]
    consultar_processo_individual(usuario, senha, lista_processos)