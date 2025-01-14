import psycopg2

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="TJSP_DJE",
            user="postgres",
            password="5246"
        )
        return connection
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


# # Script SQL para criar as tabelas
# create_tables_sql = """
# CREATE TABLE IF NOT EXISTS DJE_process_numbers (
#     id SERIAL PRIMARY KEY,
#     Cod_Processo VARCHAR(38),
#     Range_ini TIMESTAMP,
#     Range_end TIMESTAMP,
#     Num_req INT DEFAULT 0, -- Valor padrão 0
#     Last_req INT DEFAULT 0 -- Valor padrão 0
# );

# CREATE TABLE IF NOT EXISTS Req_pagamentos (
#     id SERIAL PRIMARY KEY,
#     Nome_Req VARCHAR(150),
#     CPF_Req VARCHAR(150),
#     Cod_Processo VARCHAR(38),
#     Seq INT,
#     Advogado VARCHAR(150),
#     Valor_Processo DECIMAL,
#     Data_doc DATE,
#     Data_emissão_termo_dec DATE,
#     Ent_Devedora VARCHAR(250),
#     Princ_Liq DECIMAL,
#     Link TEXT
# );
# """

# try:
#     # Conectar ao banco de dados
#     connection = psycopg2.connect(**db_config)
#     cursor = connection.cursor()

#     # Executar o script SQL para criar as tabelas
#     cursor.execute(create_tables_sql)
#     connection.commit()

#     print("Tabelas criadas com sucesso!")

# except Exception as e:
#     print(f"Erro ao criar as tabelas: {e}")

# finally:
#     # Fechar a conexão
#     if 'connection' in locals() and connection:
#         cursor.close()
#         connection.close()
#         print("Conexão ao banco de dados encerrada.")