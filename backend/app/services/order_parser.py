import re
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Set, Tuple

from app.schemas.order import ParsedOrderItem, ParsedOrderResponse
from app.services.catalogue import (
    Product,
    find_product_by_alias,
    get_all_products,
    get_sorted_aliases,
    normalize_text,
)

# Supported spoken Hindi / Hinglish numerals and fraction words
QUANTITY_WORDS: Dict[str, float] = {
    # Integers
    "ek": 1.0,
    "एक": 1.0,
    "one": 1.0,
    "do": 2.0,
    "दो": 2.0,
    "two": 2.0,
    "teen": 3.0,
    "tin": 3.0,
    "तीन": 3.0,
    "three": 3.0,
    "chaar": 4.0,
    "char": 4.0,
    "चार": 4.0,
    "four": 4.0,
    "paanch": 5.0,
    "panch": 5.0,
    "पांच": 5.0,
    "पाँच": 5.0,
    "five": 5.0,
    "chhah": 6.0,
    "che": 6.0,
    "chhe": 6.0,
    "छह": 6.0,
    "छः": 6.0,
    "six": 6.0,
    "saat": 7.0,
    "सात": 7.0,
    "seven": 7.0,
    "aath": 8.0,
    "आठ": 8.0,
    "eight": 8.0,
    "nau": 9.0,
    "नौ": 9.0,
    "nine": 9.0,
    "das": 10.0,
    "दस": 10.0,
    "ten": 10.0,
    "gyarah": 11.0,
    "ग्यारह": 11.0,
    "eleven": 11.0,
    "barah": 12.0,
    "बारह": 12.0,
    "twelve": 12.0,

    # Fractional words
    "aadha": 0.5,
    "aadhi": 0.5,
    "adha": 0.5,
    "adhi": 0.5,
    "आधा": 0.5,
    "आधी": 0.5,
    "half": 0.5,
    "dedh": 1.5,
    "deydh": 1.5,
    "डेढ़": 1.5,
    "डेढ": 1.5,
    "dhai": 2.5,
    "dhaai": 2.5,
    "ढाई": 2.5,
    "sawa": 1.25,
    "sawai": 1.25,
    "सवा": 1.25,
    "paune": 0.75,
    "pauna": 0.75,
    "पौने": 0.75,
}

# Unit variations mapped to canonical units
UNIT_MAPPINGS: Dict[str, str] = {
    # Weight
    "kg": "kg",
    "kilo": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "kilos": "kg",
    "किलो": "kg",
    "किग्रा": "kg",
    "g": "g",
    "gm": "g",
    "gms": "g",
    "gram": "g",
    "grams": "g",
    "gramme": "g",
    "ग्राम": "g",
    "ग्रा": "g",

    # Volume
    "litre": "litre",
    "litres": "litre",
    "liter": "litre",
    "liters": "litre",
    "ltr": "litre",
    "l": "litre",
    "लीटर": "litre",
    "ली": "litre",
    "ml": "ml",
    "millilitre": "ml",
    "milliliter": "ml",
    "मिली": "ml",

    # Packaging / Countable
    "packet": "packet",
    "packets": "packet",
    "pack": "packet",
    "packs": "packet",
    "pouch": "packet",
    "pouches": "packet",
    "पैकेट": "packet",
    "पैक": "packet",
    "piece": "piece",
    "pieces": "piece",
    "item": "piece",
    "items": "piece",
    "pc": "piece",
    "pcs": "piece",
    "nag": "piece",
    "nug": "piece",
    "नग": "piece",
    "पीस": "piece",
    "dozen": "dozen",
    "dozens": "dozen",
    "darjan": "dozen",
    "दर्जन": "dozen",
    "bottle": "bottle",
    "bottles": "bottle",
    "बोतल": "bottle",
    "tin": "tin",
    "tins": "tin",
    "tray": "tray",
    "trays": "tray",
    "cup": "cup",
    "bar": "piece",
}

# Vague words requiring clarification
VAGUE_QUANTITY_PATTERNS = [
    r"\bthoda\s+sa\b",
    r"\bthodi\s+si\b",
    r"\bthode\s+se\b",
    r"\bthoda\b",
    r"\bthodi\b",
    r"\bthode\b",
    r"\bथोड़ा\s+सा\b",
    r"\bथोड़ी\s+सी\b",
    r"\bथोड़ा\b",
    r"\bथोड़ी\b",
    r"\bkuchh?\b",
    r"\bकुछ\b",
    r"\bkam\s+se\s+kam\b",
    r"\bkam\b",
    r"\bjyada\b",
    r"\bbohot\b",
    r"\bbahut\b",
]

# Conversational fillers and verbs to remove from parsing tokens
FILLER_PATTERNS = [
    r"\bbhaiya\s+ji\b",
    r"\bbhaiya\b",
    r"\bbhaiji\b",
    r"\bbhai\b",
    r"\barre\s+bhaiya\b",
    r"\bare\s+bhaiya\b",
    r"\bsunna\b",
    r"\bsuno\b",
    r"\bnamaste\b",
    r"\bhello\b",
    r"\bji\b",
    r"\bbhej\s+dena\b",
    r"\bbhej\s+dijiye\b",
    r"\bbhej\s+do\b",
    r"\bbhejo\b",
    r"\bde\s+dena\b",
    r"\bde\s+dijiye\b",
    r"\bde\s+do\b",
    r"\bpack\s+kar\s+dena\b",
    r"\bpack\s+kar\s+do\b",
    r"\bkar\s+dena\b",
    r"\bkar\s+do\b",
    r"\ble\s+aana\b",
    r"\ble\s+aao\b",
    r"\bla\s+do\b",
    r"\bchahiye\s+tha\b",
    r"\bchahiye\b",
    r"\bkripya\b",
    r"\bplease\b",
    r"\burgent\b",
    r"\bjaldi\b",
    r"\bghar\s+pe\b",
    r"\bdukaan\s+pe\b",
]


def clean_filler_text(text: str) -> str:
    """Strip out common conversational greetings, politeness markers, and order request verbs."""
    cleaned = text
    for pattern in FILLER_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE | re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def check_for_vague_quantity(text: str) -> Optional[str]:
    """Check if the text contains vague quantity words such as 'thoda' or 'kuch'."""
    for pattern in VAGUE_QUANTITY_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.UNICODE)
        if match:
            return match.group(0).strip()
    return None


def parse_numeric_or_word_quantity(token: str) -> Optional[float]:
    """Parse a single token or expression into a float quantity."""
    norm = token.strip().lower()
    if norm in QUANTITY_WORDS:
        return QUANTITY_WORDS[norm]

    # Try numeric parsing (including integer or decimal like "1.5", "500", "0.5")
    try:
        val = Decimal(norm)
        if val > 0:
            return float(val)
    except (InvalidOperation, ValueError):
        pass

    return None


def split_into_candidate_clauses(transcript: str) -> List[str]:
    """Split a transcript into clauses using Hindi, Hinglish and English conjunctions."""

    text = transcript.strip()

    # Replace punctuation with commas, preserving decimal quantities such as 1.5.
    text = re.sub(r"(?<!\d)\.|\.(?!\d)", ",", text)
    text = re.sub(r"[,;!?\n\r]+", ",", text)

    # Use Unicode-aware word boundaries for Hindi and English conjunctions.
    delimiter_pattern = (
        r",+|"
        r"(?<!\w)aur\s+haan(?!\w)|"
        r"(?<!\w)aur\s+sath\s+mein(?!\w)|"
        r"(?<!\w)aur(?!\w)|"
        r"(?<!\w)और(?!\w)|"
        r"(?<!\w)and(?!\w)|"
        r"(?<!\w)tatha(?!\w)|"
        r"(?<!\w)तथा(?!\w)|"
        r"(?<!\w)evam(?!\w)|"
        r"(?<!\w)एवं(?!\w)|"
        r"(?<!\w)plus(?!\w)"
    )

    raw_clauses = re.split(
        delimiter_pattern,
        text,
        flags=re.IGNORECASE | re.UNICODE,
    )

    refined_clauses: List[str] = []

    for clause in raw_clauses:
        clause = clause.strip()

        if not clause:
            continue

        refined_clauses.extend(_split_concatenated_items(clause))

    return refined_clauses


def _split_concatenated_items(clause: str) -> List[str]:
    """Split clauses containing multiple catalogue products and quantities."""

    sorted_aliases = get_sorted_aliases()
    norm_clause = normalize_text(clause)

    occurrences: List[Tuple[int, int, str, Product]] = []

    # Find all product aliases using whitespace boundaries.
    for alias, product in sorted_aliases:
        pattern = r"(?<!\S)" + re.escape(alias) + r"(?!\S)"

        for match in re.finditer(
            pattern,
            norm_clause,
            flags=re.IGNORECASE | re.UNICODE,
        ):
            start, end = match.span()

            # Avoid overlapping aliases.
            if not any(
                old_start <= start < old_end
                or old_start < end <= old_end
                for old_start, old_end, _, _ in occurrences
            ):
                occurrences.append((start, end, alias, product))

    if len(occurrences) <= 1:
        return [norm_clause] if norm_clause else []

    occurrences.sort(key=lambda item: item[0])

    slices: List[str] = []
    last_idx = 0

    for i in range(len(occurrences) - 1):
        current = occurrences[i]
        following = occurrences[i + 1]

        between_text = norm_clause[current[1]:following[0]]

        split_point = -1

        # Locate the next item's quantity directly by token position.
        # This works for Devanagari words such as एक, दो and तीन.
        for token_match in re.finditer(r"\S+", between_text):
            word = token_match.group(0)

            if (
                parse_numeric_or_word_quantity(word) is not None
                or check_for_vague_quantity(word) is not None
            ):
                split_point = current[1] + token_match.start()
                break

        if split_point > last_idx:
            slices.append(norm_clause[last_idx:split_point].strip())
            last_idx = split_point
        else:
            # If no next quantity exists, retain the next product as
            # a separate clause so missing quantity can be clarified.
            split_point = following[0]
            slices.append(norm_clause[last_idx:split_point].strip())
            last_idx = split_point

    if last_idx < len(norm_clause):
        slices.append(norm_clause[last_idx:].strip())

    return [item for item in slices if item]

    # Sort occurrences by start position
    occurrences.sort(key=lambda x: x[0])

    # If multiple products, look for quantity boundaries before the 2nd..nth product
    # to slice the original clause cleanly
    slices: List[str] = []
    last_idx = 0

    for i in range(len(occurrences) - 1):
        curr_occ = occurrences[i]
        next_occ = occurrences[i + 1]

        # Region between current product end and next product start
        between_text = norm_clause[curr_occ[1]:next_occ[0]].strip()

        # Check if between_text contains quantity words/digits for the next product
        # Find where the next item begins (looking for number/quantity word)
        words_between = between_text.split()
        split_point = -1

        for w_idx, word in enumerate(words_between):
            if parse_numeric_or_word_quantity(word) is not None or check_for_vague_quantity(word):
                # Found start of next quantity
                # Map to index in clause
                pattern = r"\b" + re.escape(word) + r"\b"
                m = re.search(pattern, clause[curr_occ[1]:], flags=re.IGNORECASE | re.UNICODE)
                if m:
                    split_point = curr_occ[1] + m.start()
                    break

        if split_point != -1 and split_point > last_idx:
            slices.append(clause[last_idx:split_point].strip())
            last_idx = split_point
        else:
            # Fallback: slice just before next product if no explicit quantity found
            split_point = next_occ[0]
            slices.append(clause[last_idx:split_point].strip())
            last_idx = split_point

    if last_idx < len(clause):
        slices.append(clause[last_idx:].strip())

    return [s for s in slices if s]


def _extract_quantity_and_unit(tokens: List[str]) -> Tuple[Optional[float], Optional[str], List[str]]:
    """Scan tokens to extract a recognized quantity and unit.

    Returns (quantity, unit, remaining_tokens).
    """
    quantity: Optional[float] = None
    unit: Optional[str] = None
    used_indices: Set[int] = set()

    # Pass 1: Look for combined fraction patterns like "do aur aadha" -> 2.5
    for i in range(len(tokens) - 2):
        if tokens[i + 1].lower() in ["aur", "and"] and tokens[i].lower() in QUANTITY_WORDS and tokens[i + 2].lower() in QUANTITY_WORDS:
            base_q = QUANTITY_WORDS[tokens[i].lower()]
            frac_q = QUANTITY_WORDS[tokens[i + 2].lower()]
            quantity = base_q + frac_q
            used_indices.update([i, i + 1, i + 2])
            break

    # Pass 2: If no combined quantity, look for single quantity word or number
    if quantity is None:
        for i, token in enumerate(tokens):
            q_val = parse_numeric_or_word_quantity(token)
            if q_val is not None:
                quantity = q_val
                used_indices.add(i)
                break

    # Pass 3: Look for unit
    for i, token in enumerate(tokens):
        if i in used_indices:
            continue
        cleaned_tok = token.lower().strip()
        if cleaned_tok in UNIT_MAPPINGS:
            unit = UNIT_MAPPINGS[cleaned_tok]
            used_indices.add(i)
            break

    remaining = [tok for i, tok in enumerate(tokens) if i not in used_indices]
    return quantity, unit, remaining


def parse_order_transcript(transcript: str) -> ParsedOrderResponse:
    """Deterministically parse a Hindi / Hinglish voice order transcript into structured line items,

    identifying quantities, units, and ambiguities without external AI calls or hallucination.
    """
    if not transcript or not transcript.strip():
        return ParsedOrderResponse(
            items=[],
            status="needs_clarification",
            clarification_required=True,
            clarification_message="Empty order transcript received. Please speak or enter grocery items.",
            unsupported_products=[],
        )

    # Clean overall transcript and bound length
    clean_full_transcript = transcript.strip()
    if len(clean_full_transcript) > 1000:
        return ParsedOrderResponse(
            items=[],
            status="needs_clarification",
            clarification_required=True,
            clarification_message="Order transcript exceeds maximum supported length (1000 characters).",
            unsupported_products=[],
        )

    clauses = split_into_candidate_clauses(clean_full_transcript)
    if not clauses:
        return ParsedOrderResponse(
            items=[],
            status="needs_clarification",
            clarification_required=True,
            clarification_message="No grocery items detected in the transcript.",
            unsupported_products=[],
        )

    extracted_items: List[ParsedOrderItem] = []
    unsupported_products: List[str] = []
    clarification_reasons: List[str] = []

    sorted_aliases = get_sorted_aliases()

    for raw_clause in clauses:
        # Strip conversational filler words
        filtered_clause = clean_filler_text(raw_clause)
        if not filtered_clause:
            continue

        norm_clause = normalize_text(filtered_clause)
        if not norm_clause:
            continue

        # Check for vague quantities in this clause
        vague_word = check_for_vague_quantity(filtered_clause)

        # Match product from catalogue (greedy longest alias match)
        matched_product: Optional[Product] = None
        matched_alias: Optional[str] = None

        for alias, product in sorted_aliases:
            pattern = r"(?<!\S)" + re.escape(alias) + r"(?!\S)"
            if re.search(pattern, norm_clause, flags=re.IGNORECASE | re.UNICODE):
                matched_product = product
                matched_alias = alias
                break

        if matched_product and matched_alias:
            # Remove the product alias from clause to isolate quantity and unit
            alias_pattern = r"(?<!\S)" + re.escape(matched_alias) + r"(?!\S)"
            clause_without_product = re.sub(alias_pattern, " ", norm_clause, count=1, flags=re.IGNORECASE | re.UNICODE)
            tokens = clause_without_product.split()

            # Handle vague quantity detected
            if vague_word:
                clarification_reasons.append(
                    f"Vague quantity '{vague_word}' for '{matched_product.name}'. Please specify an exact quantity (e.g. 1 kg or 1 packet)."
                )
                continue

            quantity, unit, _ = _extract_quantity_and_unit(tokens)

            # Check missing quantity
            if quantity is None:
                clarification_reasons.append(
                    f"Missing quantity for '{matched_product.name}'. Please specify how much is needed (e.g. 1 kg, 500 g)."
                )
                continue

          
            
                # Check unit handling
            if unit is None:
                    # Use the default unit for countable products
                    if (
                        matched_product.default_unit in ("packet", "piece")
                        and quantity.is_integer()
                    ):
                        unit = matched_product.default_unit
                    else:
                        clarification_reasons.append(
                            f"Missing or ambiguous unit for '{matched_product.name}' "
                            f"with quantity {quantity}. "
                            f"Did you mean {quantity} {matched_product.default_unit} or packets?"
                        )
                        continue

                # Validate unit compatibility with product
                # IMPORTANT: This must be outside the `if unit is None` block.
            unit_is_valid = unit in matched_product.allowed_units

            if not unit_is_valid:
                    allowed_str = ", ".join(matched_product.allowed_units)
                    clarification_reasons.append(
                        f"Unit '{unit}' is not standard for '{matched_product.name}'. "
                        f"Requested quantity: {quantity} {unit}. "
                        f"Supported units: {allowed_str}. Please correct the unit."
                    )

                # Preserve the product even if its unit needs clarification.
            extracted_items.append(
                    ParsedOrderItem(
                        product_id=matched_product.product_id,
                        name=matched_product.name,
                        quantity=round(quantity, 3),
                        unit=unit,
                        unit_price=matched_product.typical_unit_price,
                    )
                )


        else:
            # No catalogue product matched in this clause
            # Check if this clause contains an attempted order (e.g. "do kilo seb", "500 gram paneer" if unmapped)
            tokens = norm_clause.split()
            quantity, unit, remaining = _extract_quantity_and_unit(tokens)

            # An unsupported product is only identified if order intent is present:
            # (i.e., a quantity, unit, or vague quantity expression was specified)
            has_order_intent = (quantity is not None) or (unit is not None) or (vague_word is not None)

            # Clean any remaining conversational verbs
            cand_terms = [t for t in remaining if len(t) > 1 and t not in ["aur", "ka", "ki", "ke", "se", "ko"]]
            if cand_terms and has_order_intent:
                potential_product = " ".join(cand_terms)
                if potential_product not in unsupported_products:
                    unsupported_products.append(potential_product)
                    clarification_reasons.append(
                        f"Product '{potential_product}' is not in the Kirana catalogue."
                    )

    # Compile final parsed order status
    if unsupported_products or clarification_reasons:
        clarification_msg = " ".join(clarification_reasons)
        return ParsedOrderResponse(
            items=extracted_items,
            status="needs_clarification",
            clarification_required=True,
            clarification_message=clarification_msg,
            unsupported_products=unsupported_products,
        )

    if not extracted_items:
        return ParsedOrderResponse(
            items=[],
            status="needs_clarification",
            clarification_required=True,
            clarification_message="No grocery items detected in the transcript. Please state items and quantities.",
            unsupported_products=[],
        )

    # All items parsed cleanly and unambiguously
    return ParsedOrderResponse(
        items=extracted_items,
        status="ready_for_review",
        clarification_required=False,
        clarification_message=None,
        unsupported_products=[],
    )
