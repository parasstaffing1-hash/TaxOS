"""Unit tests for India Capital Gains Engine & Loss Set-Off."""

from decimal import Decimal

from taxos.domain.india.capital_gains import (
    AssetType,
    CapitalGainsTransaction,
    IndiaCapitalGainsEngine,
)


def test_equity_ltcg_112a_with_exemption():
    """Verify Section 112A LTCG on equity with ₹1.25L exemption (AY 2025-26)."""
    engine = IndiaCapitalGainsEngine(assessment_year="2025-26")

    # Purchase 500 shares @ ₹1,000 = ₹5,00,000
    # Sale 500 shares @ ₹1,500 = ₹7,50,000 (Holding period 18 months -> LTCG = ₹2,50,000)
    # Exemption = ₹1,25,000. Taxable LTCG = ₹1,25,000 @ 12.5% = ₹15,625
    tx = CapitalGainsTransaction(
        asset_name="Reliance Industries",
        asset_type=AssetType.LISTED_EQUITY_STOCKS,
        sale_date="2024-11-15",
        purchase_date="2023-05-10",
        holding_period_months=18,
        sale_consideration=Decimal("750000.0"),
        cost_of_acquisition=Decimal("500000.0"),
    )
    res = engine.calculate_gains([tx])

    assert res.ltcg_112a_equity_gross == Decimal("250000.0")
    assert res.ltcg_112a_exemption_claimed == Decimal("125000.0")
    assert res.ltcg_112a_taxable == Decimal("125000.0")
    assert res.total_capital_gains_tax == Decimal("15625.0")


def test_capital_loss_set_off():
    """Verify Section 70/71 set-off rules: STCL can set off against LTCG, but LTCL cannot set off against STCG."""
    engine = IndiaCapitalGainsEngine(assessment_year="2025-26")

    tx_gain = CapitalGainsTransaction(
        asset_name="HDFC Bank",
        asset_type=AssetType.LISTED_EQUITY_STOCKS,
        sale_date="2024-10-01",
        purchase_date="2023-01-01",
        holding_period_months=21,
        sale_consideration=Decimal("500000.0"),
        cost_of_acquisition=Decimal("300000.0"),  # LTCG = 200,000
    )
    tx_loss = CapitalGainsTransaction(
        asset_name="Infosys",
        asset_type=AssetType.LISTED_EQUITY_STOCKS,
        sale_date="2024-10-01",
        purchase_date="2024-06-01",
        holding_period_months=4,
        sale_consideration=Decimal("100000.0"),
        cost_of_acquisition=Decimal("150000.0"),  # STCL = 50,000
    )

    res = engine.calculate_gains([tx_gain, tx_loss])
    assert res.stcl_incurred == Decimal("50000.0")
    # Gross LTCG 200k - 125k exemption = 75k taxable. 75k - 50k STCL setoff = 25k net taxable LTCG
    assert res.net_ltcg_taxable == Decimal("25000.0")
    assert res.stcl_carried_forward == Decimal("0.0")
