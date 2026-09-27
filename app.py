@st.cache_data(ttl=1800)
def analisar_ativo(ticker):
    try:
        # Baixando os dados diários
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        
        # Tratamento robusto para diferentes versões do yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Garante que as colunas essenciais existem e limpa NaNs
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            
        if len(df) < 30:
            return None

        # 1. Médias Móveis Exponenciais (Tendência)
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        
        # 2. Cálculo do ADX (Força do Mercado simplificada e segura contra divisão por zero)
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
        vol_positivo = variacao_preco >= 0

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
        logo_url = f"https://s3-symbol-logo.tradingview.com/br/b3--{ticker_limpo.lower()}.svg"

        return {
            "Ticker": ticker_limpo,
            "Logo": logo_url,
            "Score Volume": score_vol,
            "Vol Positivo": vol_positivo,
            "Tendência": tendencia,
            "Força": forca,
            "Prob 1H": prob_1h_str,
            "Prob 1D": prob_1d_str,
            "Prob 1S": prob_1s_str,
            "Sinal Final": sinal
        }
    except Exception as e:
        print(f"Erro ao processar {ticker}: {e}")
        return None
