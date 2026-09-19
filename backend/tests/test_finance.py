from decimal import Decimal
from app.services.finance import binary_profit,break_even,expected_value,stake_for_balance
from app.services.finance import session_risk
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

def test_gross_losses_over_budget_do_not_stop_a_net_profitable_or_recovered_session():
    risk=session_risk(Decimal('1993.27'),Decimal('1'),Decimal('40'),10,map(Decimal,['16.80','16.94','-20.34','-20.13']))
    assert risk.net_pnl==Decimal('-6.73')
    assert risk.loss_consumed==Decimal('6.73')
    assert risk.remaining_risk==Decimal('33.27')
    assert not risk.limit_reached

def test_recommendation_obeys_all_caps_and_profit_does_not_expand_trade_percentage():
    assert session_risk(Decimal('2016.80'),Decimal('1'),Decimal('40'),4,[Decimal('16.80')]).suggested_stake==Decimal('20.17')
    assert session_risk(Decimal('1960.20'),Decimal('1'),Decimal('40'),4,[Decimal('-39.80')]).suggested_stake==Decimal('.20')
    assert session_risk(Decimal('.01'),Decimal('100'),Decimal('40'),4,[]).suggested_stake==Decimal('.01')
