
# Imports
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from PIL import Image
from io import BytesIO

# Função para converter df para CSV
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# Função para converter df para Excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

# Funções para classificar RFV
def recencia_class(x, r, q_dict):
    if x <= q_dict.loc[0.25, r]:
        return 'A'
    elif x <= q_dict.loc[0.50, r]:
        return 'B'
    elif x <= q_dict.loc[0.75, r]:
        return 'C'
    else:
        return 'D'

def freq_val_class(x, fv, q_dict):
    if x <= q_dict.loc[0.25, fv]:
        return 'D'
    elif x <= q_dict.loc[0.50, fv]:
        return 'C'
    elif x <= q_dict.loc[0.75, fv]:
        return 'B'
    else:
        return 'A'

# Função principal da aplicação
def main():
    st.set_page_config(page_title='RFV', layout="wide", initial_sidebar_state='expanded')

    st.title("RFV")
    st.markdown("""
    RFV significa **Recência, Frequência, Valor** e é utilizado para segmentar clientes com base em seus comportamentos de compra.
    
    - **Recência (R):** Dias desde a última compra  
    - **Frequência (F):** Total de compras no período  
    - **Valor (V):** Total gasto no período
    
    Essa técnica ajuda a personalizar ações de marketing e melhorar retenção de clientes.
    """)
    st.markdown("---")

    # Upload de arquivo
    st.sidebar.title("Upload de dados")
    data_file_1 = st.sidebar.file_uploader("Arquivo de compras (.csv ou .xlsx)", type=['csv', 'xlsx'])

    if data_file_1 is not None:
        # Lê o arquivo conforme a extensão
        if data_file_1.name.endswith('.csv'):
            df_compras = pd.read_csv(data_file_1, parse_dates=['DiaCompra'])
        else:
            df_compras = pd.read_excel(data_file_1, parse_dates=['DiaCompra'])

        # Recência
        st.header('Recência (R)')
        dia_atual = df_compras['DiaCompra'].max()
        st.write('Última data da base:', dia_atual)

        df_recencia = df_compras.groupby('ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        df_recencia.drop('DiaUltimaCompra', axis=1, inplace=True)
        st.write(df_recencia.head())

        # Frequência
        st.header('Frequência (F)')
        df_frequencia = df_compras.groupby('ID_cliente')['CodigoCompra'].count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.write(df_frequencia.head())

        # Valor
        st.header('Valor (V)')
        df_valor = df_compras.groupby('ID_cliente')['ValorTotal'].sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        st.write(df_valor.head())

        # Tabela RFV
        st.header('Tabela RFV Final')
        df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        df_RFV = df_RF.merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        st.write(df_RFV.head())

        # Segmentação
        st.header('Segmentação por Quartis (A, B, C, D)')
        quartis = df_RFV.quantile(q=[0.25, 0.5, 0.75])
        st.write(quartis)

        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class, args=('Recencia', quartis))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class, args=('Frequencia', quartis))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class, args=('Valor', quartis))
        df_RFV['RFV_Score'] = df_RFV['R_quartil'] + df_RFV['F_quartil'] + df_RFV['V_quartil']
        st.write(df_RFV.head())

        # Contagem de grupos
        st.subheader('Clientes por Grupo RFV')
        st.write(df_RFV['RFV_Score'].value_counts())

        # Clientes Top
        st.subheader('Top Clientes (AAA)')
        st.write(df_RFV[df_RFV['RFV_Score'] == 'AAA'].sort_values('Valor', ascending=False).head(10))

        # Ações sugeridas
        st.header('Sugestões de Ações de Marketing/CRM')
        dict_acoes = {
            'AAA': 'Enviar cupons, pedir indicação, enviar amostras grátis.',
            'DDD': 'Churn provável — poucas compras e pouco gasto.',
            'DAA': 'Tentar recuperar com cupons de desconto.',
            'CAA': 'Enviar cupons para reativação.'
        }
        df_RFV['acoes de marketing/crm'] = df_RFV['RFV_Score'].map(dict_acoes)
        st.write(df_RFV.head())

        # Download da base RFV
        df_xlsx = to_excel(df_RFV)
        st.download_button(
            label="📥 Baixar Excel com RFV",
            data=df_xlsx,
            file_name="RFV_Result.xlsx"
        )

        st.subheader('Distribuição por Tipo de Ação')
        st.write(df_RFV['acoes de marketing/crm'].value_counts(dropna=False))

if __name__ == '__main__':
    main()









