import psycopg2
from SQL_Conections.TJSP.connect import get_db_connection
from psycopg2.extras import RealDictCursor
from psycopg2 import errors

def insert_requisicao(informacoes):

    """
    Função para adicionar uma nova requisição de pagamento na tabela req_pagamentos.
    O banco de dados foi configurado de forma que evita duplicações. Para isso ele utiliza uma constraint UNIQUE (cod_processo, seq).
    Caso o script tente inserir uma requisição que já existe, irá atualizar ela ao invés disso

    Parâmetros:
    informacoes (dict): dicionário contendo todos os valores que serão inseridos no banco de dados

    Retorna:
    None: Esta função não retorna valor, apenas atualiza o status no banco de dados.
    
    """

    nome_req = informacoes['Requerente']
    cpf_req = informacoes['CPF Req.']
    cod_processo = informacoes['Cod. Processo']
    seq = informacoes['Seq']
    advogado = informacoes['Advogado']
    valor_processo = informacoes['Valor do Processo']
    data_doc = informacoes['Data do documento']
    data_emissao = informacoes['Data de emissão do termo de declaração']
    ent_devedora = informacoes['Ent. Devedora']
    princ_liq = informacoes['Princ. Liq.']
    link = informacoes['Link']

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO req_pagamentos 
                    (Nome_Req, CPF_Req, Cod_Processo, Seq, Advogado, Valor_Processo, Data_doc, Data_emissão_termo_dec, Ent_Devedora, Princ_Liq, Link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (cod_processo, seq)
                    DO UPDATE SET Valor_Processo = EXCLUDED.Valor_Processo;
                """
                cursor.execute(sql, (nome_req, cpf_req, cod_processo, seq, advogado, valor_processo, data_doc, data_emissao, ent_devedora, princ_liq, link))
                connection.commit()
                print("Requisição de pagamento inserida com sucesso!")

        except errors.UniqueViolation:
            print(f"Erro: A requisição: {cod_processo}/{seq} já existe na tabela. Não será inserida novamente!")
            connection.rollback()
            return False
    
        except psycopg2.Error as e:
            print(f"Erro ao inserir requisição: {e}")
        finally:
            connection.close()

def get_all_req_not_exported():

    """
    Função para buscar todas as requisições que não foram exportadas para o excel (Geralmente retorna uma só)

    Parâmetros:
    Nenhum

    Retorna:
    req_non_exported (Array) contendo todas as requisições que não foram exportadas para o excel
    
    """

    connection = get_db_connection()

    if connection:
        try:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM req_pagamentos WHERE exportado = false")
                resultados = cursor.fetchall()

                
                return resultados
            
        except psycopg2.Error as e:
            print(f"Erro ao buscar requisições: {e}")
            return None
        finally:
            connection.close()

    else:
        raise print('[ERRO] - Conexão com o banco de dados não estabelecida')
    
def update_exported_status(ids):

    """
    Função para

    Exemplo: 


    Parâmetros:


    Retorna:
    None: Esta função não retorna valor, apenas atualiza o status no banco de dados.
    
    """

    connection = get_db_connection()

    if connection:
        try:
            with connection.cursor() as cursor:
                placeholders = ', '.join(['%s'] * len(ids))  # Gera o número correto de placeholders
                sql = f"UPDATE req_pagamentos SET exportado = true WHERE id IN ({placeholders})"
                cursor.execute(sql, (ids))  # Passa os valores como parâmetros
                connection.commit()

        except psycopg2.Error as e:
            print(f"Erro ao atualizar Número de requisições: {e}")
        
        connection.close() #deve ser mais eficiente chamar antes e depois de executar o loop da função

    else:
        raise print('[ERRO] - Conexão com o banco de dados não estabelecida')
