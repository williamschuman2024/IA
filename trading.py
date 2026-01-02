import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import time
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN DE ACCESO
# ==========================================
TOKEN = "7864353457:AAFmS_pLshf7zAnN9p7lRsk6S-66f8p8nO4"
CHAT_ID = "1133036423"
SYMBOL = "BTC/USDT"
TIMEFRAME = '1h'

# Configuración de Kraken (Exchange)
exchange = ccxt.kraken({
    'enableRateLimit': True,
})

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

# ==========================================
# 2. OBTENCIÓN Y PROCESAMIENTO DE DATOS
# ==========================================
def obtener_datos():
    # Descarga las últimas 100 velas de 1 hora
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Indicadores Técnicos (Base para la IA)
    df['RSI'] = df.ta.rsi(length=14)
    df['EMA_20'] = df.ta.ema(length=20)
    df['ATR'] = df.ta.atr(length=14)
    
    return df

# ==========================================
# 3. NÚCLEO DE INTELIGENCIA ARTIFICIAL
# ==========================================
def entrenar_y_predecir(df):
    # Definimos el objetivo: 1 si el precio sube en la próxima vela, 0 si baja
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    # Limpiamos datos nulos generados por indicadores y el shift
    df_clean = df.dropna().copy()
    
    # Características que la IA analizará
    features = ['RSI', 'EMA_20', 'close', 'ATR']
    X = df_clean[features]
    y = df_clean['target']
    
    # --- AQUÍ ES DONDE PODRÁS CAMBIAR LA IA EN EL FUTURO ---
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X, y)
    
    # Predicción sobre el momento actual (última fila)
    ultima_fila = X.iloc[[-1]]
    prediccion = modelo.predict(ultima_fila)[0]
    probabilidad = modelo.predict_proba(ultima_fila)[0][1]
    
    return prediccion, probabilidad

# ==========================================
# 4. CICLO PRINCIPAL DE EJECUCIÓN
# ==========================================
def main():
    enviar_telegram(f"🚀 Bot 'Oro Puro' iniciado correctamente\nExchange: Kraken\nPar: {SYMBOL}\nTimeframe: {TIMEFRAME}")
    
    while True:
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Analizando mercado...")
            
            datos = obtener_datos()
            decision, confianza = entrenar_y_predecir(datos)
            
            precio_actual = datos['close'].iloc[-1]
            
            # Umbral de seguridad: solo avisa si la IA está muy segura (>65%)
            if confianza > 0.65:
                if decision == 1:
                    alerta = f"🟢 SEÑAL DE COMPRA\nPrecio: {precio_actual}\nConfianza: {confianza:.2%}"
                else:
                    alerta = f"🔴 SEÑAL DE VENTA\nPrecio: {precio_actual}\nConfianza: {confianza:.2%}"
                
                enviar_telegram(alerta)
                print(f"Alerta enviada: {alerta.replace('\n', ' ')}")
            
            # Esperar a la siguiente vela (1 hora)
            time.sleep(3600)
            
        except Exception as e:
            print(f"⚠️ Error detectado: {e}")
            enviar_telegram(f"⚠️ Error en el bot: {str(e)[:100]}")
            time.sleep(60) # Espera un minuto antes de reintentar si hay error de red

if __name__ == "__main__":
    main()