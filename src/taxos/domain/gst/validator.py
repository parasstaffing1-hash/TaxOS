"""India GSTIN Validator (Luhn Mod-36 Algorithm) & HSN/SAC Directory."""

from __future__ import annotations

import re
from decimal import Decimal

from taxos.domain.gst.models import GSTINValidationResult, HSNCodeInfo

GST_STATE_CODES: dict[str, str] = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman and Diu",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh (New)",
    "38": "Ladakh",
    "97": "Other Territory",
    "99": "Centre Jurisdiction",
}
GSTIN_LENGTH = 15
GSTIN_CHECKSUM_INDEX = 14
INITIAL_CHECKSUM_FACTOR = 2
ALTERNATE_CHECKSUM_FACTOR = 1

# Master HSN/SAC Directory for Goods & Services
MASTER_HSN_SAC_DATABASE: list[HSNCodeInfo] = [
    HSNCodeInfo(
        code="998311",
        description="Management consulting and management services",
        standard_gst_rate=Decimal("0.18"),
        category="Services",
    ),
    HSNCodeInfo(
        code="998313",
        description="Information technology (IT) design and development services / Software",
        standard_gst_rate=Decimal("0.18"),
        category="Services",
    ),
    HSNCodeInfo(
        code="998314",
        description="Information technology (IT) infrastructure and network management services",
        standard_gst_rate=Decimal("0.18"),
        category="Services",
    ),
    HSNCodeInfo(
        code="998222",
        description="Accounting, auditing and bookkeeping services",
        standard_gst_rate=Decimal("0.18"),
        category="Services",
    ),
    HSNCodeInfo(
        code="998211",
        description="Legal advisory and representation services",
        standard_gst_rate=Decimal("0.18"),
        category="Services",
    ),
    HSNCodeInfo(
        code="997212",
        description="Renting of residential property (commercial use)",
        standard_gst_rate=Decimal("0.18"),
        category="Services",
    ),
    HSNCodeInfo(
        code="996331",
        description="Restaurant and food takeaway services (Non-AC/AC)",
        standard_gst_rate=Decimal("0.05"),
        category="Services",
    ),
    HSNCodeInfo(
        code="8471",
        description="Automatic data processing machines, computers, laptops and micro-computers",
        standard_gst_rate=Decimal("0.18"),
        category="Goods",
    ),
    HSNCodeInfo(
        code="8517",
        description="Smartphones, mobile phones and telecommunication apparatus",
        standard_gst_rate=Decimal("0.18"),
        category="Goods",
    ),
    HSNCodeInfo(
        code="8703",
        description="Motor cars and vehicles for transport of persons",
        standard_gst_rate=Decimal("0.28"),
        category="Goods",
        compensation_cess_rate=Decimal("0.15"),
    ),
    HSNCodeInfo(
        code="0401",
        description="Fresh milk and pasteurised milk (unbranded)",
        standard_gst_rate=Decimal("0.00"),
        category="Goods",
    ),
    HSNCodeInfo(
        code="1006",
        description="Rice (pre-packaged and labelled)",
        standard_gst_rate=Decimal("0.05"),
        category="Goods",
    ),
    HSNCodeInfo(
        code="3004",
        description="Medicaments consisting of mixed or unmixed products for therapeutic use",
        standard_gst_rate=Decimal("0.12"),
        category="Goods",
    ),
    HSNCodeInfo(
        code="6109",
        description="T-shirts, singlets and other vests, knitted or crocheted (<₹1,000)",
        standard_gst_rate=Decimal("0.05"),
        category="Goods",
    ),
]

# Character mapping for GSTIN Luhn Mod-36 algorithm
GST_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class IndiaGSTValidator:
    """Validator for GSTIN, State Codes, and HSN/SAC codes."""

    GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

    @classmethod
    def validate_gstin(cls, gstin: str) -> GSTINValidationResult:
        """Validate a 15-character GSTIN format, state code, PAN integrity, and Luhn Mod-36 checksum."""
        clean_gstin = gstin.strip().upper()

        if len(clean_gstin) != GSTIN_LENGTH:
            return GSTINValidationResult(
                gstin=clean_gstin,
                is_valid=False,
                error_message=f"GSTIN must be exactly 15 characters long (got {len(clean_gstin)}).",
            )

        if not cls.GSTIN_REGEX.match(clean_gstin):
            return GSTINValidationResult(
                gstin=clean_gstin,
                is_valid=False,
                error_message="Invalid GSTIN format. Expected format: 2-digit state code + 10-char PAN + 1 entity digit + 'Z' + 1 checksum character.",
            )

        state_code = clean_gstin[:2]
        state_name = GST_STATE_CODES.get(state_code)
        if not state_name:
            return GSTINValidationResult(
                gstin=clean_gstin,
                is_valid=False,
                state_code=state_code,
                error_message=f"Invalid state code '{state_code}'. Must be between 01 and 38.",
            )

        pan = clean_gstin[2:12]
        entity_code = clean_gstin[12]

        # Verify Luhn Mod-36 Checksum (15th character)
        is_checksum_valid = cls._verify_checksum(clean_gstin)

        if not is_checksum_valid:
            return GSTINValidationResult(
                gstin=clean_gstin,
                is_valid=False,
                state_code=state_code,
                state_name=state_name,
                pan=pan,
                entity_code=entity_code,
                checksum_valid=False,
                error_message="GSTIN format is syntactically valid, but checksum verification failed (15th digit mismatch).",
            )

        return GSTINValidationResult(
            gstin=clean_gstin,
            is_valid=True,
            state_code=state_code,
            state_name=state_name,
            pan=pan,
            entity_code=entity_code,
            checksum_valid=True,
        )

    @classmethod
    def _verify_checksum(cls, gstin: str) -> bool:
        """Compute Luhn Mod-36 checksum over the first 14 characters and compare to 15th."""
        total = 0
        factor = INITIAL_CHECKSUM_FACTOR

        for char in reversed(gstin[:GSTIN_CHECKSUM_INDEX]):
            val = GST_CHARS.index(char)
            code_point = val * factor
            # Sum quotient and remainder of division by 36
            digit_sum = (code_point // 36) + (code_point % 36)
            total += digit_sum
            factor = (
                ALTERNATE_CHECKSUM_FACTOR
                if factor == INITIAL_CHECKSUM_FACTOR
                else INITIAL_CHECKSUM_FACTOR
            )

        remainder = total % 36
        check_code_point = (36 - remainder) % 36
        expected_char = GST_CHARS[check_code_point]

        return gstin[GSTIN_CHECKSUM_INDEX] == expected_char

    @classmethod
    def search_hsn_sac(cls, query: str) -> list[HSNCodeInfo]:
        """Search HSN and SAC directory by code or keyword."""
        q = query.lower().strip()
        return [
            item
            for item in MASTER_HSN_SAC_DATABASE
            if q in item.code.lower()
            or q in item.description.lower()
            or q in item.category.lower()
        ]
