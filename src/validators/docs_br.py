import re

def validate_cpf(cpf: str) -> dict:
    """
    Valida um CPF utilizando o algoritmo do módulo 11.
    Retorna um dicionário com o status e detalhes.
    """
    if not isinstance(cpf, str):
        return {"status": "Formato incorreto", "detalhes": "Não é uma string"}
    
    # Remove caracteres não numéricos
    numbers = re.sub(r'[^0-9]', '', cpf)
    
    if len(numbers) != 11:
        return {"status": "Formato incorreto", "detalhes": f"Tamanho inválido: {len(numbers)} dígitos"}
    
    # Verifica se todos os dígitos são iguais (caso comum que passa no algoritmo mas é inválido)
    if numbers == numbers[0] * 11:
        return {"status": "Inválido (Todos os dígitos iguais)", "detalhes": "Dígitos repetidos"}
        
    # Validação do primeiro dígito verificador
    sum_1 = sum(int(numbers[i]) * (10 - i) for i in range(9))
    expected_dv1 = 11 - (sum_1 % 11)
    if expected_dv1 >= 10:
        expected_dv1 = 0
        
    if int(numbers[9]) != expected_dv1:
        return {"status": "Inválido (DV incorreto)", "detalhes": "Primeiro dígito verificador falhou"}
        
    # Validação do segundo dígito verificador
    sum_2 = sum(int(numbers[i]) * (11 - i) for i in range(10))
    expected_dv2 = 11 - (sum_2 % 11)
    if expected_dv2 >= 10:
        expected_dv2 = 0
        
    if int(numbers[10]) != expected_dv2:
        return {"status": "Inválido (DV incorreto)", "detalhes": "Segundo dígito verificador falhou"}
        
    return {"status": "Válido", "detalhes": "CPF validado com sucesso"}

def validate_cnpj(cnpj: str) -> dict:
    """
    Valida um CNPJ utilizando o algoritmo do módulo 11.
    Retorna um dicionário com o status e detalhes.
    """
    if not isinstance(cnpj, str):
        return {"status": "Formato incorreto", "detalhes": "Não é uma string"}
        
    # Remove caracteres não numéricos
    numbers = re.sub(r'[^0-9]', '', cnpj)
    
    if len(numbers) != 14:
        return {"status": "Formato incorreto", "detalhes": f"Tamanho inválido: {len(numbers)} dígitos"}
        
    if numbers == numbers[0] * 14:
        return {"status": "Inválido (Todos os dígitos iguais)", "detalhes": "Dígitos repetidos"}
        
    # Pesos para o cálculo do primeiro DV
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_1 = sum(int(numbers[i]) * weights_1[i] for i in range(12))
    expected_dv1 = 11 - (sum_1 % 11)
    if expected_dv1 >= 10:
        expected_dv1 = 0
        
    if int(numbers[12]) != expected_dv1:
        return {"status": "Inválido (DV incorreto)", "detalhes": "Primeiro dígito verificador falhou"}
        
    # Pesos para o cálculo do segundo DV
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_2 = sum(int(numbers[i]) * weights_2[i] for i in range(13))
    expected_dv2 = 11 - (sum_2 % 11)
    if expected_dv2 >= 10:
        expected_dv2 = 0
        
    if int(numbers[13]) != expected_dv2:
        return {"status": "Inválido (DV incorreto)", "detalhes": "Segundo dígito verificador falhou"}
        
    return {"status": "Válido", "detalhes": "CNPJ validado com sucesso"}
