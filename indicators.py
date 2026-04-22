import numpy as np
import talib
import logging
from config import INDICATOR_WEIGHTS

logger = logging.getLogger(__name__)


def calculate_indicator_signals(high, low, close, volume):
    """
    Расчитывает сигналы для всех четырех индикаторов.

    Returns:
        dict: Словарь с сигналами каждого индикатора:
            {
                'ma_crossover': 'bullish'/'bearish'/None,
                'macd': 'bullish'/'bearish'/None,
                'stochastic': 'bullish'/'bearish'/None,
                'obv': 'bullish'/'bearish'/None
            }
    """
    signals = {}

    try:
        # Индикатор #1: MA10/EMA50 Crossover
        signals['ma_crossover'] = _get_ma_crossover_signal(close)
    except Exception as e:
        logger.warning(f"Ошибка при расчете MA crossover: {e}")
        signals['ma_crossover'] = None

    try:
        # Индикатор #2: MACD
        signals['macd'] = _get_macd_signal(close)
    except Exception as e:
        logger.warning(f"Ошибка при расчете MACD: {e}")
        signals['macd'] = None

    try:
        # Индикатор #3: Stochastic
        signals['stochastic'] = _get_stochastic_signal(high, low, close)
    except Exception as e:
        logger.warning(f"Ошибка при расчете Stochastic: {e}")
        signals['stochastic'] = None

    try:
        # Индикатор #4: OBV Trend
        signals['obv'] = _get_obv_signal(close, volume)
    except Exception as e:
        logger.warning(f"Ошибка при расчете OBV: {e}")
        signals['obv'] = None

    return signals


def _get_ma_crossover_signal(close):
    """
    Индикатор #1: Пересечение MA10 и EMA50

    Бычий сигнал: MA10 пересекает EMA50 снизу вверх
    Медвежий сигнал: MA10 пересекает EMA50 сверху вниз
    """
    if len(close) < 50:
        return None

    ma10 = talib.SMA(close, timeperiod=10)
    ema50 = talib.EMA(close, timeperiod=50)

    # Берем последние 2 значения для определения пересечения
    current_ma10 = ma10[-1]
    current_ema50 = ema50[-1]
    prev_ma10 = ma10[-2]
    prev_ema50 = ema50[-2]

    # Проверяем пересечение
    if np.isnan(current_ma10) or np.isnan(current_ema50) or \
            np.isnan(prev_ma10) or np.isnan(prev_ema50):
        return None

    # MA10 было ниже EMA50, теперь выше → BULLISH
    if prev_ma10 <= prev_ema50 and current_ma10 > current_ema50:
        return 'bullish'

    # MA10 было выше EMA50, теперь ниже → BEARISH
    elif prev_ma10 >= prev_ema50 and current_ma10 < current_ema50:
        return 'bearish'

    return None


def _get_macd_signal(close):
    """
    Индикатор #2: MACD

    Бычий сигнал: MACD пересекает сигнальную линию снизу вверх
    Медвежий сигнал: MACD пересекает сигнальную линию сверху вниз
    """
    if len(close) < 26:
        return None

    macd, signal_line, histogram = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

    # Берем последние 2 значения
    current_macd = macd[-1]
    current_signal = signal_line[-1]
    prev_macd = macd[-2]
    prev_signal = signal_line[-2]

    # Проверяем пересечение
    if np.isnan(current_macd) or np.isnan(current_signal) or \
            np.isnan(prev_macd) or np.isnan(prev_signal):
        return None

    # MACD было ниже сигнальной линии, теперь выше → BULLISH
    if prev_macd <= prev_signal and current_macd > current_signal:
        return 'bullish'

    # MACD было выше сигнальной линии, теперь ниже → BEARISH
    elif prev_macd >= prev_signal and current_macd < current_signal:
        return 'bearish'

    return None


def _get_stochastic_signal(high, low, close):
    """
    Индикатор #3: Stochastic Oscillator

    Бычий сигнал: %K пересекает %D снизу вверх в зоне перепродажи (<20)
    Медвежий сигнал: %K пересекает %D сверху вниз в зоне перекупленности (>80)
    """
    if len(close) < 14:
        return None

    slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)

    # Берем последние 2 значения
    current_k = slowk[-1]
    current_d = slowd[-1]
    prev_k = slowk[-2]
    prev_d = slowd[-2]

    if np.isnan(current_k) or np.isnan(current_d) or \
            np.isnan(prev_k) or np.isnan(prev_d):
        return None

    # %K пересекает %D снизу вверх в зоне перепродажи → BULLISH
    if prev_k <= prev_d and current_k > current_d and current_k < 20:
        return 'bullish'

    # %K пересекает %D сверху вниз в зоне перекупленности → BEARISH
    elif prev_k >= prev_d and current_k < current_d and current_k > 80:
        return 'bearish'

    return None


def _get_obv_signal(close, volume):
    """
    Индикатор #4: OBV Trend

    Бычий сигнал: OBV растет
    Медвежий сигнал: OBV падает
    """
    if len(close) < 10:
        return None

    obv = talib.OBV(close, volume)

    # Сглаживаем OBV для более стабильного сигнала
    obv_sma = talib.SMA(obv, timeperiod=5)

    # Берем последние 2 значения
    current_obv = obv_sma[-1]
    prev_obv = obv_sma[-2]

    if np.isnan(current_obv) or np.isnan(prev_obv):
        return None

    # OBV растет → BULLISH
    if current_obv > prev_obv:
        return 'bullish'

    # OBV падает → BEARISH
    elif current_obv < prev_obv:
        return 'bearish'

    return None


def calculate_consensus_signal(signals):
    """
    Рассчитывает консенсус-сигнал на основе взвешенного голосования.

    Args:
        signals (dict): Результат calculate_indicator_signals()

    Returns:
        tuple: (consensus_signal, details)
            consensus_signal: 'bullish', 'bearish', или 'hold'
            details: dict с детальной информацией о голосовании
    """

    # Инициализируем счетчики
    bullish_weight = 0.0
    bearish_weight = 0.0
    details = {
        'votes': {},
        'weights_used': INDICATOR_WEIGHTS.copy(),
        'bullish_total': 0.0,
        'bearish_total': 0.0,
        'consensus': None
    }

    # Обходим каждый индикатор
    for indicator_name, signal in signals.items():
        weight = INDICATOR_WEIGHTS.get(indicator_name, 1.0)

        details['votes'][indicator_name] = {
            'signal': signal,
            'weight': weight
        }

        if signal == 'bullish':
            bullish_weight += weight
        elif signal == 'bearish':
            bearish_weight += weight

    details['bullish_total'] = bullish_weight
    details['bearish_total'] = bearish_weight

    # Логируем голосование
    logger.info(f"Консенсус-голосование:")
    for ind_name, vote_info in details['votes'].items():
        logger.info(f"  {ind_name}: {vote_info['signal']} (вес: {vote_info['weight']})")
    logger.info(f"  BULLISH сумма: {bullish_weight} | BEARISH сумма: {bearish_weight}")

    # Определяем результат на основе перевеса
    if bullish_weight > bearish_weight:
        consensus_signal = 'bullish'
        logger.info(f"✅ BULLISH консенсус ({bullish_weight} vs {bearish_weight})")
    elif bearish_weight > bullish_weight:
        consensus_signal = 'bearish'
        logger.info(f"❌ BEARISH консенсус ({bearish_weight} vs {bullish_weight})")
    else:
        # При равном весе - HOLD
        consensus_signal = 'hold'
        logger.info(f"⏸️  HOLD консенсус (равное голосование: {bullish_weight})")

    details['consensus'] = consensus_signal

    return consensus_signal, details


def get_indicator_analysis(high, low, close, volume):
    """
    Главная функция для получения консенсус-сигнала.
    Объединяет расчет сигналов и определение консенсуса.

    Returns:
        tuple: (consensus_signal, details)
    """

    # Получаем сигналы от всех индикаторов
    signals = calculate_indicator_signals(high, low, close, volume)

    # Рассчитываем консенсус-сигнал
    consensus_signal, details = calculate_consensus_signal(signals)

    return consensus_signal, details
