import string

def analyze_free_text(text: str, mean_length: float) -> dict:
    """
    Analisa um campo de texto livre buscando sujeira e anomalias.
    
    Parâmetros:
    text: O texto a ser analisado
    mean_length: O tamanho médio da coluna (para detectar spikes)
    """
    if not isinstance(text, str):
        return {"status": "Não-texto", "detalhes": "Valor não é string"}
        
    if not text:
        return {"status": "Vazio", "detalhes": "String vazia"}
        
    detalhes = []
    
    # Detecção de quebras de linha
    if '\\n' in text or '\\r' in text:
        detalhes.append("Contém quebras de linha")
        
    # Análise de caracteres (contar os não-imprimíveis / anômalos)
    # printable contém letras, dígitos, pontuação e whitespace(espaço, tab, \n, \r)
    # Vamos considerar estranho tudo que não for comum
    weird_chars = [c for c in text if c not in string.printable and not (192 <= ord(c) <= 255)] # permitindo latim comum
    if weird_chars:
        detalhes.append(f"Possui {len(weird_chars)} caracteres especiais/estranhos")
        
    # Detecção de spikes
    length = len(text)
    if mean_length > 0:
        if length > mean_length * 3:
            detalhes.append("Spike de tamanho (Muito longo)")
        elif length < mean_length * 0.3:
            detalhes.append("Spike de tamanho (Muito curto)")
            
    if detalhes:
        return {"status": "Contém anomalias", "detalhes": "; ".join(detalhes)}
        
    return {"status": "Limpo", "detalhes": "Texto aparentemente padrão"}
