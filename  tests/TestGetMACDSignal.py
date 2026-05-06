import unittest
import numpy as np
import sys
from indicators import _get_macd_signal
# Добавляем путь к директории проекта
sys.path.insert(0, '/home/edvard-user/PycharmProjects/bot_4ind')
class TestGetMACDSignal(unittest.TestCase):

    def test_not_enough_data(self):
        close = np.array([1.0] * 25)  # less than 26
        result = _get_macd_signal(close)
        self.assertIsNone(result)

    def test_nan_values(self):
        close = np.array([1.0] * 100)
        # Mock talib.MACD to return NaNs
        import talib
        original_macd = talib.MACD
        def mock_macd(*args, **kwargs):
            macd = np.array([np.nan] * len(args[0]))
            signal = np.array([np.nan] * len(args[0]))
            hist = np.array([np.nan] * len(args[0]))
            return macd, signal, hist
        talib.MACD = mock_macd
        result = _get_macd_signal(close)
        self.assertIsNone(result)
        talib.MACD = original_macd

    def test_bullish_crossover(self):
        # Create a simple increasing price series to simulate bullish crossover
        close = np.linspace(100, 120, 100)
        result = _get_macd_signal(close)
        # Depending on actual values, it might be 'bullish' or 'hold'
        # This test just ensures it doesn't crash and returns a valid string
        self.assertIn(result, ['bullish', 'bearish', 'hold'])

    def test_bearish_crossover(self):
        # Create a simple decreasing price series
        close = np.linspace(120, 100, 100)
        result = _get_macd_signal(close)
        self.assertIn(result, ['bullish', 'bearish', 'hold'])

    def test_hold_case(self):
        # Flat price data
        close = np.array([100.0] * 100)
        result = _get_macd_signal(close)
        self.assertIn(result, ['bullish', 'bearish', 'hold'])


if __name__ == '__main__':
    unittest.main()
