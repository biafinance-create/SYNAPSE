import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import ta
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# ==========================================
# 1. CONFIGURAÇÕES CENTRAIS
# ==========================================
SCORE_WEIGHTS = {
    "volume": 0.25,
    "momentum": 0.30,
    "trend": 0.45
}

TARGET_THRESHOLDS = {
    "1H": 0.003, # 0.3%
    "1D": 0.015, # 1.5%
    "1W": 0.040  # 4.0%
}

# ==========================================
# 2. CAMADA DE DADOS
# ==========================================
class YahooFinanceProvider:
    def __init__(self):
        self.tf_map = {"1H": "1h", "1D": "1d", "1W": "1wk"}
    
    def get_historical_data(self, ticker: str, timeframe: str, period: str = "1y") -> pd.DataFrame:
        yf_tf = self.tf_map.get(timeframe, "1d")
        if timeframe == "1H" and period not in ["1mo", "3mo", "6mo", "1y", "730d"]:
            period = "730d"
            
        data = yf.download(f"{ticker}.SA", period=period, interval=yf_tf, progress=False)
        if data.empty:
            return pd.DataFrame()
            
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        data.dropna(inplace=True)
        return data

# ==========================================
# 3. INDICADORES E SCORES
# ==========================================
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 200: return pd.DataFrame() # Precisa de 200 para a EMA_200
    
    # Tendência (usando a biblioteca 'ta')
    df['EMA_9'] = ta.trend.ema_indicator(df['Close'], window=9)
    df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    
    # Momentum
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    macd = ta.trend.MACD(df['Close'])
    df['MACDh'] = macd.macd_diff()
    
    # Volume
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
    df['RVOL'] = df['Volume'] / df['Volume_SMA']
    
    df.dropna(inplace=True)
    return df

def generate_scores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    
    # Trend Score
    bullish_align = (df['EMA_9'] > df['EMA_20']) & (df['EMA_20'] > df['EMA_50'])
    bearish_align = (df['EMA_9'] < df['EMA_20']) & (df['EMA_20'] < df['EMA_50'])
    adx_norm = np.clip(df['ADX'] / 50.0 * 100.0, 0, 100)
    
    df['Trend_Score'] = 50.0
    df.loc[bullish_align, 'Trend_Score'] = 50.0 + (adx_norm / 2.0)
    df.loc[bearish_align, 'Trend_Score'] = 50.0 - (adx_norm / 2.0)
    
    # Momentum Score
    rsi_component = df['RSI_14']
    macd_component = np.where(df['MACDh'] > 0, 10.0, -10.0) 
    df['Momentum_Score'] = np.clip(rsi_component + macd_component, 0, 100).astype(float)
    
    # Volume Score
    obv_roc = df['OBV'].pct_change(3).fillna(0)
    obv_signal = np.where(obv_roc > 0, 1.0, -1.0)
    rvol_capped = np.clip(df['RVOL'], 0, 3.0)
    df['Volume_Score'] = np.clip(50.0 + (rvol_capped * obv_signal * 15.0), 0, 100).astype(float)
    
    # Composite Score
    df['Composite_Score'] = (
        df['Trend_Score'] * SCORE_WEIGHTS['trend'] +
        df['Momentum_Score'] * SCORE_WEIGHTS['momentum'] +
        df['Volume_Score'] * SCORE_WEIGHTS['volume']
    ).astype(float)
    
    return df

# ==========================================
# 4. MOTOR DE PROBABILIDADES (ML)
# ==========================================
class QuantitativeModel:
    def __init__(self, timeframe: str):
        self.timeframe = timeframe
        self.model = LogisticRegression(class_weight='balanced', max_iter=1000)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.features = ['Trend_Score', 'Momentum_Score', 'Volume_Score', 'Composite_Score']

    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Future_Return'] = df['Close'].shift(-1) / df['Close'] - 1
        threshold = TARGET_THRESHOLDS.get(self.timeframe, 0.01)
        conditions = [(df['Future_Return'] > threshold), (df['Future_Return'] < -threshold)]
        choices = [1, -1]
        df['Target'] = np.select(conditions, choices, default=0)
        return df.dropna(subset=['Future_Return'])

    def train(self, df: pd.DataFrame):
        df_target = self.create_targets(df)
        if len(df_target) < 10: return # Segurança
        X = df_target[self.features]
        y = df_target['Target']
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True

    def predict_probabilities(self, current_features: dict) -> dict:
        if not self.is_trained:
            return {"UP": 0, "NEUTRAL": 100, "DOWN": 0}
        df_features = pd.DataFrame([current_features])[self.features]
        X_scaled = self.scaler.transform(df_features)
        probs = self.model.predict_proba(X_scaled)[0]
        classes = self.model.classes_
        prob_dict = {
            "DOWN": round(probs[list(classes).index(-1)] * 100, 1) if -1 in classes else 0,
            "NEUTRAL": round(probs[list(classes).index(0)] * 100, 1) if 0 in classes else 0,
            "UP": round(probs[list(classes).index(1)] * 100, 1) if 1 in classes else 0
        }
        return prob_dict

# ==========================================
# 5. DASHBOARD UI (STREAMLIT)
# ==========================================
st.set_page_config(page_title="SYNAPSE Quant Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .metric-card { background-color: #1e1e1e; border-radius: 5px; padding: 15px; text-align: center; border: 1px solid #333; }
    .metric-value { font-size: 28px; font-weight: bold; }
    .bullish { color: #00ff88; }
    .bearish { color: #ff3344; }
    .neutral { color: #888888; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_and_process_data(ticker: str):
    provider = YahooFinanceProvider()
    results = {}
    for tf in ["1H", "1D", "1W"]:
        # Pedimos mais dados (10 anos) para garantir que 1D e 1W tenham histórico para as médias móveis
        period = "730d" if tf == "1H" else "10y"
        df = provider.get_historical_data(ticker, tf, period=period)
        
        if not df.empty:
            df = calculate_indicators(df)
            if not df.empty: # Se sobrou dados após limpar
                df = generate_scores(df)
                results[tf] = df
    return results

def render_gauge(val: float, title: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=val, title={'text': title, 'font': {'size': 14}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#00ff88" if val > 60 else "#ff3344" if val < 40 else "#888888"},
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 51, 68, 0.2)'},
                {'range': [40, 60], 'color': 'rgba(136, 136, 136, 0.2)'},
                {'range': [60, 100], 'color': 'rgba(0, 255, 136, 0.2)'}
            ]
        }
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- SIDEBAR ---
st.sidebar.title("⚙️ CONFIGURAÇÕES")
ticker = st.sidebar.text_input("Ativo (Ticker)", value="PETR4").upper()
model_choice = st.sidebar.selectbox("Modelo Quantitativo", ["Logistic Regression", "Rule Based (Em breve)"])

# --- ENGINE ---
data_dict = load_and_process_data(ticker)

# Proteção de UI
if not data_dict or "1D" not in data_dict or data_dict["1D"].empty:
    st.error(f"Dados insuficientes para calcular os indicadores de {ticker}. Tente outro ativo brasileiro válido (ex: VALE3, ITUB4).")
    st.stop()

df_1d = data_dict["1D"]
latest_1d = df_1d.iloc[-1]

st.markdown(f"### SYNAPSE QUANTITATIVE DASHBOARD | **{ticker}** | Atualizado: {datetime.now().strftime('%H:%M')}")

# --- ROW 1: SCORES ---
cols = st.columns(4)
scores = [("VOLUME", latest_1d['Volume_Score']), ("MOMENTUM", latest_1d['Momentum_Score']), ("TREND", latest_1d['Trend_Score']), ("COMPOSITE", latest_1d['Composite_Score'])]
for col, (title, val) in zip(cols, scores):
    with col: st.plotly_chart(render_gauge(val, title), use_container_width=True)

# --- ROW 2: PROBABILITIES & REGIME ---
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("#### PROBABILIDADE DE MOVIMENTO (ML)")
    prob_data = []
    for tf in ["1H", "1D", "1W"]:
        if tf in data_dict and not data_dict[tf].empty:
            df_tf = data_dict[tf]
            model = QuantitativeModel(tf)
            model.train(df_tf)
            probs = model.predict_probabilities(df_tf.iloc[-1].to_dict())
            prob_data.append({"Timeframe": tf, "UP (%)": probs["UP"], "NEUTRAL (%)": probs["NEUTRAL"], "DOWN (%)": probs["DOWN"]})
            
    if prob_data:
        prob_df = pd.DataFrame(prob_data).set_index("Timeframe")
        st.dataframe(prob_df.style.background_gradient(cmap='Greens', subset=['UP (%)']).background_gradient(cmap='Reds', subset=['DOWN (%)']).format("{:.1f}"), use_container_width=True)
    else:
        st.warning("Sem dados suficientes para as Probabilidades")

with col2:
    st.markdown("#### MARKET REGIME (1D)")
    adx_val = latest_1d[[c for c in df_1d.columns if c.startswith('ADX')][0]]
    regime = "SIDEWAYS"
    if adx_val > 25: regime = "TRENDING BULL" if latest_1d['Trend_Score'] > 50 else "TRENDING BEAR"
    regime_color = "bullish" if "BULL" in regime else "bearish" if "BEAR" in regime else "neutral"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: #888;">REGIME ATUAL</div>
        <div class="metric-value {regime_color}">{regime}</div><br>
        <div style="text-align: left; font-size: 14px;">ADX: {adx_val:.1f} | RVOL: {latest_1d['RVOL']:.2f}x</div>
    </div>
    """, unsafe_allow_html=True)

# --- ROW 3: CHART ---
st.markdown("#### CANDLESTICK & TECHNICALS (1D)")
fig_chart = go.Figure(data=[go.Candlestick(x=df_1d.index, open=df_1d['Open'], high=df_1d['High'], low=df_1d['Low'], close=df_1d['Close'], name="Preço")])
fig_chart.add_trace(go.Scatter(x=df_1d.index, y=df_1d['EMA_20'], line=dict(color='orange', width=1), name='EMA 20'))
fig_chart.add_trace(go.Scatter(x=df_1d.index, y=df_1d['EMA_200'], line=dict(color='purple', width=2), name='EMA 200'))
fig_chart.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
st.plotly_chart(fig_chart, use_container_width=True)
