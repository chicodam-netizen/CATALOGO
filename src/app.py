import streamlit as st
import pandas as pd
import traceback
import io
from src.core.db_manager import DBManager
from src.core.profiler import profile_column
from src.models.glossary import save_metadata, get_all_metadata
from src.core.deduplicator import find_duplicates

st.set_page_config(page_title="Data Catalog & Profiler", layout="wide")

st.title("🗂️ Catálogo de Metadados Ativo e Profiler")

# --- Sidebar para Conexão e Navegação ---
with st.sidebar:
    st.header("Modo de Análise")
    app_mode = st.radio("Selecione a tela:", ["Data Discovery & Profiling", "Análise de Duplicidades"])
    
    st.divider()
    
    st.header("Conexão ao Banco de Dados")
    conn_string = st.text_input(
        "String de Conexão (SQLAlchemy)", 
        value="sqlite:///metadata.db",
        help="Ex: mssql+pyodbc://FRANCISCO/FDLABS?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
    )
    
    if st.button("Conectar"):
        try:
            st.session_state['db'] = DBManager(conn_string)
            st.session_state['schemas'] = st.session_state['db'].get_schemas()
            st.success("Conectado com sucesso!")
        except Exception as e:
            st.error(f"Erro na conexão: {e}")

# --- Controles Superiores Universais ---
if 'db' in st.session_state:
    st.write("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_schema = st.selectbox("Selecione o Schema", st.session_state.get('schemas', ['default']))
        
    with col2:
        if selected_schema:
            try:
                tables = st.session_state['db'].get_tables(selected_schema)
                selected_table = st.selectbox("Selecione a Tabela", tables)
            except Exception as e:
                st.error(f"Erro ao listar tabelas: {e}")
                selected_table = None
        else:
            selected_table = None
            
    with col3:
        sample_size = st.number_input("Tamanho da Amostra (Linhas)", min_value=1, max_value=1000000, value=50000)

    # =========================================================================
    # TELA 1: DATA DISCOVERY & PROFILING
    # =========================================================================
    if app_mode == "Data Discovery & Profiling" and selected_table:
        st.subheader("📊 Profiling de Dados e Metadados")
        
        if st.button("Executar Data Discovery"):
            with st.spinner(f"Analisando dados da tabela {selected_table}..."):
                try:
                    df = st.session_state['db'].fetch_sample_data(selected_table, selected_schema, sample_size)
                    if df.empty:
                        st.warning("Tabela está vazia.")
                    else:
                        results = []
                        for col in df.columns:
                            stats = profile_column(col, df[col])
                            stats['column_name'] = col
                            stats['native_type'] = str(df[col].dtype)
                            results.append(stats)
                            
                        st.session_state['profiling_results'] = pd.DataFrame(results)
                        st.success("Análise concluída!")
                except Exception as e:
                    st.error(f"Erro ao processar: {str(e)}")
                    st.code(traceback.format_exc())

        if 'profiling_results' in st.session_state:
            df_results = st.session_state['profiling_results']
            
            st.subheader("Saúde dos Dados (Health %)")
            st.bar_chart(df_results.set_index('column_name')[['health_valid_pct', 'health_invalid_pct']])
            
            st.subheader("Glossário de Negócios")
            saved_meta = get_all_metadata(selected_schema, selected_table)
            
            for _, row in df_results.iterrows():
                col_name = row['column_name']
                with st.expander(f"Coluna: {col_name} ({row['native_type']}) - {row['health_valid_pct']}% Válido"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Análise Automática (Inferido: {row['inferred_type']})**")
                        st.write(f"- Nulos: {row['null_pct']}%")
                        st.write(f"- Únicos: {row['unique_pct']}%")
                        if pd.notna(row['mean']):
                            st.write(f"- Média: {row['mean']} | Mín: {row['min']} | Máx: {row['max']}")
                    
                    with c2:
                        st.write("**Tags Manuais (Business Glossary)**")
                        current_meta = saved_meta.get(col_name, {})
                        
                        b_name = st.text_input("Nome Amigável", value=current_meta.get('business_name', ''), key=f"bn_{col_name}")
                        desc = st.text_area("Descrição", value=current_meta.get('description', ''), key=f"desc_{col_name}")
                        domain = st.text_input("Domínio de Valores", value=current_meta.get('domain_values', ''), key=f"dom_{col_name}")
                        classif = st.selectbox("Classificação (LGPD)", ["Público", "Interno", "Confidencial", "Restrito"], 
                                               index=["Público", "Interno", "Confidencial", "Restrito"].index(current_meta.get('classification', 'Público')) if current_meta.get('classification') else 0,
                                               key=f"class_{col_name}")
                        is_mand = st.checkbox("Obrigatório?", value=current_meta.get('is_mandatory', False), key=f"mand_{col_name}")
                        is_uniq = st.checkbox("Único?", value=current_meta.get('is_unique', False), key=f"uniq_{col_name}")
                        
                        if st.button("Salvar Metadados", key=f"btn_{col_name}"):
                            save_metadata(selected_schema, selected_table, col_name, {
                                'business_name': b_name, 'description': desc,
                                'domain_values': domain, 'classification': classif,
                                'is_mandatory': is_mand, 'is_unique': is_uniq
                            })
                            st.success("Salvo!")

            st.subheader("Exportar Relatório Profiling")
            export_data = []
            saved_meta = get_all_metadata(selected_schema, selected_table)
            for _, row in df_results.iterrows():
                m = saved_meta.get(row['column_name'], {})
                merged = row.to_dict()
                merged.update(m)
                export_data.append(merged)
                
            export_df = pd.DataFrame(export_data)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                export_df.to_excel(writer, index=False)
            
            st.download_button("Download Excel Profiling", data=buffer.getvalue(), file_name=f"profiling_{selected_table}.xlsx", mime="application/vnd.ms-excel")

    # =========================================================================
    # TELA 2: ANÁLISE DE DUPLICIDADES
    # =========================================================================
    elif app_mode == "Análise de Duplicidades" and selected_table:
        st.subheader("👯 Análise de Duplicidades (Exatas e Aproximadas)")
        
        try:
            # Buscar apenas nomes de colunas usando LIMIT 1 para não puxar dados atoa
            df_cols = st.session_state['db'].fetch_sample_data(selected_table, selected_schema, 1)
            all_cols = df_cols.columns.tolist()
            
            col_sel, thresh_sel = st.columns(2)
            with col_sel:
                selected_cols = st.multiselect("Colunas chave para busca de duplicidades", all_cols, default=all_cols)
            with thresh_sel:
                similarity_threshold = st.slider("Probabilidade Mínima (% Similaridade)", min_value=50.0, max_value=100.0, value=95.0, step=0.5, help="100% = Duplicidade exata. Abaixo de 100 considera erros de digitação (Fuzzy Match).")
                
            if st.button("Buscar Duplicidades"):
                if not selected_cols:
                    st.warning("Selecione ao menos uma coluna.")
                else:
                    with st.spinner(f"Extraindo {sample_size} linhas e computando álgebra TF-IDF..."):
                        df_full = st.session_state['db'].fetch_sample_data(selected_table, selected_schema, sample_size)
                        
                        if df_full.empty:
                            st.warning("Tabela está vazia.")
                        else:
                            st.info(f"Analisando {len(df_full)} linhas...")
                            results = find_duplicates(df_full, selected_cols, similarity_threshold)
                            st.session_state['dup_results'] = results
                            st.success("Busca finalizada!")
                            
        except Exception as e:
            st.error(f"Erro ao inicializar duplicador: {str(e)}")
            st.code(traceback.format_exc())
            
        if 'dup_results' in st.session_state:
            res = st.session_state['dup_results']
            df_dup = res['duplicates']
            df_uni = res['uniques']
            
            c1, c2 = st.columns(2)
            c1.metric("Registros com Duplicidade (Total no Grupo)", len(df_dup))
            c2.metric("Registros Seguros (Únicos)", len(df_uni))
            
            if not df_dup.empty:
                st.write("### Prováveis Duplicados (Agrupados)")
                st.dataframe(df_dup)
            else:
                st.success("Nenhuma duplicidade encontrada com esse critério!")
                
            st.write("### Exportar Resultados")
            buffer_dup = io.BytesIO()
            with pd.ExcelWriter(buffer_dup, engine='openpyxl') as writer:
                if not df_dup.empty:
                    df_dup.to_excel(writer, sheet_name="Duplicados", index=False)
                df_uni.to_excel(writer, sheet_name="Registros Unicos", index=False)
                
            st.download_button(
                label="📥 Baixar Excel Completo (Duplicados + Únicos)",
                data=buffer_dup.getvalue(),
                file_name=f"duplicidades_{selected_table}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
