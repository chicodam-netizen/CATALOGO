import re

# Tabela de DDDs válidos no Brasil (simplificada com os principais em uso)
VALID_DDDS = {
    '11', '12', '13', '14', '15', '16', '17', '18', '19', # SP
    '21', '22', '24', # RJ
    '27', '28', # ES
    '31', '32', '33', '34', '35', '37', '38', # MG
    '41', '42', '43', '44', '45', '46', # PR
    '47', '48', '49', # SC
    '51', '53', '54', '55', # RS
    '61', # DF
    '62', '64', # GO
    '63', # TO
    '65', '66', # MT
    '67', # MS
    '68', # AC
    '69', # RO
    '71', '73', '74', '75', '77', # BA
    '79', # SE
    '81', '82', # PE, AL
    '83', # PB
    '84', # RN
    '85', '88', # CE
    '86', '89', # PI
    '87', # PE
    '91', '93', '94', # PA
    '92', '97', # AM
    '95', # RR
    '96', # AP
    '98', '99' # MA
}

def validate_phone(phone: str) -> dict:
    """
    Valida um telefone brasileiro (fixo ou celular), identificando DDD.
    """
    if not isinstance(phone, str):
        return {"status": "Formato incorreto", "detalhes": "Não é uma string"}
        
    # Remove tudo que não é dígito
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) < 10 or len(digits) > 11:
        return {"status": "Tamanho incorreto", "detalhes": f"Possui {len(digits)} dígitos"}
        
    ddd = digits[:2]
    if ddd not in VALID_DDDS:
        return {"status": "DDD Inválido", "detalhes": f"DDD {ddd} não reconhecido pela Anatel"}
        
    number = digits[2:]
    
    if len(number) == 9:
        if not number.startswith('9'):
            return {"status": "Celular Inválido", "detalhes": "Telefone com 9 dígitos deve começar com 9"}
        return {"status": "Válido", "detalhes": "Celular válido"}
    elif len(number) == 8:
        if not number[0] in '2345678':
            return {"status": "Fixo Inválido", "detalhes": "Telefone fixo deve começar com dígito de 2 a 8"}
        return {"status": "Válido", "detalhes": "Telefone fixo válido"}
        
    return {"status": "Formato incorreto", "detalhes": "Tamanho do número após DDD não esperado"}
