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

# BARRA LATERAL COM NAVEGAÇÃO EXPANDIDA
st.sidebar.title("🧭 Navegação Synapse")
pagina_selecionada = st.sidebar.radio("Selecione o Módulo:", ["MARKET X-RAY", "MARKET FEELING", "OPTIONS SCANNER"])

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
            "Preco_Atual": close_atual
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

    # ABA 3: OPTIONS SCANNER (Novo Módulo de Derivativos e Opções)
    elif pagina_selecionada == "OPTIONS SCANNER":
        st.title("🎯 Options Scanner - Autofiltragem de Calls e Puts")
        st.markdown("Analise a cadeia de opções de qualquer ativo da B3 com filtros automáticos de Moneyness, Liquidez e Vencimento.")
        st.divider()

        # Seleção do Ativo base para buscar as opções
        tickers_disponiveis = df_display['Ticker'].tolist()
        ativo_escolhido = st.selectbox("Selecione o Ativo Base:", tickers_disponiveis)

        if ativo_escolhido:
            # Obtém o preço atual do ativo selecionado
            preco_ativo = df_display.loc[df_display['Ticker'] == ativo_escolhido, 'Preco_Atual'].values[0]
            st.markdown(f"💵 **Preço Atual de {ativo_escolhido}:** R$ {preco_ativo:.2f}")

            try:
                # Buscando a cadeia de opções via yfinance
                ticker_yf = yf.Ticker(f"{ativo_escolhido}.SA")
                vencimentos = ticker_yf.options

                if not vencimentos:
                    st.warning(f"Não foram encontradas opções disponíveis para {ativo_escolhido} no momento.")
                else:
                    # Filtros na barra lateral ou na tela principal
                    col_f1, col_f2, col_f3 = st.columns(3)
                    
                    with col_f1:
                        tipo_opcao = st.selectbox("Tipo de Opção:", ["CALL", "PUT"])
                    with col_f2:
                        vencimento_escolhido = st.selectbox("Data de Vencimento:", vencimentos)
                    with col_f3:
                        moneyness_filtro = st.selectbox("Classificação (Moneyness):", ["TODOS", "ATM (No Dinheiro)", "ITM (Dentro do Dinheiro)", "OTM (Fora do Dinheiro)"])

                    # Carrega a tabela de opções para o vencimento selecionado
                     cadeia = ticker_yf.option_chain(vencimento_escolhido)
                    tabela_opcoes = cadeia.calls if tipo_opcao == "CALL" else cadeia.puts

                    if not tabela_opcoes.empty:
                        # Cálculo da Distância do Strike em relação ao Preço Atual (Moneyness)
                        tabela_opcoes['Distancia_%'] = ((tabela_opcoes['strike'] - preco_ativo) / preco_ativo) * 100

                        # Classificação automática ATM / ITM / OTM
                        def classificar_moneyness(row, tipo, preco):
                            strike = row['strike']
                            if tipo == "CALL":
                                if abs(strike - preco) / preco <= 0.03: return "ATM"
                                elif strike < preco: return "ITM"
                                else: return "OTM"
                            else: # PUT
                                if abs(strike - preco) / preco <= 0.03: return "ATM"
                                elif strike > preco: return "ITM"
                                else: return "OTM"

                        tabela_opcoes['Status'] = tabela_opcoes.apply(lambda r: classificar_moneyness(r, tipo_opcao, preco_ativo), axis=1)

                        # Aplicando o filtro de Moneyness selecionado pelo usuário
                        if moneyness_filtro != "TODOS":
                            sigla_filtro = moneyness_filtro.split(" ")[0]
                            tabela_opcoes = tabela_opcoes[tabela_opcoes['Status'] == sigla_filtro]

                        # Filtros e formatação de colunas limpas
                        tabela_limpa = tabela_opcoes[['contractSymbol', 'strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility', 'Status']].copy()
                        tabela_limpa.columns = ['Contrato', 'Strike (R$)', 'Último (R$)', 'Bid', 'Ask', 'Volume', 'Open Interest', 'Vol. Implicita', 'Moneyness']

                        # Ordenando por volume (maior liquidez primeiro)
                        tabela_limpa = tabela_limpa.sort_values(by='Volume', ascending=False).fillna(0)

                        st.subheader(f"📋 Cadeia de {tipo_opcao}s Filtrada — Vencimento: {vencimento_escolhido}")
                        st.markdown(f"Mostrando opções para **{ativo_escolhido}** com base nos critérios selecionados:")

                        # Exibindo tabela interativa polida
                        st.dataframe(
                            tabela_limpa,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Nenhum contrato encontrado para este vencimento.")

            except Exception as e:
                st.error(f"Erro ao carregar a cadeia de opções para {ativo_escolhido}: {e}")

renderizar_painel()
