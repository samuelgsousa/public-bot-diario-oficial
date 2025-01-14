# painel.py

# Valor mínimo do precatório
 
VALOR_MINIMO = float(150000)  # preferencialmente sem vírgulas
USUARIO = 'XXXXXXXXXXXX'
SENHA = 'XXXXXX'

# USUARIO = 'XXXXXXXXXXXX'
# SENHA = 'XXXXXX'

# XPATH = "//*[contains(text(), 'limite diário')]" #caminho pra achar o popup de limite diário

#classe para 
class Precatorio:
    def __init__(self, num, valido: bool, valor: float = 0.0):
        self.num = num
        self.valido = valido
        self.valor = valor

    def __repr__(self):
        return f"Precatorio(numero={self.num}, valido={self.valido}, valor={self.valor})"
    

class SessaoExpirada(Exception): 
    pass

class LimiteConsultas(Exception): 
    print("LIMITE DE CONSULTAS ATINGIDO!!!")
    pass

class NenhumaConta(Exception): 
    pass