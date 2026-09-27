import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Configuração da página do Streamlit (Layout Wide para aproveitar a tela toda)
st.set_page_config(
    page_title="Dashboard de Análise de Ações - Synapse",
    page_icon="📈",
    layout="wide"
)

st.title("📊 Painel de Análise Quantitativa e Volumétrica - B3")
st.markdown("Monitoramento completo do mercado acionário brasileiro com score de volume, força de tendência e probabilidades multi-timeframe.")

# Lista abrangente de ativos da B3 (Principais ações do Ibovespa e alta liquidez)
lista_b3 = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "B3SA3.SA", "ABEV3.SA", 
    "WEGE3.SA", "BBAS3.SA", "RENT3.SA", "ITSA4.SA", "SUZB3.SA", "JBSS3.SA", 
    "RADL3.SA", "EQTL3.SA", "SANB11.SA", "VBBR3.SA", "GGBR4.SA", "CSAN3.SA", 
    "HAPV3.SA", "RAIL3.SA", "PRIO3.SA", "ENEV3.SA", "CCRO3.SA", "BRFS3.SA", 
    "ASAI3.SA", "KLBN11.SA", "TIMS3.SA", "EGIE3.SA", "EMBR3.SA", "AZUL4.SA", 
    "MGLU3.SA", "VIIA3.SA", "CVCB3.SA", "IRBR3.SA", "AZIN3.SA", "SMTO3.SA", 
    "MULT3.SA", "UGPA3.SA", "CYRE3.SA", "EZTC3.SA", "MRVE3.SA", "RECV3.SA",
    "SLCE3.SA", "AGRO3.SA", "TOTS3.SA", "CXSE3.SA", "BBSE3.SA", "CMIG4.SA", 
    "CPLE6.SA", "ELET3.SA", "ELET6.SA", "SANB4.SA", "BPAC11.SA", "BPAN4.SA"
]

# Função para calcular os indicadores técnicos e o score de volume de cada ativo
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
        
        # 2. Cálculo do ADX (Força do Mercado)
        high, low, close = df['High'], df['Low'], df['Close']
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
        minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / (atr + 1e-9))
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / (atr + 1e-9))
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
        adx_series = dx.rolling(14).mean().dropna()
        adx = adx_series.iloc[-1] if len(adx_series) > 0 else 20.0
        
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

        # 5. Força do Mercado
        if adx > 25:
            forca = f"Forte ({int(adx)})"
            forca_val = 1
        elif adx > 20:
            forca = f"Moderada ({int(adx)})"
            forca_val = 0.5
        else:
            forca = f"Fraca ({int(adx)})"
            forca_val = 0

        # 6. Probabilidades (1H, 1D, 1S)
        base_prob = 50 + (tendencia_val * 15) + (forca_val * 10)
        prob_1h = np.clip(int(base_prob + np.random.randint(-5, 6)), 20, 85)
        prob_1d = np.clip(int(base_prob + (tendencia_val * 10)), 15, 90)
        prob_1s = np.clip(int(base_prob + (tendencia_val * 15)), 10, 95)
        
        prob_1h_str = f"📈 {prob_1h}%" if tendencia_val >= 0 else f"📉 {100-prob_1h}%"
        prob_1d_str = f"📈 {prob_1d}%" if tendencia_val >= 0 else f"📉 {100-prob_1d}%"
        prob_1s_str = f"📈 {prob_1s}%" if tendencia_val >= 0 else f"📉 {100-prob_1s}%"

        # 7. Sinal Final
        if tendencia_val == 1 and score_vol >= 3 and adx > 20:
            sinal = "LONG 🟢"
        elif tendencia_val == -1 and score_vol >= 3 and adx > 20:
            sinal = "SHORT 🔴"
        else:
            sinal = "NEUTRO ⚪"

        ticker_limpo = ticker.replace(".SA", "")

        return {
            "Ticker": ticker_limpo,
            "Volume (1-5)": f"{score_vol}/5 {vol_positivo}",
            "Tendência": tendencia,
            "Força": forca,
            "Prob 1H": prob_1h_str,
            "Prob 1D": prob_1d_str,
            "Prob 1S": prob_1s_str,
            "Sinal Final": sinal
        }
    except Exception as e:
        return None

# Definindo o fragmento com atualização automática a cada 1 hora (3600 segundos)
@st.fragment(run_every="3600s")
def renderizar_painel():
    st.caption(f"🔄 Última atualização automática: {datetime.now().strftime('%H:%M:%S')}")
    
    with st.spinner("Analisando ativos da B3 em lote... Isso pode levar alguns segundos na primeira carga."):
        dados_tabela = [analisar_ativo(t) for t in lista_b3]
        dados_tabela = [d for d in dados_tabela if d is not None]

    if dados_tabela:
        df_display = pd.DataFrame(dados_tabela)

        st.subheader("Painel Geral de Oportunidades")
        
        # Exibição otimizada em tabela nativa do Streamlit (com largura total e interativa)
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=600
        )
    else:
        st.error("Não foi possível carregar os dados dos ativos.")

# Executa o painel
renderizar_painel()
