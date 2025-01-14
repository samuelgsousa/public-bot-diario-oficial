import psycopg2
from SQL_Conections.TJSP.connect import get_db_connection
from psycopg2.extras import RealDictCursor


from datetime import date

def verificar_limite_diario():
    """
    Função para atualizar o status de disponibilidade da conta somente se o limite diário tiver sido atingido no dia anterior
    A variável "hoje" busca a data atual.
    Uma condicional na query garante que uma conta só fique disponível para processar precatórios caso a data limite não tenha sido atingida no mesmo dia da execução do código
    
    """

    connection = get_db_connection()

    with connection.cursor() as cursor:
        hoje = date.today()

        print(f"data de hoje: {hoje}")

        sql = """
        UPDATE contas
        SET limite_atingido = FALSE, data_limite = NULL
        WHERE data_limite < %s OR data_limite IS NULL;
        """
        cursor.execute(sql, (hoje,))
        connection.commit()

    connection.close() 


def verificar_conta_disponivel():


    connection = get_db_connection()
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        sql = """
        SELECT id, usuario, senha
        FROM contas
        WHERE limite_atingido = FALSE
        ORDER BY id ASC
        LIMIT 1;
        """
        cursor.execute(sql)
        conta = cursor.fetchone()
        return conta
    
    except psycopg2.Error as e:
            print(f"Erro ao buscar conta: {e}")

    
def update_conta(id, campo, dado):
    """
    Função para atualizar determinado campo de um item da tabela contas

    Exemplo: 


    Parâmetros:
        id(int): id do item que será atualziado
        campo(str): coluna que será atualizada
        dado(any): dado que será inserido na 
        
    Retorna:
    None: Esta função não retorna valor, apenas atualiza o status no banco de dados.
    
    """

    connection = get_db_connection()

    if connection:
        try:
            with connection.cursor() as cursor:
                sql = f"UPDATE contas SET {campo} = %s WHERE id = %s"
                cursor.execute(sql, (dado, id))  # Passa os valores como parâmetros
                connection.commit()

        except psycopg2.Error as e:
            print(f"Erro ao atualizar contas: {e}")
        
        connection.close() 

    else:
        raise print('[ERRO] - Conexão com o banco de dados não estabelecida')