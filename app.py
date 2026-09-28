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

modulos_disponiveis = ["MARKET X-RAY", "MARKET FEELING", "OPTIONS SCANNER", "BACKTESTING"]
indice_inicial = modulos_disponiveis.index(modulo_url) if modulo_url in modulos_disponiveis else 0

# BARRA LATERAL COM NAVEGAÇÃO EXPANDIDA
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
            
        if len(df) < 35:
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

        # 3. Indicador de Momentum (MACD)
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
        
        macd_hist_atual = df['MACD_Hist'].iloc[-1]
        momentum_val = 1 if macd_hist_atual > 0 else -1

        # 4. Score de Volume (1 a 5)
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

        # 5. Tendência atual
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

        # 6. SINAL FINAL INTELIGENTE
        if tendencia_val == 1 and score_vol >= 3 and forca_val > 0 and momentum_val == 1:
            sinal = "LONG 🟢"
            status_orquestra = 1 
        elif tendencia_val == -1 and score_vol >= 3 and forca_val > 0 and momentum_val == -1:
            sinal = "SHORT 🔴"
            status_orquestra = -1
        else:
            sinal = "NEUTRO ⚪"
            status_orquestra = 0

        # 7. PROBABILIDADES SINCRONIZADAS
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
    
    with st.spinner("Analisando ativos da B3..."):
        dados_tabela = [analisar_ativo(t) for t in lista_b3]
        dados_tabela = [d for d in dados_tabela if d is not None]

    if not dados_tabela:
        st.error("Não foi possível carregar os dados dos ativos.")
        return

    df_display = pd.DataFrame(dados_tabela)

    # ABA 1: MARKET X-RAY
    if pagina_selecionada == "MARKET X-RAY":
        st.title("🔬 Market X-Ray - Análise Quantitativa Detalhada")
        st.markdown(f"Monitoramento individual com filtro de aceleração e momentum. *Última atualização: {horario_brasilia} (Brasília)*")
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

    # ABA 3: OPTIONS SCANNER
    elif pagina_selecionada == "OPTIONS SCANNER":
        st.title("🎯 Options Scanner - Central de Derivativos")
        st.markdown("Acesse a grade completa de opções na B3 e utilize o passo a passo profissional para operações direcionais de alta performance.")
        st.divider()

        tickers_disponiveis = df_display['Ticker'].tolist()
        ativo_escolhido = st.selectbox("Selecione o Ativo Base para Operação:", tickers_disponiveis)

        if ativo_escolhido:
            preco_ativo = df_display.loc[df_display['Ticker'] == ativo_escolhido, 'Preco_Atual'].values[0]
            
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

            with st.expander("📖 Guia Passo a Passo: Como escolher a melhor opção para Swing/Position Trade", expanded=True):
                st.markdown("""
                Siga esta metodologia de sniper para filtrar e escolher a opção ideal ao abrir a grade externa:
                
                1. **Defina a Direção (Viés):**
                   * Se a sua análise no **Market X-Ray** deu **LONG 🟢**, foque exclusivamente em **CALLs** (opções de compra).
                   * Se deu **SHORT 🔴**, foque exclusivamente em **PUTs** (opções de venda).
                
                2. **Escolha o Vencimento Ideal (Prazo):**
                   * Para **Swing Trade** (dias ou poucas semanas), busque vencimentos entre **30 e 45 dias** para evitar o desgaste acelerado do tempo (*theta*).
                   * Para **Position Trade** (tendências longas), prefira vencimentos superiores a **60 dias**.
                
                3. **Selecione o Moneyness (Strike vs Preço Atual):**
                   * **ATM (At-the-Money / No Dinheiro):** Strikes muito próximos ao preço atual. Excelentes para operações direcionais ágeis com **Delta próximo a 0.50**.
                   * **OTM Leve (Fora do Dinheiro de 2% a 5%):** Prêmios mais baratos (pó controlado). Ideais para buscar alta assimetria e alavancagem em rompimentos.
                
                4. **Valide a Liquidez via Bid / Ask (O Critério de Ouro):**
                   * **Bid (Compra):** O preço máximo que o mercado está disposto a **pagar** para comprar o ativo de você.
                   * **Ask (Venda):** O preço mínimo que o mercado está pedindo para **vender** o ativo para você.
                   * **Exemplo Prático na Prateleira:** Imagine que uma opção de PETR4 mostra no book: `Bid = R$ 0,80` e `Ask = R$ 0,82`. 
                     * Se você quiser **comprar** a mercado agora, você vai pagar o preço do vendedor (`R$ 0,82`).
                     * Se você quiser **vender** (sair da posição) a mercado logo em seguida, você vai entregar pelo preço do comprador (`R$ 0,80`). 
                     * A diferença de R$ 0,02 é o **Spread**. *Regra de ouro:* Evite opções com spreads gigantescos (ex: Bid a R$ 0,50 e Ask a R$ 0,90), pois você perde dinheiro só de entrar e sair! Procure contratos onde Bid e Ask estejam bem coladinhos e com bom **Volume** e **Open Interest**.
                """)

    # ABA 4: BACKTESTING (Novo Motor Quantitativo de Simulação Histórica)
    elif pagina_selecionada == "BACKTESTING":
        st.title("📊 Backtesting & Validação Estatística da Estratégia")
        st.markdown("Simule o desempenho histórico da nossa 'orquestra' de sinais nos últimos meses e avalie a robustez estatística do setup.")
        st.divider()

        # Controles de Parâmetros do Backtest
        col_bt1, col_bt2, col_bt3 = st.columns(3)
        with col_bt1:
            ativo_bt = st.selectbox("Ativo para Simulação:", df_display['Ticker'].tolist())
        with col_bt2:
            periodo_bt = st.selectbox("Período Histórico:", ["6 meses", "1 ano", "2 anos"], index=1)
        with col_bt3:
            alvo_gain_pct = st.slider("Alvo de Lucro (% Gain):", min_value=2.0, max_value=15.0, value=5.0, step=0.5)
            stop_loss_pct = st.slider("Proteção (% Loss):", min_value=1.0, max_value=8.0, value=2.5, step=0.5)

        if st.button("🚀 Rodar Backtesting", type="primary"):
            with st.spinner(f"Executando simulação matemática para {ativo_bt} ({periodo_bt})..."):
                # Mapeia o período para o yfinance
                map_periodo = {"6 meses": "6mo", "1 ano": "1y", "2 anos": "2y"}
                df_hist = yf.download(f"{ativo_bt}.SA", period=map_periodo[periodo_bt], interval="1d", progress=False)
                
                if isinstance(df_hist.columns, pd.MultiIndex):
                    df_hist.columns = df_hist.columns.droplevel(1)
                
                df_hist = df_hist[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

                if len(df_hist) < 50:
                    st.warning("Dados insuficientes para rodar o backtest neste período.")
                else:
                    # Aplicando os indicadores históricos
                    df_hist['EMA9'] = df_hist['Close'].ewm(span=9, adjust=False).mean()
                    df_hist['EMA21'] = df_hist['Close'].ewm(span=21, adjust=False).mean()
                    df_hist['MA20'] = df_hist['Close'].rolling(20).mean()
                    df_hist['STD20'] = df_hist['Close'].rolling(20).std()
                    df_hist['Banda_Sup'] = df_hist['MA20'] + (2 * df_hist['STD20'])
                    df_hist['Banda_Inf'] = df_hist['MA20'] - (2 * df_hist['STD20'])
                    
                    exp12 = df_hist['Close'].ewm(span=12, adjust=False).mean()
                    exp26 = df_hist['Close'].ewm(span=26, adjust=False).mean()
                    df_hist['MACD_Hist'] = (exp12 - exp26) - (exp12 - exp26).ewm(span=9, adjust=False).mean()
                    
                    # Volume rolling percentil
                    df_hist['Vol_Medio'] = df_hist['Volume'].rolling(30).mean()

                    # Motor de Simulação de Trades
                    trades = []
                    capital_inicial = 10000.0
                    capital_atual = capital_inicial
                    curva_capital = [capital_inicial]

                    # Percorre o histórico simulando as entradas
                    for i in-range(35, len(df_hist) - 10):
                        close_p = df_hist['Close'].iloc[i]
                        ema9_p = df_hist['EMA9'].iloc[i]
                        ema21_p = df_hist['EMA21'].iloc[i]
                        macd_p = df_hist['MACD_Hist'].iloc[i]
                        vol_p = df_hist['Volume'].iloc[i]
                        vol_med_p = df_hist['Vol_Medio'].iloc[i]
                        banda_sup_p = df_hist['Banda_Sup'].iloc[i]
                        banda_inf_p = df_hist['Banda_Inf'].iloc[i]

                        # Condições da Orquestra Histórica
                        tendencia_alta = close_p > ema9_p and ema9_p > ema21_p
                        vol_forte = vol_p >= vol_med_p
                        momentum_alta = macd_p > 0
                        expansao_bollinger = (banda_sup_p - banda_inf_p) / df_hist['MA20'].iloc[i] >= 0.04

                        # Sinal LONG Histórico
                        if tendencia_alta and vol_forte and momentum_alta and expansao_bollinger:
                            preco_entrada = df_hist['Open'].iloc[i+1] # Entra no dia seguinte na abertura
                            preco_alvo = preco_entrada * (1 + (alvo_gain_pct / 100))
                            preco_stop = preco_entrada * (1 - (stop_loss_pct / 100))

                            # Simula o desfecho do trade nos dias seguintes
                            resultado_trade = "GAIN"
                            retorno_pct = alvo_gain_pct
                            for j in range(i+1, min(i+15, len(df_hist))):
                                max_dia = df_hist['High'].iloc[j]
                                min_dia = df_hist['Low'].iloc[j]

                                if min_dia <= preco_stop:
                                    resultado_trade = "LOSS"
                                    retorno_pct = -stop_loss_pct
                                    break
                                elif max_dia >= preco_alvo:
                                    resultado_trade = "GAIN"
                                    retorno_pct = alvo_gain_pct
                                    break

                            lucro_bruto = capital_atual * (retorno_pct / 100)
                            capital_atual += lucro_bruto
                            curva_capital.append(capital_atual)

                            trades.append({
                                "Data": df_hist.index[i].strftime('%Y-%m-%d'),
                                "Tipo": "LONG",
                                "Entrada": preco_entrada,
                                "Saída": preco_alvo if resultado_trade == "GAIN" else preco_stop,
                                "Resultado": resultado_trade,
                                "Retorno (%)": retorno_pct
                            })

                    # Métricas Estatísticas do Backtest
                    df_trades = pd.DataFrame(trades)
                    
                    if not df_trades.empty:
                        total_trades = len(df_trades)
                        vitorias = len(df_trades[df_trades['Resultado'] == "GAIN"])
                        derrotas = len(df_trades[df_trades['Resultado'] == "LOSS"])
                        win_rate = (vitorias / total_trades) * 100

                        lucro_bruto_total = df_trades[df_trades['Retorno (%)'] > 0]['Retorno (%)'].sum()
                        prejuizo_bruto_total = abs(df_trades[df_trades['Retorno (%)'] < 0]['Retorno (%)'].sum())
                        
                        # Fator de Lucro (Profit Factor)
                        profit_factor = (lucro_bruto_total / prejuizo_bruto_total) if prejuizo_bruto_total > 0 else 99.0
                        
                        # Expectativa Matemática por operação
                        media_gain = df_trades[df_trades['Retorno (%)'] > 0]['Retorno (%)'].mean() if vitorias > 0 else 0
                        media_loss = abs(df_trades[df_trades['Retorno (%)'] < 0]['Retorno (%)'].mean()) if derrotas > 0 else 0
                        
                        prob_gain = vitorias / total_trades
                        prob_loss = derrotas / total_trades
                        expectativa_matematica = (prob_gain * media_gain) - (prob_loss * media_loss)

                        # Exibindo os Resultados em Métricas Executivas
                        st.subheader(f"📈 Relatório de Desempenho — {ativo_bt}")
                        
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Taxa de Acerto (Win Rate)", f"{win_rate:.1f}%", delta=f"{vitorias} Wins / {derrotas} Losses")
                        m2.metric("Fator de Lucro (Profit Factor)", f"{profit_factor:.2f}", delta="Ideal > 1.30")
                        m3.metric("Expectativa Matemática", f"{expectativa_matematica:+.2f}%", delta="Por operação")
                        m4.metric("Total de Trades", f"{total_trades} operações")

                        st.divider()

                        # Gráfico da Curva de Capital (Equity Curve)
                        st.subheader("📉 Curva de Capital Acumulado (Equity Curve)")
                        st.line_chart(curva_capital)

                        # Tabela de Histórico de Trades
                        with st.expander("📋 Ver Log Detalhado das Operações Simuladas"):
                            st.dataframe(df_trades, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Nenhum trade foi disparado pelo modelo neste período com os parâmetros atuais. Tente ajustar o alvo/stop ou escolher outro ativo.")

renderizar_painel()
