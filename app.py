from datetime import datetime
from SQL_Conections.TJSP.crud_operations_contas import verificar_conta_disponivel, verificar_limite_diario
from painel import NenhumaConta
import ptvsd

from SQL_Conections.TJSP.crud_operations_historico import insert_historic, update_historic #get_last_exec,
from SQL_Conections.TJSP.crud_operations_process import clean_table_process, get_process
from SQL_Conections.TJSP.crud_operations_req_pagamentos import get_all_req_not_exported, update_exported_status
from scraping.TJSP import extraiTermo
from utils import exportar_csv, redefinir_contagem


from SQL_Conections.TJSP.crud_operations_historico import get_last_exec as get_last_exec_tjsp

# Permite a conexão com o depurador do VSCode na porta 5678
ptvsd.enable_attach(address=("localhost", 5678))
ptvsd.wait_for_attach()  # Aguarda a conexão do depurador


import streamlit as st
from scraping.TJSP.diario_tjsp import search_diario_tjsp
from scraping.driver import start_driver
from scraping.TJSP.consulta_processos_tjsp import consultar_processo_individual
import time
import os

def credenciais(usuario, senha, process_numbers):
    if usuario and senha:
        st.write("Consultando o processo no TJSP...")
        consultar_processo_individual(usuario, senha, process_numbers)
    else:
        st.warning("Por favor, preencha todos os campos para consultar o processo.")

def fechar_streamlit():
    st.write("Encerrando a aplicação...")
    os._exit(0)  # Encerra o processo imediatamente

def main():
    st.title("Consulta de Processos - DJE")

    # Seleção do Tribunal
    tribunal = st.selectbox("Selecione o Tribunal:", ["TJSP"])

    if tribunal == "TJSP":
        st.subheader("Consulta DJE - TJSP")
        
        # Campos específicos para o TJSP usando input de data
        data_inicio = st.date_input("Data Início:")
        data_fim = st.date_input("Data Fim:")
        with st.expander("Instruções para a Pesquisa"):
            st.markdown("""
            Você pode usar operadores lógicos para refinar sua pesquisa na palavra-chave. Os operadores disponíveis são:

            - <span style="font-weight:bold; font-size:16px;">E</span>: Retorna resultados que contêm **ambas** as palavras.
                - *Exemplo*: `palavra1 E palavra2` retorna resultados que contêm **palavra1** **e** **palavra2**.
            
            - <span style="font-weight:bold; font-size:16px;">OU</span>: Retorna resultados que contêm pelo menos **uma** das palavras.
                - *Exemplo*: `palavra1 OU palavra2` retorna resultados que contêm **palavra1** **ou** **palavra2**.
            
            - <span style="font-weight:bold; font-size:16px;">NÃO</span>: Exclui resultados que contêm a palavra seguinte.
                - *Exemplo*: `palavra1 NÃO palavra2` retorna resultados que contêm **palavra1** mas **não** contêm **palavra2**.
            
            - <span style="font-weight:bold; font-size:16px;">?</span>: Substitui **um** caractere na palavra.
                - *Exemplo*: `palavr?` pode retornar **palavra**, **palavre**, **palavro**.
            
            - <span style="font-weight:bold; font-size:16px;">\*</span>: Substitui **zero ou mais** caracteres na palavra.
                - *Exemplo*: `palav*` pode retornar **palavra**, **palavras**, **palavrinhas**.
            
            - <span style="font-weight:bold; font-size:16px;">"" (aspas duplas)</span>: Pesquisa a **frase exata**.
                - *Exemplo*: `"frase exata"` retorna resultados que contêm exatamente **frase exata**.

            **Nota:** Certifique-se de utilizar os operadores em maiúsculas conforme apresentado.
            """, unsafe_allow_html=True)
        palavra_chave = st.text_input("Palavra Chave:")

        # usuario = st.text_input("Usuário e-SAJ TJSP:", type="default", value="XXXXXXXXXXXX")
        # senha = st.text_input("Senha e-SAJ TJSP:", type="password", value="XXXXXX")

        def iniciar_consulta(palavra_chave, data_inicio, data_fim):
                try:
                    # Converte as datas para o formato dd/mm/aaaa
                    data_inicio_str = data_inicio.strftime("%d/%m/%Y")
                    data_fim_str = data_fim.strftime("%d/%m/%Y")

                    hist = get_last_exec_tjsp()

                    if hist['paginacao_conc'] == False: #se a páginação não for concluída ou iniciada, irá extrair processos
                        #Inicializa o driver do Selenium
                        driver = start_driver()

                        st.write(f"Buscando no DJEN-SP com a palavra chave: {palavra_chave}, entre {data_inicio.strftime('%d/%m/%Y')} e {data_fim.strftime('%d/%m/%Y')}...")
                        
                        search_diario_tjsp(driver, palavra_chave, data_inicio_str, data_fim_str, hist) #busca processos no site do DJE
                        
                        driver.quit()
                    else:
                        print('Paginação dessa consulta já foi concluída')

                    process_numbers = get_process()

                    if process_numbers:

                        verificar_limite_diario()
                        conta = verificar_conta_disponivel()

                        if conta is None:
                            raise NenhumaConta

                        st.success(f"{len(process_numbers)} Processos encontrados: {process_numbers}")

                        st.write("Consultando o processo no TJSP...")

                        consultar_processo_individual(conta['usuario'], conta['senha'], process_numbers)

                        end_exec = get_last_exec_tjsp()
                        update_historic(end_exec['id'], 'status', 'concluído')

                        st.warning("Consulta finalizada. Encerrando em 3 segundos.")
                        time.sleep(3)
                        fechar_streamlit()

                    else:
                        st.warning("Nenhum número de processo foi encontrado no scraping.")

                except NenhumaConta:

                    st.error("Todas as contas atingiram o limite diário de consultas! Adicione uma nova conta ou tente novamente amanhã")
                    time.sleep(3)
                    fechar_streamlit()

        historico = get_last_exec_tjsp()


        if historico:
            st.warning('Última consulta não foi finalizada! Clique em "Continuar última execução" para retomar ou em "Buscar no DJE - TJSP" para iniciar uma nova consulta')

            text = f"Dados da última execução:<br> Termo de busca: {historico['palavra_chave']} <br> Data Início: {historico['data_inicio']} <br> Data Fim: {historico['data_fim']} <br> Consulta Iniciada em: {historico['data_exec']}"

            st.markdown(f"""
                            <div style="background-color: rgba(61, 213, 109, 0.2); padding: 10px; border-radius: 5px;">
                                {text}
                            </div>
                            <br>
                        """, unsafe_allow_html=True)
            
            # Botão para continuar última busca
            if st.button("Continuar última execução"):
                
                palavra_chave = historico['palavra_chave']
                data_inicio = historico['data_inicio']
                data_fim = historico['data_fim']

                num_exec = 0
                max_tentativas = 10

                while num_exec < max_tentativas:
                    try:
                        iniciar_consulta(palavra_chave, data_inicio, data_fim)
                        break  # Sai do loop se a função for bem-sucedida
                    except Exception as e:
                        num_exec += 1
                        print(f"Tentativa {num_exec}/{max_tentativas} falhou: {e}")
                        if num_exec >= max_tentativas:
                            print("Número máximo de tentativas alcançado!")
                            raise e  # Relança a exceção para lidar fora do loop, se necessário
                        else:
                            time.sleep(5)  # Aguarda antes de tentar novamente

        # Botão para buscar
        if st.button("Buscar no DJE - TJSP"):
            
            redefinir_contagem()

            if data_inicio and data_fim and palavra_chave:
                clean_table_process() #Limpando tabela que contém os processos 
                if historico:
                    update_historic(historico['id'], 'status', 'interrompido')

                insert_historic(palavra_chave, data_inicio, data_fim) #criar uma nova excução no histórico

                num_exec = 0
                max_tentativas = 10
                
                while num_exec < max_tentativas:
                    try:
                        iniciar_consulta(palavra_chave, data_inicio, data_fim)
                        break  # Sai do loop se a função for bem-sucedida
                    except Exception as e:
                        num_exec += 1
                        print(f"Tentativa {num_exec}/{max_tentativas} falhou: {e}")
                        if num_exec >= max_tentativas:
                            print("Número máximo de tentativas alcançado!")
                            raise e  # Relança a exceção para lidar fora do loop, se necessário
                        else:
                            time.sleep(5)  # Aguarda antes de tentar novamente

            else:
                st.warning("Por favor, preencha todos os campos para a busca.")


if __name__ == "__main__":
    main()