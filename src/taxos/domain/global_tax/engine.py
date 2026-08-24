"""Global Multi-Jurisdiction Tax Engine.

Provides independent country rule packs and deterministic tax calculations
for US, GB, AE, CA, AU, SG, SA, DE, FR, NL, IT, ES, NZ, JP, and ZA.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from taxos.domain.financial.trace import TaxSlabBreakdown
from taxos.domain.global_tax.models import (
    CountryTaxProfile,
    GlobalCalculationInput,
    GlobalCalculationResult,
    GlobalTaxType,
)

# Statutory Multi-Country Rule Packs
GLOBAL_COUNTRY_PACKS: dict[str, CountryTaxProfile] = {
    # 1. UNITED STATES (US) - 2024/2025 Federal Brackets
    "US": CountryTaxProfile(
        country_code="US",
        country_name="United States",
        currency_code="USD",
        currency_symbol="$",
        personal_allowance_or_standard_deduction=Decimal("14600.0"),  # Single 2024
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("11600.0"), Decimal("0.10")),
            (Decimal("11600.0"), Decimal("47150.0"), Decimal("0.12")),
            (Decimal("47150.0"), Decimal("100525.0"), Decimal("0.22")),
            (Decimal("100525.0"), Decimal("191950.0"), Decimal("0.24")),
            (Decimal("191950.0"), Decimal("243725.0"), Decimal("0.32")),
            (Decimal("243725.0"), Decimal("609350.0"), Decimal("0.35")),
            (Decimal("609350.0"), None, Decimal("0.37")),
        ],
        employee_social_security_rate=Decimal("0.0765"),  # 6.2% Social Security + 1.45% Medicare
        employer_social_security_rate=Decimal("0.0765"),
        corporate_tax_standard_rate=Decimal("0.21"),
        vat_gst_standard_rate=Decimal("0.07"),  # Avg state sales tax
        official_tax_authority_name="Internal Revenue Service (IRS)",
        tax_authority_website="https://www.irs.gov",
    ),
    # 2. UNITED KINGDOM (GB) - 2024/2025 HMRC
    "GB": CountryTaxProfile(
        country_code="GB",
        country_name="United Kingdom",
        currency_code="GBP",
        currency_symbol="£",
        personal_allowance_or_standard_deduction=Decimal("12570.0"),
        income_tax_slabs=[
            (
                Decimal("0.0"),
                Decimal("37700.0"),
                Decimal("0.20"),
            ),  # Basic rate (above personal allowance)
            (Decimal("37700.0"), Decimal("125140.0"), Decimal("0.40")),  # Higher rate
            (Decimal("125140.0"), None, Decimal("0.45")),  # Additional rate
        ],
        employee_social_security_rate=Decimal("0.08"),  # National Insurance Class 1 (8%)
        employer_social_security_rate=Decimal("0.138"),  # Employer NI (13.8%)
        corporate_tax_standard_rate=Decimal("0.25"),  # 25% for profits > £250k (19% small profits)
        corporate_tax_threshold=Decimal("250000.0"),
        corporate_tax_reduced_rate=Decimal("0.19"),
        vat_gst_standard_rate=Decimal("0.20"),  # 20% standard VAT
        vat_gst_reduced_rate=Decimal("0.05"),  # 5% reduced VAT
        vat_registration_threshold=Decimal("90000.0"),  # £90,000 threshold
        official_tax_authority_name="HM Revenue & Customs (HMRC)",
        tax_authority_website="https://www.gov.uk/government/organisations/hm-revenue-customs",
    ),
    # 3. UNITED ARAB EMIRATES (AE) - Federal Tax Authority (FTA)
    "AE": CountryTaxProfile(
        country_code="AE",
        country_name="United Arab Emirates",
        currency_code="AED",
        currency_symbol="AED ",
        personal_allowance_or_standard_deduction=Decimal("0.0"),  # 0% Personal Income Tax
        income_tax_slabs=[
            (Decimal("0.0"), None, Decimal("0.00")),  # No personal income tax in UAE
        ],
        corporate_tax_standard_rate=Decimal("0.09"),  # 9% Corporate Tax over AED 375,000
        corporate_tax_threshold=Decimal("375000.0"),  # 0% up to AED 375,000 / Qualifying Free Zone
        corporate_tax_reduced_rate=Decimal("0.00"),
        vat_gst_standard_rate=Decimal("0.05"),  # 5% standard VAT
        vat_registration_threshold=Decimal("375000.0"),
        official_tax_authority_name="Federal Tax Authority (FTA)",
        tax_authority_website="https://tax.gov.ae",
    ),
    # 4. CANADA (CA) - CRA Federal Rates
    "CA": CountryTaxProfile(
        country_code="CA",
        country_name="Canada",
        currency_code="CAD",
        currency_symbol="C$",
        personal_allowance_or_standard_deduction=Decimal("15705.0"),  # Basic Personal Amount 2024
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("55867.0"), Decimal("0.15")),
            (Decimal("55867.0"), Decimal("111733.0"), Decimal("0.205")),
            (Decimal("111733.0"), Decimal("173205.0"), Decimal("0.26")),
            (Decimal("173205.0"), Decimal("246752.0"), Decimal("0.29")),
            (Decimal("246752.0"), None, Decimal("0.33")),
        ],
        corporate_tax_standard_rate=Decimal("0.15"),  # Federal net tax (9% small business rate)
        corporate_tax_threshold=Decimal("500000.0"),
        corporate_tax_reduced_rate=Decimal("0.09"),
        vat_gst_standard_rate=Decimal("0.05"),  # 5% Federal GST (+ provincial HST/PST/QST)
        official_tax_authority_name="Canada Revenue Agency (CRA)",
        tax_authority_website="https://www.canada.ca/en/revenue-agency.html",
    ),
    # 5. AUSTRALIA (AU) - ATO 2024/2025 Stage 3 Cuts
    "AU": CountryTaxProfile(
        country_code="AU",
        country_name="Australia",
        currency_code="AUD",
        currency_symbol="A$",
        personal_allowance_or_standard_deduction=Decimal("18200.0"),  # Tax-free threshold
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("18200.0"), Decimal("0.00")),
            (Decimal("18200.0"), Decimal("45000.0"), Decimal("0.16")),  # Stage 3 revised
            (Decimal("45000.0"), Decimal("135000.0"), Decimal("0.30")),
            (Decimal("135000.0"), Decimal("190000.0"), Decimal("0.37")),
            (Decimal("190000.0"), None, Decimal("0.45")),
        ],
        employee_social_security_rate=Decimal("0.02"),  # 2% Medicare Levy
        employer_social_security_rate=Decimal("0.115"),  # 11.5% Superannuation Guarantee
        corporate_tax_standard_rate=Decimal("0.30"),  # 30% (25% for base rate entities)
        corporate_tax_threshold=Decimal("50000000.0"),
        corporate_tax_reduced_rate=Decimal("0.25"),
        vat_gst_standard_rate=Decimal("0.10"),  # 10% GST
        vat_registration_threshold=Decimal("75000.0"),
        official_tax_authority_name="Australian Taxation Office (ATO)",
        tax_authority_website="https://www.ato.gov.au",
    ),
    # 6. SINGAPORE (SG) - IRAS
    "SG": CountryTaxProfile(
        country_code="SG",
        country_name="Singapore",
        currency_code="SGD",
        currency_symbol="S$",
        personal_allowance_or_standard_deduction=Decimal("0.0"),
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("20000.0"), Decimal("0.00")),
            (Decimal("20000.0"), Decimal("30000.0"), Decimal("0.02")),
            (Decimal("30000.0"), Decimal("40000.0"), Decimal("0.035")),
            (Decimal("40000.0"), Decimal("80000.0"), Decimal("0.07")),
            (Decimal("80000.0"), Decimal("120000.0"), Decimal("0.115")),
            (Decimal("120000.0"), Decimal("160000.0"), Decimal("0.15")),
            (Decimal("160000.0"), Decimal("200000.0"), Decimal("0.18")),
            (Decimal("200000.0"), Decimal("240000.0"), Decimal("0.19")),
            (Decimal("240000.0"), Decimal("280000.0"), Decimal("0.195")),
            (Decimal("280000.0"), Decimal("320000.0"), Decimal("0.20")),
            (Decimal("320000.0"), Decimal("500000.0"), Decimal("0.22")),
            (Decimal("500000.0"), Decimal("1000000.0"), Decimal("0.23")),
            (Decimal("1000000.0"), None, Decimal("0.24")),
        ],
        corporate_tax_standard_rate=Decimal(
            "0.17"
        ),  # 17% Flat Corporate Tax (with partial exemption)
        vat_gst_standard_rate=Decimal("0.09"),  # 9% GST (effective 2024)
        vat_registration_threshold=Decimal("1000000.0"),
        official_tax_authority_name="Inland Revenue Authority of Singapore (IRAS)",
        tax_authority_website="https://www.iras.gov.sg",
    ),
    # 7. GERMANY (DE) - BZSt
    "DE": CountryTaxProfile(
        country_code="DE",
        country_name="Germany",
        currency_code="EUR",
        currency_symbol="€",
        personal_allowance_or_standard_deduction=Decimal("11604.0"),  # Grundfreibetrag 2024
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("11604.0"), Decimal("0.00")),
            (Decimal("11604.0"), Decimal("66760.0"), Decimal("0.24")),  # Progressive Zone
            (Decimal("66760.0"), Decimal("277825.0"), Decimal("0.42")),
            (Decimal("277825.0"), None, Decimal("0.45")),  # Reichensteuer
        ],
        corporate_tax_standard_rate=Decimal(
            "0.15"
        ),  # 15% Körperschaftsteuer (+ 5.5% Soli + Gewerbesteuer)
        vat_gst_standard_rate=Decimal("0.19"),  # 19% MwSt / Umsatzsteuer
        vat_gst_reduced_rate=Decimal("0.07"),  # 7% reduced
        official_tax_authority_name="Bundeszentralamt für Steuern (BZSt)",
        tax_authority_website="https://www.bzst.de",
    ),
    # 8. SAUDI ARABIA (SA) - ZATCA
    "SA": CountryTaxProfile(
        country_code="SA",
        country_name="Saudi Arabia",
        currency_code="SAR",
        currency_symbol="SAR ",
        personal_allowance_or_standard_deduction=Decimal("0.0"),
        income_tax_slabs=[
            (
                Decimal("0.0"),
                None,
                Decimal("0.00"),
            ),  # 0% personal income tax for citizens/residents
        ],
        corporate_tax_standard_rate=Decimal(
            "0.20"
        ),  # 20% Income tax for foreign entities (or 2.5% Zakat for Saudi/GCC)
        vat_gst_standard_rate=Decimal("0.15"),  # 15% Standard VAT
        vat_registration_threshold=Decimal("375000.0"),
        official_tax_authority_name="Zakat, Tax and Customs Authority (ZATCA)",
        tax_authority_website="https://zatca.gov.sa",
    ),
    # 9. FRANCE (FR) - DGFiP
    "FR": CountryTaxProfile(
        country_code="FR",
        country_name="France",
        currency_code="EUR",
        currency_symbol="€",
        personal_allowance_or_standard_deduction=Decimal("11294.0"),
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("11294.0"), Decimal("0.00")),
            (Decimal("11294.0"), Decimal("28797.0"), Decimal("0.11")),
            (Decimal("28797.0"), Decimal("82341.0"), Decimal("0.30")),
            (Decimal("82341.0"), Decimal("177106.0"), Decimal("0.41")),
            (Decimal("177106.0"), None, Decimal("0.45")),
        ],
        corporate_tax_standard_rate=Decimal("0.25"),  # 25% (15% for PME < €42,500)
        vat_gst_standard_rate=Decimal("0.20"),  # 20% TVA
        vat_gst_reduced_rate=Decimal("0.055"),  # 5.5% reduced TVA
        official_tax_authority_name="Direction Générale des Finances Publiques (DGFiP)",
        tax_authority_website="https://www.impots.gouv.fr",
    ),
    # 10. NETHERLANDS (NL) - Belastingdienst
    "NL": CountryTaxProfile(
        country_code="NL",
        country_name="Netherlands",
        currency_code="EUR",
        currency_symbol="€",
        personal_allowance_or_standard_deduction=Decimal("0.0"),
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("75518.0"), Decimal("0.3697")),  # Box 1 Bracket 1 (2024)
            (Decimal("75518.0"), None, Decimal("0.4950")),  # Box 1 Bracket 2
        ],
        corporate_tax_standard_rate=Decimal("0.258"),  # 25.8% (>€200,000)
        corporate_tax_threshold=Decimal("200000.0"),
        corporate_tax_reduced_rate=Decimal("0.19"),  # 19% (<€200,000)
        vat_gst_standard_rate=Decimal("0.21"),  # 21% BTW
        vat_gst_reduced_rate=Decimal("0.09"),  # 9% BTW
        official_tax_authority_name="Belastingdienst",
        tax_authority_website="https://www.belastingdienst.nl",
    ),
    # 11. ITALY (IT) - Agenzia delle Entrate
    "IT": CountryTaxProfile(
        country_code="IT",
        country_name="Italy",
        currency_code="EUR",
        currency_symbol="€",
        personal_allowance_or_standard_deduction=Decimal("8500.0"),  # No tax area
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("28000.0"), Decimal("0.23")),  # 2024 3-bracket reform
            (Decimal("28000.0"), Decimal("50000.0"), Decimal("0.35")),
            (Decimal("50000.0"), None, Decimal("0.43")),
        ],
        corporate_tax_standard_rate=Decimal("0.24"),  # 24% IRES (+ 3.9% IRAP)
        vat_gst_standard_rate=Decimal("0.22"),  # 22% IVA
        vat_gst_reduced_rate=Decimal("0.10"),  # 10% IVA
        official_tax_authority_name="Agenzia delle Entrate",
        tax_authority_website="https://www.agenziaentrate.gov.it",
    ),
    # 12. SPAIN (ES) - Agencia Tributaria
    "ES": CountryTaxProfile(
        country_code="ES",
        country_name="Spain",
        currency_code="EUR",
        currency_symbol="€",
        personal_allowance_or_standard_deduction=Decimal("5550.0"),  # Mínimo personal
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("12450.0"), Decimal("0.19")),
            (Decimal("12450.0"), Decimal("20200.0"), Decimal("0.24")),
            (Decimal("20200.0"), Decimal("35200.0"), Decimal("0.30")),
            (Decimal("35200.0"), Decimal("60000.0"), Decimal("0.37")),
            (Decimal("60000.0"), Decimal("300000.0"), Decimal("0.45")),
            (Decimal("300000.0"), None, Decimal("0.47")),
        ],
        corporate_tax_standard_rate=Decimal("0.25"),  # 25% (15% new companies)
        vat_gst_standard_rate=Decimal("0.21"),  # 21% IVA
        vat_gst_reduced_rate=Decimal("0.10"),  # 10% IVA
        official_tax_authority_name="Agencia Estatal de Administración Tributaria (AEAT)",
        tax_authority_website="https://sede.agenciatributaria.gob.es",
    ),
    # 13. NEW ZEALAND (NZ) - Inland Revenue (IRD)
    "NZ": CountryTaxProfile(
        country_code="NZ",
        country_name="New Zealand",
        currency_code="NZD",
        currency_symbol="NZ$",
        personal_allowance_or_standard_deduction=Decimal("0.0"),
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("15600.0"), Decimal("0.105")),  # Budget 2024 adjusted
            (Decimal("15600.0"), Decimal("53500.0"), Decimal("0.175")),
            (Decimal("53500.0"), Decimal("78100.0"), Decimal("0.30")),
            (Decimal("78100.0"), Decimal("180000.0"), Decimal("0.33")),
            (Decimal("180000.0"), None, Decimal("0.39")),
        ],
        corporate_tax_standard_rate=Decimal("0.28"),  # 28% Company Tax
        vat_gst_standard_rate=Decimal("0.15"),  # 15% GST
        vat_registration_threshold=Decimal("60000.0"),
        official_tax_authority_name="Inland Revenue Department (IRD)",
        tax_authority_website="https://www.ird.govt.nz",
    ),
    # 14. JAPAN (JP) - National Tax Agency (NTA)
    "JP": CountryTaxProfile(
        country_code="JP",
        country_name="Japan",
        currency_code="JPY",
        currency_symbol="¥",
        personal_allowance_or_standard_deduction=Decimal("480000.0"),  # Basic exemption (¥480k)
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("1950000.0"), Decimal("0.05")),
            (Decimal("1950000.0"), Decimal("3300000.0"), Decimal("0.10")),
            (Decimal("3300000.0"), Decimal("6950000.0"), Decimal("0.20")),
            (Decimal("6950000.0"), Decimal("9000000.0"), Decimal("0.23")),
            (Decimal("9000000.0"), Decimal("18000000.0"), Decimal("0.33")),
            (Decimal("18000000.0"), Decimal("40000000.0"), Decimal("0.40")),
            (Decimal("40000000.0"), None, Decimal("0.45")),
        ],
        corporate_tax_standard_rate=Decimal("0.232"),  # 23.2% national corporate tax
        vat_gst_standard_rate=Decimal("0.10"),  # 10% Consumption Tax (8% food)
        vat_gst_reduced_rate=Decimal("0.08"),
        official_tax_authority_name="National Tax Agency (NTA)",
        tax_authority_website="https://www.nta.go.jp",
    ),
    # 15. SOUTH AFRICA (ZA) - SARS
    "ZA": CountryTaxProfile(
        country_code="ZA",
        country_name="South Africa",
        currency_code="ZAR",
        currency_symbol="R ",
        personal_allowance_or_standard_deduction=Decimal("95750.0"),  # Primary tax threshold 2024
        income_tax_slabs=[
            (Decimal("0.0"), Decimal("237100.0"), Decimal("0.18")),
            (Decimal("237100.0"), Decimal("370500.0"), Decimal("0.26")),
            (Decimal("370500.0"), Decimal("512800.0"), Decimal("0.31")),
            (Decimal("512800.0"), Decimal("673000.0"), Decimal("0.36")),
            (Decimal("673000.0"), Decimal("857900.0"), Decimal("0.39")),
            (Decimal("857900.0"), Decimal("1817000.0"), Decimal("0.41")),
            (Decimal("1817000.0"), None, Decimal("0.45")),
        ],
        corporate_tax_standard_rate=Decimal("0.27"),  # 27% Flat Corporate Tax
        vat_gst_standard_rate=Decimal("0.15"),  # 15% VAT
        vat_registration_threshold=Decimal("1000000.0"),
        official_tax_authority_name="South African Revenue Service (SARS)",
        tax_authority_website="https://www.sars.gov.za",
    ),
}


class GlobalTaxEngine:
    """Enterprise multi-jurisdiction calculation engine for global countries."""

    def get_country_profile(self, country_code: str) -> CountryTaxProfile | None:
        """Fetch statutory tax profile by 2-letter ISO country code."""
        return GLOBAL_COUNTRY_PACKS.get(country_code.upper())

    def list_supported_countries(self) -> list[CountryTaxProfile]:
        """List all supported global country packs."""
        return list(GLOBAL_COUNTRY_PACKS.values())

    def calculate(self, user_input: GlobalCalculationInput) -> GlobalCalculationResult:
        """Calculate personal income tax, corporate tax, or VAT for any supported country."""
        country = self.get_country_profile(user_input.country_code)
        if not country:
            raise ValueError(
                f"Country code '{user_input.country_code}' is not supported yet. "
                f"Supported: {', '.join(GLOBAL_COUNTRY_PACKS.keys())}"
            )

        gross = user_input.gross_income_or_revenue
        notes: list[str] = []
        slabs_breakdown: list[TaxSlabBreakdown] = []
        assumptions = [
            f"Tax year {user_input.tax_year} and rule pack {country.rule_version} selected.",
            f"Taxpayer type: {user_input.taxpayer_type}; residency: {user_input.residency}; entity: {user_input.entity_type}.",
        ]
        warnings = list(country.known_limitations)

        if user_input.tax_type == GlobalTaxType.INCOME_TAX:
            # Personal Income Tax
            deduction = (
                country.personal_allowance_or_standard_deduction
                + user_input.expenses_or_deductions
            )
            taxable = max(Decimal("0.0"), gross - deduction)

            total_tax = Decimal("0.0")
            rem = taxable
            for min_a, max_a, rate in country.income_tax_slabs:
                if rem <= min_a:
                    continue
                in_slab = min(rem, max_a) - min_a if max_a is not None else rem - min_a

                tax_in_slab = (in_slab * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_tax += tax_in_slab

                slabs_breakdown.append(
                    TaxSlabBreakdown(
                        min_amount=min_a,
                        max_amount=max_a,
                        rate=rate,
                        taxable_in_slab=in_slab,
                        tax_amount=tax_in_slab,
                    )
                )

            # Apply employee social security if applicable
            if country.employee_social_security_rate > 0:
                ss_tax = (gross * country.employee_social_security_rate).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                total_tax += ss_tax
                notes.append(
                    f"Employee social security / Medicare contribution: {country.currency_symbol}{ss_tax:,.2f}"
                )

            notes.append(
                f"Statutory personal allowance/deduction applied: {country.currency_symbol}{deduction:,.2f}"
            )

        elif user_input.tax_type == GlobalTaxType.CORPORATE_TAX:
            # Corporate Tax
            deduction = user_input.expenses_or_deductions
            taxable = max(Decimal("0.0"), gross - deduction)

            if country.corporate_tax_threshold > 0 and taxable <= country.corporate_tax_threshold:
                total_tax = (taxable * country.corporate_tax_reduced_rate).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                notes.append(
                    f"Small business/reduced rate applied ({country.corporate_tax_reduced_rate * 100:.1f}%) up to {country.currency_symbol}{country.corporate_tax_threshold:,.0f}"
                )
            else:
                total_tax = (taxable * country.corporate_tax_standard_rate).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

        elif user_input.tax_type == GlobalTaxType.VAT_GST:
            # Indirect VAT/GST
            deduction = Decimal("0.0")
            taxable = gross
            total_tax = (taxable * country.vat_gst_standard_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            notes.append(
                f"Standard VAT/GST rate of {country.vat_gst_standard_rate * 100:.1f}% applied."
            )

        else:
            deduction = Decimal("0.0")
            taxable = gross
            total_tax = Decimal("0.0")

        total_tax = total_tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        eff_rate = (
            ((total_tax / gross) * Decimal("100.0")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if gross > 0
            else Decimal("0.0")
        )
        net_after = max(Decimal("0.0"), gross - total_tax)

        return GlobalCalculationResult(
            country_code=country.country_code,
            country_name=country.country_name,
            currency_code=country.currency_code,
            currency_symbol=country.currency_symbol,
            tax_type=user_input.tax_type,
            gross_basis=gross,
            allowances_and_deductions=deduction,
            taxable_basis=taxable,
            calculated_tax=total_tax,
            effective_tax_rate_percent=eff_rate,
            net_after_tax=net_after,
            slabs_breakdown=slabs_breakdown,
            official_source_reference=f"{country.official_tax_authority_name} ({country.tax_authority_website})",
            notes=notes,
            tax_year=user_input.tax_year,
            rule_version=country.rule_version,
            taxpayer_type=user_input.taxpayer_type,
            assumptions=assumptions,
            warnings=warnings,
            confidence="moderate" if warnings else "deterministic",
            review_required=bool(warnings),
        )
