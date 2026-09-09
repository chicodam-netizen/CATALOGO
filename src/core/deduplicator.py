import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz

def find_duplicates(df: pd.DataFrame, columns: list, threshold: float = 95.0) -> dict:
    """
    Encontra duplicidades exatas e fuzzy no DataFrame baseado nas colunas fornecidas.
    Retorna um dicionário com df_duplicates e df_uniques.
    """
    if df.empty or not columns:
        return {'duplicates': pd.DataFrame(), 'uniques': df}
        
    # Copia o df e cria uma coluna concatenada para análise
    df_work = df.copy()
    
    # Lidar com NAs convertendo para string vazia
    concat_series = df_work[columns].astype(str).fillna('').agg(' '.join, axis=1)
    
    # 1. Duplicidades Exatas
    # Marca como duplicado todas as ocorrências de um valor idêntico
    exact_dups_mask = concat_series.duplicated(keep=False)
    
    # 2. Fuzzy Matching para os registros que NÃO são duplicidades exatas
    # (Para performance, calculamos similaridade apenas no que sobrou, 
    # ou para ser rigoroso, agrupamos tudo. Como o usuário pediu agrupamento, 
    # vamos vetorizar toda a string concatenada para identificar os grupos).
    
    # Vetorização TF-IDF (Ngrams de caracteres capturam erros de digitação)
    vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
    tfidf_matrix = vectorizer.fit_transform(concat_series)
    
    # Calcula a similaridade do cosseno (Matrix N x N)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    n = len(df_work)
    visited = set()
    duplicate_groups = []
    
    threshold_dec = threshold / 100.0
    
    for i in range(n):
        if i in visited:
            continue
            
        # Encontra índices onde a similaridade é maior que o threshold
        # Evita comparar consigo mesmo (j != i) mas inclui o próprio i no grupo depois
        similar_indices = np.where(cosine_sim[i] >= threshold_dec)[0]
        
        if len(similar_indices) > 1:
            # Encontrou um grupo de duplicados (ele mesmo + outros)
            group = []
            for j in similar_indices:
                visited.add(j)
                # Pega o score em relação ao elemento pivot (i)
                score = round(cosine_sim[i][j] * 100, 2)
                row_data = df_work.iloc[j].to_dict()
                row_data['_Grupo_ID'] = i + 1
                row_data['_Similaridade'] = score
                group.append(row_data)
                
            duplicate_groups.extend(group)
        else:
            # Único
            visited.add(i)
            
    # Registros que não entraram em nenhum duplicate_group são únicos
    duplicated_indices = [idx for idx, _ in enumerate(df_work.index) if any(idx == j for j in similar_indices for similar_indices in [np.where(cosine_sim[k] >= threshold_dec)[0] for k in range(n) if len(np.where(cosine_sim[k] >= threshold_dec)[0]) > 1])]
    
    # Uma forma mais eficiente de pegar os não visitados/únicos
    all_indices = set(range(n))
    dup_indices_flat = set()
    
    for i in range(n):
        sims = np.where(cosine_sim[i] >= threshold_dec)[0]
        if len(sims) > 1:
            dup_indices_flat.update(sims)
            
    unique_indices = list(all_indices - dup_indices_flat)
    
    df_duplicates = pd.DataFrame(duplicate_groups)
    if not df_duplicates.empty:
        # Reordenar colunas para Grupo e Similaridade ficarem na frente
        cols = ['_Grupo_ID', '_Similaridade'] + [c for c in df_duplicates.columns if c not in ['_Grupo_ID', '_Similaridade']]
        df_duplicates = df_duplicates[cols]
        
    df_uniques = df_work.iloc[unique_indices].copy()
    
    return {
        'duplicates': df_duplicates,
        'uniques': df_uniques
    }
