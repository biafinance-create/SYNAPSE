# 2. Substituição do ADX por Desvio Padrão (Volatilidade / Força)
        # Calculamos o desvio padrão dos retornos percentuais dos últimos 14 períodos
        df['Retorno'] = df['Close'].pct_change()
        desvio_padrao = df['Retorno'].rolling(14).std().iloc[-1] * 100  # em %
        
        # Como o desvio padrão varia por ativo, usamos limiares dinâmicos ou baseados em percentil
        # (Ou podemos usar a largura normalizada das Bandas de Bollinger de 20 períodos, 2 desvios)
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD20'] = df['Close'].rolling(20).std()
        df['Banda_Superior'] = df['MA20'] + (2 * df['STD20'])
        df['Banda_Inferior'] = df['MA20'] - (2 * df['STD20'])
        
        # Largura das Bandas de Bollinger (Métrica excelente de força/compressão)
        largura_bandas = ((df['Banda_Superior'] - df['Banda_Inferior']) / df['MA20']).iloc[-1]
        
        # Classificação baseada na largura das bandas (Força / Volatilidade)
        if largura_bandas > 0.08:  # 8% de amplitude relativa
            forca_str = f"🚀 Forte (Vol. Alta)"
            forca_val = 1
        elif largura_bandas >= 0.04:
            forca_str = f"📈 Moderada"
            forca_val = 0.5
        else:
            forca_str = f"💤 Fraca (Comprimido)"
            forca_val = 0
