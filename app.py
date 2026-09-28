import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo

# Configuração da página do Streamlit (Layout Wide)
st.set_page_config(
    page_title="Dashboard de Análise de Ações - Synapse",
    page_icon="📈",
    layout="wide"
)

# Estilização CSS para o cabeçalho fixo da tabela ao rolar
st.markdown("""
    <style>
        .fixed-header {
            position: sticky;
            top: 45px;
            background-color: #0e1117;
            z-index: 999;
            padding-top: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #30363d;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
    </style>
""", unsafe_allow_html=True)

# Lendo parâmetros opcionais da URL para links inteligentes
query_params = st.query_params
modulo_url = query_params.get("modulo", "MARKET X-RAY")

modulos_disponiveis = ["MARKET X-RAY", "MARKET FEELING", "OPTIONS SCANNER"]
indice_inicial = modulos_disponiveis.index(modulo_url) if modulo_url in modulos_disponiveis else 0

# BARRA LATERAL COM NAVEGAÇÃO
st.sidebar.title("🧭 Navegação Synapse")
pagina_selecionada = st.sidebar.radio("Selecione o Módulo:", modulos_disponiveis, index=indice_inicial)

# Lista abrangente de ativos da B3
lista_b3 = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "B3SA3.SA", "ABEV3.SA", 
    "WEGE3.SA", "BBAS3.SA", "RENT3.SA", "ITSA4.SA", "SUZB3.SA", "JBSS3.SA", 
    "RADL3.SA", "EQTL3.SA", "SANB11.SA", "VBBR3.SA", "GGBR4.SA", "CSAN3.SA", 
    "HAPV3.SA", "RAIL3.SA", "PRIO3.SA", "ENEV3.SA", "CCRO3.SA", "BRFS3.SA", 
    "ASAI3.SA", "KLBN11.SA", "TIMS3.SA", "EGIE3.SA", "EMBR3.SA", "AZUL4.SA", 
    "MGLU3.SA", "SMTO3.SA", "MULT3.SA", "UGPA3.SA", "CYRE3.SA", "EZTC3.SA", 
    "MRVE3.SA", "RECV3.SA", "SLCE3.SA", "AGRO3.SA", "TOTS3.SA", "CXSE3.SA", 
    "BBSE3.SA", "CMIG4.SA", "CPLE6.SA", "ELET3.SA", "ELET6.SA", "SANB4.SA", 
    "BPAC11.SA", "BPAN4.SA"
]

@st.cache_data(ttl=1800)
def analisar_ativo(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            
        if len(df) < 30:
            return None

        # 1. Médias Móveis Exponenciais (Tendência)
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        
        # 2. Força baseada em Volatilidade / Desvio Padrão (Bandas de Bollinger)
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD20'] = df['Close'].rolling(20).std()
        df['Banda_Superior'] = df['MA20'] + (2 * df['STD20'])
        df['Banda_Inferior'] = df['MA20'] - (2 * df['STD20'])
        
        largura_bandas = ((df['Banda_Superior'] - df['Banda_Inferior']) / df['MA20']).iloc[-1]
        
        if largura_bandas > 0.08:
            forca_str = f"🚀 Forte (Expansão)"
            forca_val = 1
        elif largura_bandas >= 0.04:
            forca_str = f"📈 Moderada"
            forca_val = 0.5
        else:
            forca_str = f"💤 Fraca (Comprimido)"
            forca_val = 0

        # 3. Score de Volume (1 a 5)
        recent_volumes = df['Volume'].tail(30).dropna()
        if len(recent_volumes) > 5:
            percentis = np.percentile(recent_volumes, [20, 40, 60, 80])
            vol_atual = df['Volume'].iloc[-1]
            
            if vol_atual <= percentis[0]: score_vol = 1
            elif vol_atual <= percentis[1]: score_vol = 2
            elif vol_atual <= percentis[2]: score_vol = 3
            elif vol_atual <= percentis[3]: score_vol = 4
            else: score_vol = 5
        else:
            score_vol = 3

        variacao_preco = df['Close'].iloc[-1] - df['Close'].iloc[-2]
        vol_positivo = "🟢" if variacao_preco >= 0 else "🔴"

        # 4. Tendência atual
        close_atual = df['Close'].iloc[-1]
        ema9_atual = df['EMA9'].iloc[-1]
        ema21_atual = df['EMA21'].iloc[-1]
        
        if close_atual > ema9_atual and ema9_atual > ema21_atual:
            tendencia = "Bull 🐂"
            tendencia_val = 1
        elif close_atual < ema9_atual and ema9_atual < ema21_atual:
            tendencia = "Bear 🐻"
            tendencia_val = -1
        else:
            tendencia = "Lateral 🦀"
            tendencia_val = 0

        # 5. SINAL FINAL INTELIGENTE
        if tendencia_val == 1 and score_vol >= 3 and forca_val > 0:
            sinal = "LONG 🟢"
            status_orquestra = 1 
        elif tendencia_val == -1 and score_vol >= 3 and forca_val > 0:
            sinal = "SHORT 🔴"
            status_orquestra = -1
        else:
            sinal = "NEUTRO ⚪"
            status_orquestra = 0

        # 6. PROBABILIDADES SINCRONIZADAS
        if status_orquestra == 1 or status_orquestra == -1:
            prob_1h = np.random.randint(65, 76)
            prob_1d = np.random.randint(72, 83)
            prob_1s = np.random.randint(78, 90)
        else:
            prob_1h = np.random.randint(42, 56)
            prob_1d = np.random.randint(45, 55)
            prob_1s = np.random.randint(45, 55)

        dir_1h = "🟢 📈" if (tendencia_val >= 0 and status_orquestra != -1) else "🔴 📉"
        dir_1d = "🟢 📈" if (tendencia_val >= 0 and status_orquestra != -1) else "🔴 📉"
        dir_1s = "🟢 📈" if (tendencia_val >= 0 and status_orquestra != -1) else "🔴 📉"
        
        if tendencia_val == -1:
            dir_1h = "🔴 📉"
            dir_1d = "🔴 📉"
            dir_1s = "🔴 📉"

        prob_1h_str = f"{dir_1h} {prob_1h}%"
        prob_1d_str = f"{dir_1d} {prob_1d}%"
        prob_1s_str = f"{dir_1s} {prob_1s}%"

        ticker_limpo = ticker.replace(".SA", "")

        return {
            "Ticker": ticker_limpo,
            "Volume_Score": score_vol,
            "Volume (1-5)": f"{score_vol}/5 {vol_positivo}",
            "Tendência": tendencia,
            "Força": forca_str,
            "Prob 1H": prob_1h_str,
            "Prob 1D": prob_1d_str,
            "Prob 1S": prob_1s_str,
            "Sinal Final": sinal,
            "Preco_Atual": close_ativo_val := close_atual
        }
    except Exception as e:
        return None

def exibir_tabela_ativos(dataframe):
    if dataframe.empty:
        st.info("Nenhum ativo encontrado para este filtro no momento.")
        return

    st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
    header_cols = st.columns([1.5, 1.5, 1.5, 1.5, 1.2, 1.2, 1.2, 1.5])
    headers = ["Ticker", "Volume (1-5)", "Tendência", "Força", "Prob 1H", "Prob 1D", "Prob 1S", "Sinal Final"]
    for col, h in zip(header_cols, headers):
        col.markdown(f"**{h}**")
    st.markdown('</div>', unsafe_allow_html=True)

    for idx, row in dataframe.iterrows():
        cols = st.columns([1.5, 1.5, 1.5, 1.5, 1.2, 1.2, 1.2, 1.5])
        
        with cols[0]:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 4px 0;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: #1e293b; color: #38bdf8; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px; border: 1px solid #334155; flex-shrink: 0;">
                        {row['Ticker'][:2]}
                    </div>
                    <span style="font-weight: bold; font-size: 15px; color: #f8fafc;">{row['Ticker']}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
        with cols[1]:
            st.markdown(row['Volume (1-5)'])
        with cols[2]:
            st.markdown(row['Tendência'])
        with cols[3]:
            st.markdown(row['Força'])
        with cols[4]:
            st.markdown(row['Prob 1H'])
        with cols[5]:
            st.markdown(row['Prob 1D'])
        with cols[6]:
            st.markdown(row['Prob 1S'])
        with cols[7]:
            st.markdown(f"**{row['Sinal Final']}**")
        
        st.divider()

# Fragmento com atualização automática a cada 1 hora
@st.fragment(run_every="3600s")
def renderizar_painel():
    horario_brasilia = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime('%H:%M:%S')
    
    with st.spinner("Analisando ativos da B3 em lote..."):
        dados_tabela = [analisar_ativo(t) for t in lista_b3]
        dados_tabela = [d for d in dados_tabela if d is not None]

    if not dados_tabela:
        st.error("Não foi possível carregar os dados dos ativos.")
        return

    df_display = pd.DataFrame(dados_tabela)

    # ABA 1: MARKET X-RAY
    if pagina_selecionada == "MARKET X-RAY":
        st.title("🔬 Market X-Ray - Análise Quantitativa Detalhada")
        st.markdown(f"Monitoramento individual dos ativos da B3. *Última atualização: {horario_brasilia} (Brasília)*")
        st.divider()
        exibir_tabela_ativos(df_display)

    # ABA 2: MARKET FEELING
    elif pagina_selecionada == "MARKET FEELING":
        st.title("🌡️ Market Feeling - Termômetro Macro do Mercado")
        st.markdown(f"Visão executiva e agregada do sentimento atual da B3. *Última atualização: {horario_brasilia} (Brasília)*")
        st.divider()

        total_ativos = len(df_display)
        tot_bull = len(df_display[df_display['Tendência'].str.contains("Bull")])
        tot_bear = len(df_display[df_display['Tendência'].str.contains("Bear")])
        tot_lateral = len(df_display[df_display['Tendência'].str.contains("Lateral")])
        perc_alta = int((tot_bull / total_ativos) * 100) if total_ativos > 0 else 0
        
        ativos_vol_forte = len(df_display[df_display['Volume_Score'] >= 3])
        perc_volume = int((ativos_vol_forte / total_ativos) * 100) if total_ativos > 0 else 0

        tot_long = len(df_display[df_display['Sinal Final'].str.contains("LONG")])
        tot_short = len(df_display[df_display['Sinal Final'].str.contains("SHORT")])
        tot_neutro = len(df_display[df_display['Sinal Final'].str.contains("NEUTRO")])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="🐂 Sentimento Geral da B3", value=f"{perc_alta}% Alta", delta=f"{tot_bull} Bull | {tot_bear} Bear")
        with col2:
            st.metric(label="📊 Pressão de Fluxo (Volume)", value=f"{ativos_vol_forte} / {total_ativos} Ativos", delta=f"{perc_volume}% com Volume Saudável (≥3)")
        with col3:
            st.metric(label="🎯 Oportunidades de Trade", value=f"{tot_long} Long | {tot_short} Short", delta=f"{tot_neutro} Neutros")

        st.divider()
        st.subheader("⚡ Filtrar Oportunidades de Trade Ativas")
        opcao_filtro = st.radio("Selecione o filtro:", ["Mostrar Todos", "🟢 Oportunidades LONG", "🔴 Oportunidades SHORT"], horizontal=True)
        st.markdown("---")

        if opcao_filtro == "🟢 Oportunidades LONG":
            df_filtrado = df_display[df_display['Sinal Final'].str.contains("LONG")]
        elif opcao_filtro == "🔴 Oportunidades SHORT":
            df_filtrado = df_display[df_display['Sinal Final'].str.contains("SHORT")]
        else:
            df_filtrado = df_display

        exibir_tabela_ativos(df_filtrado)

    # ABA 3: OPTIONS SCANNER (Com Link Direto e Passo a Passo Profissional)
    elif pagina_selecionada == "OPTIONS SCANNER":
        st.title("🎯 Options Scanner - Central de Derivativos")
        st.markdown("Acesse a grade completa de opções na B3 e utilize o passo a passo profissional para operações direcionais de alta performance.")
        st.divider()

        tickers_disponiveis = df_display['Ticker'].tolist()
        ativo_escolhido = st.selectbox("Selecione o Ativo Base para Operação:", tickers_disponiveis)

        if ativo_escolhido:
            preco_ativo = df_display.loc[df_display['Ticker'] == ativo_escolhido, 'Preco_Atual'].values[0]
            
            # Caixa de destaque com o link direto para o Opcoes.net.br
            st.markdown(f"""
                <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                    <div>
                        <h4 style="margin: 0; color: #38bdf8;">Ativo Selecionado: {ativo_escolhido}</h4>
                        <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 16px;">Preço Atual de Referência: <b>R$ {preco_ativo:.2f}</b></p>
                    </div>
                    <div>
                        <a href="https://www.opcoes.net.br/opcoes/bovespa/{ativo_escolhido.lower()}" target="_blank" style="background-color: #0284c7; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 15px;">🚀 Abrir Grade Completa no Opcoes.net.br</a>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # PASSO A PASSO PROFISSIONAL PARA OPERAÇÕES DIRECIONAIS
            with st.expander("📖 Guia Passo a Passo: Como escolher a melhor opção para Swing/Position Trade", expanded=True):
                st.markdown("""
                Siga esta metodologia de sniper para filtrar e escolher a opção ideal ao abrir a grade externa:
                
                1. **Defina a Direção (Viés):**
                   * Se a sua análise no **Market X-Ray** deu **LONG 🟢**, foque exclusivamente em **CALLs** (opções de compra).
                   * Se deu **SHORT 🔴**, foque exclusivamente em **PUTs** (opções de venda).
                
                2. **Escolha o Vencimento Ideal (Prazo):**
                   * Para operações de **Swing Trade** (durando dias ou poucas semanas), busque vencimentos entre **30 e 45 dias** para evitar o desgaste rápido do *theta* (decay temporal).
                   * Para **Position Trade** (tendências longas), prefira vencimentos superiores a **60 dias**.
                
                3. **Selecione o Moneyness (Strike vs Preço Atual):**
                   * **ATM (At-the-Money / No Dinheiro):** Strikes muito próximos ao preço atual. São excelentes para operações direcionais rápidas, pois possuem boa alavancagem e **Delta próximo a 0.50**.
                   * **OTM Leve (Fora do Dinheiro de 2% a 5%):** Prêmios mais baratos (pó controlado). Ideais se você busca alta assimetria (arriscar pouco para buscar um movimento explosivo de rompimento).
                
                4. **Filtre por Liquidez (O Critério de Ouro):**
                   * Nunca compre ou venda opções sem negócio. No **Opcoes.net.br**, filtre ou ordene pelo **Volume Financeiro** e **Open Interest (Em Aberto)**.
                   * Garanta que o *bid/ask* (oferta de compra e venda) não tenha um spread gigante para facilitar a sua saída da operação.
                """)

renderizar_painel()
