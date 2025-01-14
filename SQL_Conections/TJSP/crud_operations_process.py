import psycopg2
from SQL_Conections.TJSP.connect import get_db_connection
from psycopg2 import errors


def insert_process(connection, Cod_Processo, Range_ini, Range_end):

    """
    Função para adicionar um novo processo ao banco de dados.

    Parâmetros:
    connection: conexão com o banco de dados. Passado como argumento para não gerar overhead, visto que essa função é executada em loop.
    Cod_Processo (str): Código do processo
    Range_ini (str): Data de início da busca
    Range_end (str): Data final da busca

    Retorna:
    None: Esta função não retorna valor, apenas atualiza o status no banco de dados.
    
    """

    #connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO dje_process_numbers 
                    (cod_processo, range_ini, range_end)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (cod_processo) DO NOTHING
                    RETURNING cod_processo
                """
                cursor.execute(sql, (Cod_Processo, Range_ini, Range_end))

                resultado = cursor.fetchone()  # Captura o retorno da operação
                
                if resultado:
                    print("Processo inserido com sucesso!")
                else:
                    print(f"O código de processo '{Cod_Processo}' já existe na tabela. Não será inserido novamente.")

                connection.commit()

        except psycopg2.Error as e:
            connection.rollback()  # Reverte apenas a iteração com erro
            print(f"Erro ao inserir Processo: {e}")
    else:
        raise print("[ERRO] - Nenhuma conexão com o banco de dados estabelecida")

def update_process(cod_processo, campo, dado):
    """
    Função para atualizar determinado campo de um item da tabela dje_process_numbers

    Exemplo: 
    
    update_process('0005591-63.2023.8.26.0348','num_req', 5) #atualiza o número de requisições de pagamento

    Parâmetros:
       - cod_processo(str): código do processo que será atualizdo
       - campo(str): coluna que será atualizada
       - dado(any): dado que será inserido na coluna

    Retorna:
    None: Esta função não retorna valor, apenas atualiza o status no banco de dados.
    
    """

    connection = get_db_connection()

    if connection:
        try:
            with connection.cursor() as cursor:
                sql = f"UPDATE dje_process_numbers SET {campo} = %s WHERE cod_processo = %s"
                cursor.execute(sql, (dado, cod_processo))  # Passa os valores como parâmetros
                connection.commit()

        except psycopg2.Error as e:
            print(f"Erro ao atualizar a tabela dje_process_numbers: {e}")
        
        connection.close()

    else:
        raise print('[ERRO] - Conexão com o banco de dados não estabelecida')


   
def get_process():
    """
    Busca todos os processos que não foram processados
    """
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT cod_processo FROM dje_process_numbers WHERE processado = false ORDER BY id")
                resultados = cursor.fetchall()

                codigos_processos = [resultado[0] for resultado in resultados]
                return codigos_processos
            
        except psycopg2.Error as e:
            print(f"Erro ao buscar requisições: {e}")
        finally:
            connection.close()


def get_last_req(processo):
    """
    Busca a última requisição de pagamento a ser processada para aquele precatório. Ùtil em caso de interrupção do código
    """
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "SELECT last_req FROM dje_process_numbers WHERE cod_processo = %s"
                cursor.execute(sql, (processo,))  

                resultado = cursor.fetchone()  
                return resultado[0] if resultado else None  # Retorna o valor ou None se não houver resultado
            
        except psycopg2.Error as e:
            print(f"Erro ao buscar requisições: {e}")
        finally:
            connection.close()


def clean_table_process():
    
    print("Limpando Tabela de Processos")

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = "TRUNCATE dje_process_numbers"
                cursor.execute(sql)
                connection.commit()
                print('Tabela Limpa com Sucesso')
            
        except psycopg2.Error as e:
            connection.rollback()
            print(f"Erro ao Limpar Tabela: {e}")
        finally:
            connection.close()



