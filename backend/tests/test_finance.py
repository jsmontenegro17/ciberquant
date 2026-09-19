from decimal import Decimal
from app.services.finance import binary_profit,break_even,expected_value,stake_for_balance
def test_binary_math():
    assert binary_profit(Decimal('20'),Decimal('84'),'WIN')==Decimal('16.80')
    assert binary_profit(Decimal('20'),Decimal('84'),'LOSS')==Decimal('-20.00')
    assert break_even(Decimal('84'))==Decimal('0.5434782608695652173913043478')
    assert stake_for_balance(Decimal('2000'),Decimal('1'))==Decimal('20.00')
def test_ev(): assert expected_value(Decimal('0.6'),Decimal('84'))==Decimal('0.104')
def test_ev_negative_and_break_even():
    assert expected_value(Decimal('0.5'),Decimal('84'))==Decimal('-0.08')
    assert expected_value(Decimal('0.5434782608695652173913043478'),Decimal('84'))==Decimal('0E-28')
def test_non_integer_rounding():
    assert binary_profit(Decimal('19.99'),Decimal('83.5'),'WIN')==Decimal('16.69')
