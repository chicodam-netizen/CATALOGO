import re
import dns.resolver

def validate_email(email: str) -> dict:
    """
    Valida o formato e a existência do domínio (MX) do email.
    """
    if not isinstance(email, str) or not email:
        return {"status": "Formato incorreto", "detalhes": "Vazio ou tipo incorreto"}
        
    email = email.strip()
    
    # Regex estrito para email
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return {"status": "Formato incorreto", "detalhes": "Não corresponde ao regex"}
        
    domain = email.split('@')[1]
    
    # Validação DNS
    try:
        records = dns.resolver.resolve(domain, 'MX')
        if not records:
            return {"status": "Domínio inexistente/Inválido", "detalhes": "Nenhum registro MX encontrado"}
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return {"status": "Domínio inexistente/Inválido", "detalhes": "Falha ao resolver domínio MX"}
    except Exception as e:
        return {"status": "Erro de verificação", "detalhes": str(e)}
        
    return {"status": "Válido", "detalhes": "Email válido e domínio ativo"}
