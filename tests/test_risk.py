"""Unit tests for Risk Manager"""

import pytest
from src.risk.manager import RiskManager
from src.models.domain import Portfolio


@pytest.fixture
def sample_portfolio():
    """Create sample portfolio for testing"""
    return Portfolio(
        positions={'SPY': 100, 'GLD': 50},
        cash=50000,
        nav=100000,
        peak_nav=110000,
        weights={'SPY': 0.5, 'GLD': 0.2},
        unrealized_pnl=-5000,
        cost_basis={'SPY': 400, 'GLD': 180}
    )


def test_risk_manager_initialization():
    """Test RiskManager initialization"""
    rm = RiskManager()
    assert rm is not None
    assert rm.current_level == 0


def test_assess_risk_level_normal(sample_portfolio):
    """Test risk level assessment - normal state"""
    rm = RiskManager()
    
    # No drawdown
    sample_portfolio.nav = sample_portfolio.peak_nav
    level = rm.assess_risk_level(sample_portfolio)
    assert level == 0


def test_assess_risk_level_1():
    """Test risk level 1 trigger"""
    rm = RiskManager()
    
    portfolio = Portfolio(
        positions={},
        cash=94000,
        nav=94000,  # 6% drawdown from peak
        peak_nav=100000,
        weights={},
        unrealized_pnl=0,
        cost_basis={}
    )
    
    level = rm.assess_risk_level(portfolio)
    assert level == 1


def test_assess_risk_level_2():
    """Test risk level 2 trigger"""
    rm = RiskManager()
    
    portfolio = Portfolio(
        positions={},
        cash=91000,
        nav=91000,  # 9% drawdown
        peak_nav=100000,
        weights={},
        unrealized_pnl=0,
        cost_basis={}
    )
    
    level = rm.assess_risk_level(portfolio)
    assert level == 2


def test_assess_risk_level_3():
    """Test risk level 3 trigger"""
    rm = RiskManager()
    
    portfolio = Portfolio(
        positions={},
        cash=87000,
        nav=87000,  # 13% drawdown
        peak_nav=100000,
        weights={},
        unrealized_pnl=0,
        cost_basis={}
    )
    
    level = rm.assess_risk_level(portfolio)
    assert level == 3


def test_assess_risk_level_4():
    """Test risk level 4 trigger"""
    rm = RiskManager()
    
    portfolio = Portfolio(
        positions={},
        cash=84000,
        nav=84000,  # 16% drawdown
        peak_nav=100000,
        weights={},
        unrealized_pnl=0,
        cost_basis={}
    )
    
    level = rm.assess_risk_level(portfolio)
    assert level == 4


def test_apply_controls():
    """Test risk control application"""
    rm = RiskManager()
    
    portfolio = Portfolio(
        positions={},
        cash=91000,
        nav=91000,
        peak_nav=100000,
        weights={},
        unrealized_pnl=0,
        cost_basis={}
    )
    
    actions = rm.apply_controls(2, portfolio)
    assert 'REDUCE_25%' in actions
    assert 'CLOSE_BTC' in actions
    assert 'SELL_ONLY' in actions


def test_check_single_asset_stop_exit():
    """Test single asset stop loss - exit trigger"""
    rm = RiskManager()
    
    # 20% drawdown should trigger exit
    action = rm.check_single_asset_stop('SPY', 100, 80)
    assert action == "EXIT"


def test_check_single_asset_stop_reduce():
    """Test single asset stop loss - reduce trigger"""
    rm = RiskManager()
    
    # 15% drawdown should trigger reduce
    action = rm.check_single_asset_stop('SPY', 100, 85)
    assert action == "REDUCE_50%"


def test_check_single_asset_stop_ok():
    """Test single asset stop loss - no trigger"""
    rm = RiskManager()
    
    # 5% drawdown should not trigger
    action = rm.check_single_asset_stop('SPY', 100, 95)
    assert action is None


def test_should_block_new_positions():
    """Test position blocking"""
    rm = RiskManager()
    
    rm.current_level = 0
    assert not rm.should_block_new_positions()
    
    rm.current_level = 2
    assert rm.should_block_new_positions()


def test_should_sell_only():
    """Test sell-only mode"""
    rm = RiskManager()
    
    rm.current_level = 1
    assert not rm.should_sell_only()
    
    rm.current_level = 2
    assert rm.should_sell_only()


def test_get_position_reduction_factor():
    """Test position reduction factor calculation"""
    rm = RiskManager()
    
    rm.current_level = 0
    assert rm.get_position_reduction_factor() == 1.0
    
    rm.current_level = 2
    assert rm.get_position_reduction_factor() == 0.75
    
    rm.current_level = 3
    assert rm.get_position_reduction_factor() == 0.50
    
    rm.current_level = 4
    assert rm.get_position_reduction_factor() == 0.0


def test_is_safe_haven_asset():
    """Test safe haven asset identification"""
    rm = RiskManager()
    
    assert rm.is_safe_haven_asset('GLD')
    assert rm.is_safe_haven_asset('TLT')
    assert not rm.is_safe_haven_asset('SPY')
    assert not rm.is_safe_haven_asset('BTC-USD')