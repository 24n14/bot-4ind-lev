import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Добавляем путь к директории проекта
sys.path.insert(0, '/home/edvard-user/PycharmProjects/bot_4ind')

# Импортируем тестируемую функцию и необходимые константы
from indicators import calculate_consensus_signal
import config
from config import INDICATOR_WEIGHTS


class TestCalculateConsensusSignal(unittest.TestCase):

    def setUp(self):
        # Сохраняем оригинальные значения конфигураций
        self.original_min_consensus_weight = config.MIN_CONSENSUS_WEIGHT
        self.original_min_participation = config.MIN_PARTICIPATION
        self.original_indicator_weights = INDICATOR_WEIGHTS.copy()

    def tearDown(self):
        # Восстанавливаем оригинальные значения после каждого теста
        config.MIN_CONSENSUS_WEIGHT = self.original_min_consensus_weight
        config.MIN_PARTICIPATION = self.original_min_participation
        INDICATOR_WEIGHTS.clear()
        INDICATOR_WEIGHTS.update(self.original_indicator_weights)

    def test_all_indicators_bullish(self):
        # Устанавливаем минимальные пороги для активации сигнала
        config.MIN_CONSENSUS_WEIGHT = 2
        config.MIN_PARTICIPATION = 3

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0,
            'stochastic': 1.0,
            'obv': 1.0
        })

        signals = {
            'ma_crossover': 'bullish',
            'macd': 'bullish',
            'stochastic': 'bullish',
            'obv': 'bullish'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        self.assertEqual(consensus_signal, 'bullish')
        self.assertTrue(is_absolute)
        self.assertEqual(details['bullish_total'], 4.0)
        self.assertEqual(details['bearish_total'], 0.0)

    def test_all_indicators_bearish(self):
        # Устанавливаем минимальные пороги для активации сигнала
        config.MIN_CONSENSUS_WEIGHT = 2
        config.MIN_PARTICIPATION = 3

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0,
            'stochastic': 1.0,
            'obv': 1.0
        })

        signals = {
            'ma_crossover': 'bearish',
            'macd': 'bearish',
            'stochastic': 'bearish',
            'obv': 'bearish'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        self.assertEqual(consensus_signal, 'bearish')
        self.assertTrue(is_absolute)
        self.assertEqual(details['bullish_total'], 0.0)
        self.assertEqual(details['bearish_total'], 4.0)

    def test_hold_due_to_insufficient_active_indicators(self):
        # Устанавливаем минимальное участие в 3 индикатора
        config.MIN_PARTICIPATION = 3

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0,
            'stochastic': 1.0,
            'obv': 1.0
        })

        # Только 2 активных индикатора
        signals = {
            'ma_crossover': 'bullish',
            'macd': 'bullish',
            'stochastic': None,
            'obv': None
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        self.assertEqual(consensus_signal, 'hold')
        self.assertFalse(is_absolute)

    def test_hold_when_weights_below_threshold(self):
        # Устанавливаем минимальный вес для сигнала в 3
        config.MIN_CONSENSUS_WEIGHT = 3
        config.MIN_PARTICIPATION = 2

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0,
            'stochastic': 1.0,
            'obv': 1.0
        })

        # Только 2 bullish индикатора = вес 2 < 3
        signals = {
            'ma_crossover': 'bullish',
            'macd': 'bullish',
            'stochastic': 'hold',
            'obv': 'hold'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        self.assertEqual(consensus_signal, 'hold')
        self.assertFalse(is_absolute)
        self.assertEqual(details['bullish_total'], 2.0)
        self.assertEqual(details['bearish_total'], 0.0)

    def test_bullish_wins_with_sufficient_weight(self):
        # Устанавливаем минимальный вес для сигнала в 2
        config.MIN_CONSENSUS_WEIGHT = 2
        config.MIN_PARTICIPATION = 3

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.5,
            'stochastic': 1.0,
            'obv': 0.5
        })

        signals = {
            'ma_crossover': 'bullish',
            'macd': 'bullish',
            'stochastic': 'hold',
            'obv': 'bearish'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        # bullish: 1.0 + 1.5 = 2.5
        # bearish: 0.5
        self.assertEqual(consensus_signal, 'bullish')
        self.assertFalse(is_absolute)
        self.assertEqual(details['bullish_total'], 2.5)
        self.assertEqual(details['bearish_total'], 0.5)

    def test_bearish_wins_with_sufficient_weight(self):
        # Устанавливаем минимальный вес для сигнала в 2
        config.MIN_CONSENSUS_WEIGHT = 2
        config.MIN_PARTICIPATION = 3

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0,
            'stochastic': 1.0,
            'obv': 1.0
        })

        signals = {
            'ma_crossover': 'bearish',
            'macd': 'bearish',
            'stochastic': 'hold',
            'obv': 'hold'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        # bullish: 0
        # bearish: 2.0
        self.assertEqual(consensus_signal, 'bearish')
        self.assertFalse(is_absolute)
        self.assertEqual(details['bullish_total'], 0.0)
        self.assertEqual(details['bearish_total'], 2.0)

    def test_hold_when_equal_weights(self):
        # Устанавливаем минимальный вес для сигнала в 2
        config.MIN_CONSENSUS_WEIGHT = 2
        config.MIN_PARTICIPATION = 2

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0
        })

        signals = {
            'ma_crossover': 'bullish',
            'macd': 'bearish'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        # bullish: 1.0
        # bearish: 1.0
        self.assertEqual(consensus_signal, 'hold')
        self.assertFalse(is_absolute)
        self.assertEqual(details['bullish_total'], 1.0)
        self.assertEqual(details['bearish_total'], 1.0)

    def test_none_signals_are_ignored(self):
        # Устанавливаем минимальный вес для сигнала в 2
        config.MIN_CONSENSUS_WEIGHT = 2
        config.MIN_PARTICIPATION = 2

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0,
            'stochastic': 1.0
        })

        signals = {
            'ma_crossover': 'bullish',
            'macd': None,
            'stochastic': 'bullish'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        self.assertEqual(consensus_signal, 'bullish')
        self.assertFalse(is_absolute)
        self.assertEqual(details['bullish_total'], 2.0)
        self.assertEqual(details['bearish_total'], 0.0)

    @patch('indicators.logger')
    def test_logging_output(self, mock_logger):
        # Устанавливаем минимальные пороги
        config.MIN_CONSENSUS_WEIGHT = 2
        config.MIN_PARTICIPATION = 2

        # Устанавливаем веса индикаторов
        INDICATOR_WEIGHTS.update({
            'ma_crossover': 1.0,
            'macd': 1.0
        })

        signals = {
            'ma_crossover': 'bullish',
            'macd': 'bearish'
        }

        consensus_signal, details, is_absolute = calculate_consensus_signal(signals)

        # Проверяем, что логирование вызывалось
        self.assertTrue(mock_logger.info.called)


if __name__ == '__main__':
    unittest.main()
