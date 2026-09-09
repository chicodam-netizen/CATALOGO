import pandas as pd
from typing import Dict, Any

from src.validators.docs_br import validate_cpf, validate_cnpj
from src.validators.email_val import validate_email
from src.validators.phone import validate_phone
from src.validators.text_clean import analyze_free_text

def infer_validation_type(col_name: str, sample_series: pd.Series) -> str:
    """Tenta inferir qual validador rodar baseado no nome da coluna ou conteúdo."""
    name_lower = col_name.lower()
    if 'cpf' in name_lower:
        return 'cpf'
    if 'cnpj' in name_lower:
        return 'cnpj'
    if 'email' in name_lower or 'e-mail' in name_lower:
        return 'email'
    if 'telefone' in name_lower or 'celular' in name_lower or 'phone' in name_lower:
        return 'phone'
    return 'text'

def profile_column(col_name: str, series: pd.Series) -> Dict[str, Any]:
    """Executa profiling estatístico e descoberta na coluna (Serie pandas)."""
    total_rows = len(series)
    null_count = series.isnull().sum()
    null_pct = (null_count / total_rows) * 100 if total_rows > 0 else 0
    
    unique_count = series.nunique(dropna=True)
    unique_pct = (unique_count / (total_rows - null_count)) * 100 if (total_rows - null_count) > 0 else 0
    
    stats = {
        'total_rows': total_rows,
        'null_pct': round(null_pct, 2),
        'unique_pct': round(unique_pct, 2),
    }
    
    if pd.api.types.is_numeric_dtype(series):
        stats['min'] = series.min()
        stats['max'] = series.max()
        stats['mean'] = round(series.mean(), 2)
        mode_val = series.mode()
        stats['mode'] = mode_val.iloc[0] if not mode_val.empty else None
    else:
        stats['min'] = None
        stats['max'] = None
        stats['mean'] = None
        mode_val = series.mode()
        stats['mode'] = mode_val.iloc[0] if not mode_val.empty else None
        
    # Validation Profile
    val_type = infer_validation_type(col_name, series)
    val_results = {"Válido": 0, "Inválido": 0, "Outros": 0}
    
    # Process valid values only
    valid_series = series.dropna().astype(str)
    
    mean_len = valid_series.str.len().mean() if not valid_series.empty else 0
    
    for val in valid_series:
        if val_type == 'cpf':
            res = validate_cpf(val)
        elif val_type == 'cnpj':
            res = validate_cnpj(val)
        elif val_type == 'email':
            res = validate_email(val)
        elif val_type == 'phone':
            res = validate_phone(val)
        else:
            res = analyze_free_text(val, mean_len)
            
        status = res.get('status', 'Outros')
        # Simplificando a contagem
        if "Válido" in status or "Limpo" in status:
            val_results["Válido"] += 1
        elif "Inválido" in status or "Contém anomalias" in status or "incorreto" in status:
            val_results["Inválido"] += 1
        else:
            val_results["Outros"] += 1
            
    total_validations = len(valid_series)
    if total_validations > 0:
        stats['health_valid_pct'] = round((val_results["Válido"] / total_validations) * 100, 2)
        stats['health_invalid_pct'] = round((val_results["Inválido"] / total_validations) * 100, 2)
    else:
        stats['health_valid_pct'] = 0.0
        stats['health_invalid_pct'] = 0.0
        
    stats['inferred_type'] = val_type
    
    return stats
