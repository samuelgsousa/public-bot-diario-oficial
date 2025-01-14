import psycopg2
from SQL_Conections.TJSP.connect import get_db_connection
from psycopg2.extras import RealDictCursor

def insert_historic(palavra_chave, data_ini, data_fim):
    connection = get_db_connection()

    if connection:
        try:
            with connection.cursor() as cursor:
                # Iniciar nova execução
                sql = """
                INSERT INTO historico_exec (palavra_chave, data_inicio, data_fim)
                VALUES (%s, %s, %s) RETURNING id;
                """
                cursor.execute(sql, (palavra_chave, data_ini, data_fim))
                connection.commit()
                return cursor.fetchone()[0]  # Retorna o ID da execução
        finally:
            connection.close()

    else:
        raise print('[ERRO] - Conexão com o banco de dados não estabelecida')

def get_last_exec():
    connection = get_db_connection()

    if connection:
        try:
            # Configurando o cursor para retornar resultados como dicionários
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            # Query para buscar o último registro não concluído
            sql = """
                SELECT *
                FROM historico_exec
                WHERE status = %s
                LIMIT 1
            """
            cursor.execute(sql, ("não concluído",))
            resultado = cursor.fetchone()
            
            return resultado
            
        except psycopg2.Error as e:
            print(f"Erro ao buscar requisições: {e}")
            return None
        finally:
            connection.close()
    else:
        raise Exception('[ERRO] - Conexão com o banco de dados não estabelecida')
    

def update_historic(id, campo, dado):
    """
    Função para atualizar determinado campo de um item da tabela historico_exec

    Exemplo: 


    Parâmetros:
        id(int): id do item que será 
        campo(str): coluna que será atualizada
        dado(any): dado que será inserido na coluna

    Retorna:
    None: Esta função não retorna valor, apenas atualiza o status no banco de dados.
    
    """

    connection = get_db_connection()

    if connection:
        try:
            with connection.cursor() as cursor:
                sql = f"UPDATE historico_exec SET {campo} = %s WHERE id = %s"
                cursor.execute(sql, (dado, id))  # Passa os valores como parâmetros
                connection.commit()

        except psycopg2.Error as e:
            print(f"Erro ao atualizar historico_exec: {e}")
        
        connection.close() #deve ser mais eficiente chamar antes e depois de executar o loop da função

    else:
        raise print('[ERRO] - Conexão com o banco de dados não estabelecida')
    