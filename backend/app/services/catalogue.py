import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Product:
    """Represents a standardized grocery item in the Kirana catalogue."""
    product_id: str
    name: str
    category: str
    aliases: Tuple[str, ...]
    allowed_units: Tuple[str, ...]
    default_unit: str
    typical_unit_price: Optional[float] = None


# Predefined Indian grocery catalogue tailored for neighborhood Kirana stores
_PRODUCTS: List[Product] = [
    # --- Staples ---
    Product(
        product_id="atta",
        name="Atta",
        category="Staples",
        aliases=(
            "atta", "aata", "gehu ka atta", "gehun ka aata", "wheat flour",
            "गेहूं का आटा", "गेहू का आटा", "आटा", "आता"
        ),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=45.0,
    ),
    Product(
        product_id="rice",
        name="Rice",
        category="Staples",
        aliases=(
            "rice", "chawal", "chaawal", "basmati", "basmati chawal", "pulao chawal",
            "चावल", "बासमती चावल", "चांवल"
        ),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=60.0,
    ),
    Product(
        product_id="maida",
        name="Maida",
        category="Staples",
        aliases=("maida", "all purpose flour", "मैदा"),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=40.0,
    ),
    Product(
        product_id="suji",
        name="Suji",
        category="Staples",
        aliases=("suji", "sooji", "rawa", "semolina", "सूजी", "रवा"),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=50.0,
    ),
    Product(
        product_id="besan",
        name="Besan",
        category="Staples",
        aliases=("besan", "gram flour", "chana besan", "बेसन"),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=80.0,
    ),

    # --- Dairy ---
    Product(
        product_id="milk",
        name="Milk",
        category="Dairy",
        aliases=(
            "milk", "doodh", "dudh", "amul doodh", "taaza", "gold",
            "दूध", "मिल्क", "दुध"
        ),
        allowed_units=("litre", "ml", "packet"),
        default_unit="litre",
        typical_unit_price=33.0,  # per 500ml or ~66/litre
    ),
    Product(
        product_id="dahi",
        name="Dahi",
        category="Dairy",
        aliases=("dahi", "curd", "yogurt", "दही"),
        allowed_units=("kg", "g", "packet", "cup"),
        default_unit="packet",
        typical_unit_price=35.0,
    ),
    Product(
        product_id="paneer",
        name="Paneer",
        category="Dairy",
        aliases=("paneer", "cottage cheese", "पनीर"),
        allowed_units=("kg", "g", "packet"),
        default_unit="g",
        typical_unit_price=90.0,  # 200g pack
    ),
    Product(
        product_id="butter",
        name="Butter",
        category="Dairy",
        aliases=("butter", "makkhan", "makhan", "मक्खन", "बटर"),
        allowed_units=("packet", "g"),
        default_unit="packet",
        typical_unit_price=58.0,
    ),
    Product(
        product_id="ghee",
        name="Ghee",
        category="Dairy",
        aliases=("ghee", "ghi", "desi ghee", "घी", "देसी घी"),
        allowed_units=("litre", "ml", "kg", "g", "packet", "tin"),
        default_unit="litre",
        typical_unit_price=650.0,
    ),

    # --- Pulses (Dals) ---
    Product(
        product_id="arhar_dal",
        name="Arhar Dal",
        category="Pulses",
        aliases=(
            "arhar dal", "arhar", "toor dal", "tur dal", "tuar dal", "toor",
            "अरहर दाल", "तूर दाल", "अरहर"
        ),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=160.0,
    ),
    Product(
        product_id="moong_dal",
        name="Moong Dal",
        category="Pulses",
        aliases=(
            "moong dal", "mung dal", "moong dhuli", "moong chilka", "moong",
            "मूंग दाल", "मूंग"
        ),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=120.0,
    ),
    Product(
        product_id="masoor_dal",
        name="Masoor Dal",
        category="Pulses",
        aliases=(
            "masoor dal", "masur dal", "malka masoor", "masoor",
            "मसूर दाल", "मसूर"
        ),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=110.0,
    ),
    Product(
        product_id="chana_dal",
        name="Chana Dal",
        category="Pulses",
        aliases=("chana dal", "chana", "चना दाल", "चना"),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=95.0,
    ),
    Product(
        product_id="rajma",
        name="Rajma",
        category="Pulses",
        aliases=("rajma", "kidney beans", "chitra rajma", "राजमा"),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=140.0,
    ),
    Product(
        product_id="chole",
        name="Chole",
        category="Pulses",
        aliases=("chole", "kabuli chana", "white chana", "safed chana", "काबुली चना", "छोले"),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=130.0,
    ),

    # --- Spices & Seasonings ---
    Product(
        product_id="salt",
        name="Salt",
        category="Spices",
        aliases=("salt", "namak", "tata salt", "safed namak", "नमक"),
        allowed_units=("kg", "packet"),
        default_unit="packet",
        typical_unit_price=28.0,
    ),
    Product(
        product_id="haldi",
        name="Haldi",
        category="Spices",
        aliases=("haldi", "turmeric", "haldi powder", "हल्दी", "हल्दी पाउडर"),
        allowed_units=("g", "kg", "packet"),
        default_unit="g",
        typical_unit_price=40.0,
    ),
    Product(
        product_id="mirch",
        name="Red Chilli Powder",
        category="Spices",
        aliases=(
            "mirch", "lal mirch", "red chilli", "red chili", "chilli powder",
            "लाल मिर्च", "मिर्च", "मिर्ची"
        ),
        allowed_units=("g", "kg", "packet"),
        default_unit="g",
        typical_unit_price=55.0,
    ),
    Product(
        product_id="dhaniya",
        name="Coriander Powder",
        category="Spices",
        aliases=(
            "dhaniya", "dhaniya powder", "coriander powder", "धनिया", "धनिया पाउडर"
        ),
        allowed_units=("g", "kg", "packet"),
        default_unit="g",
        typical_unit_price=45.0,
    ),
    Product(
        product_id="jeera",
        name="Jeera",
        category="Spices",
        aliases=("jeera", "cumin", "cumin seeds", "जीरा"),
        allowed_units=("g", "kg", "packet"),
        default_unit="g",
        typical_unit_price=70.0,
    ),

    # --- Edible Oils ---
    Product(
        product_id="mustard_oil",
        name="Mustard Oil",
        category="Oils",
        aliases=(
            "mustard oil", "sarson ka tel", "sarson tel", "sarso tel", "kachi ghani",
            "सरसों का तेल", "सरसों तेल", "सरसो तेल"
        ),
        allowed_units=("litre", "ml", "bottle", "packet", "pouch"),
        default_unit="litre",
        typical_unit_price=160.0,
    ),
    Product(
        product_id="refined_oil",
        name="Refined Oil",
        category="Oils",
        aliases=(
            "refined oil", "refined tel", "vegetable oil", "fortune refined",
            "रिफाइंड तेल", "रिफाइंड"
        ),
        allowed_units=("litre", "ml", "packet", "pouch", "bottle"),
        default_unit="litre",
        typical_unit_price=145.0,
    ),
    Product(
        product_id="sunflower_oil",
        name="Sunflower Oil",
        category="Oils",
        aliases=("sunflower oil", "surajmukhi tel", "सनफ्लावर तेल"),
        allowed_units=("litre", "ml", "packet", "bottle"),
        default_unit="litre",
        typical_unit_price=155.0,
    ),

    # --- Household Essentials ---
    Product(
        product_id="soap",
        name="Soap",
        category="Household",
        aliases=("soap", "sabun", "bathing soap", "lifebuoy", "lux", "dettol sabun", "साबुन"),
        allowed_units=("piece", "packet", "bar"),
        default_unit="piece",
        typical_unit_price=35.0,
    ),
    Product(
        product_id="detergent",
        name="Detergent",
        category="Household",
        aliases=(
            "detergent", "surf", "washing powder", "tide", "surf excel", "ariel", "ghadi",
            "सर्फ", "डिटर्जेंट", "वाशिंग पाउडर"
        ),
        allowed_units=("kg", "packet"),
        default_unit="packet",
        typical_unit_price=110.0,
    ),
    Product(
        product_id="dishwash",
        name="Dishwash Soap",
        category="Household",
        aliases=(
            "dishwash", "vim bar", "dishwashing liquid", "bartan ka sabun", "vim",
            "विम बार", "बर्तन का साबुन"
        ),
        allowed_units=("piece", "packet", "bottle"),
        default_unit="piece",
        typical_unit_price=20.0,
    ),

    # --- Snacks & Packaged Goods ---
    Product(
        product_id="biscuits",
        name="Biscuits",
        category="Packaged Goods",
        aliases=(
            "biscuit", "biscuits", "biskut", "parle g", "good day", "marie gold",
            "बिस्कुट", "बिस्किट"
        ),
        allowed_units=("packet", "piece"),
        default_unit="packet",
        typical_unit_price=20.0,
    ),
    Product(
        product_id="bread",
        name="Bread",
        category="Packaged Goods",
        aliases=("bread", "double roti", "white bread", "brown bread", "ब्रेड", "डबल रोटी"),
        allowed_units=("packet", "piece"),
        default_unit="packet",
        typical_unit_price=40.0,
    ),
    Product(
        product_id="tea",
        name="Tea",
        category="Packaged Goods",
        aliases=("tea", "chai", "chai patti", "chaye", "taj mahal tea", "red label", "चाय", "चाय पत्ती"),
        allowed_units=("g", "kg", "packet"),
        default_unit="packet",
        typical_unit_price=120.0,  # 250g pack
    ),
    Product(
        product_id="sugar",
        name="Sugar",
        category="Packaged Goods",
        aliases=("sugar", "cheeni", "chini", "shakkar", "khand", "चीनी", "शक्कर"),
        allowed_units=("kg", "g", "packet"),
        default_unit="kg",
        typical_unit_price=46.0,
    ),
    Product(
        product_id="noodles",
        name="Noodles",
        category="Packaged Goods",
        aliases=("noodles", "maggi", "noodle", "instant noodles", "मैगी", "नूडल्स"),
        allowed_units=("packet", "piece"),
        default_unit="packet",
        typical_unit_price=14.0,
    ),
    Product(
        product_id="eggs",
        name="Eggs",
        category="Staples",
        aliases=("egg", "eggs", "anda", "ande", "अंडे", "अंडा"),
        allowed_units=("piece", "dozen", "tray"),
        default_unit="piece",
        typical_unit_price=7.0,
    ),
]


def normalize_text(text: str) -> str:
    """Normalize text by lowering case, removing punctuation, and collapsing whitespace,

    while safely preserving numbers with decimal points (e.g. 1.5, 2.5).
    """
    if not text:
        return ""
    # Protect decimal dots between digits so '1.5' does not become '1 5'
    protected = re.sub(r"(?<=\d)\.(?=\d)", "__DEC__", text.lower())
    # Retain Hindi characters (Unicode range \u0900-\u097F), alphanumeric, and spaces
    cleaned = re.sub(r"[^\w\s\u0900-\u097F]", " ", protected, flags=re.UNICODE)
    restored = cleaned.replace("__DEC__", ".")
    return re.sub(r"\s+", " ", restored).strip()


# Build reverse index: normalized alias -> Product
# Sorted by alias length descending so multi-word aliases (e.g. "sarson ka tel") match before "tel"
_ALIAS_TO_PRODUCT: Dict[str, Product] = {}
_ALL_ALIASES_SORTED: List[Tuple[str, Product]] = []

for prod in _PRODUCTS:
    for alias in prod.aliases:
        norm_alias = normalize_text(alias)
        if norm_alias:
            _ALIAS_TO_PRODUCT[norm_alias] = prod

# Sort aliases by word count descending, then character length descending
_ALL_ALIASES_SORTED = sorted(
    _ALIAS_TO_PRODUCT.items(),
    key=lambda pair: (len(pair[0].split()), len(pair[0])),
    reverse=True,
)


def get_all_products() -> List[Product]:
    """Return the list of all registered products in the catalogue."""
    return list(_PRODUCTS)


def get_product_by_id(product_id: str) -> Optional[Product]:
    """Look up a product by its unique product_id."""
    for prod in _PRODUCTS:
        if prod.product_id == product_id:
            return prod
    return None


def find_product_by_alias(alias: str) -> Optional[Product]:
    """Look up a product by an exact normalized alias match."""
    norm = normalize_text(alias)
    return _ALIAS_TO_PRODUCT.get(norm)


def get_sorted_aliases() -> List[Tuple[str, Product]]:
    """Return a list of (normalized_alias, Product) sorted longest first for greedy phrase matching."""
    return _ALL_ALIASES_SORTED
