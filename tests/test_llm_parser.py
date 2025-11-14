"""
Test the LLM-based parser with sample markdown data
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.llm_parser_tools import LLMParserTool, LLMParserToolConfig
from src.config.settings import settings

# Sample markdown with problematic case (no product name at top)
sample_markdown_problematic = """
# Product datasheet

## - <br> Product features and benefits

- Lightweight and compact reflector lamps with ECG
- High luminance through very short arc and high pressure
- Produces brilliant light effects
- Stable light output over the entire lifetime
- Long lifetime
- Easy lamp replacement
- Approved by leading moving lighting fixture companies

--- Page Separator ---

# Technical data

## General Product Information

| Product number (Americas) | 4062172392938 |
| :-- | :-- |
| Product name (Americas) | SIRIUS HRI 420W S 2/CS 1/SKU |
| Family brand | SIRIUS HRI |
| Category | CORE |
| Global order reference | SIRIUS HRI 420 W S |

## Electrical Data

| Nominal wattage | 420 W |
| :-- | :-- |
| Nominal voltage | 70.0 V |
| Nominal current | 5 A |

## Photometric Data

| Nominal luminous flux | 21000 lm |
| :-- | :-- |
| Color temperature | 7700 K |
| Color rendering index Ra | 85 |
| Working distance | 34.4 mm |

## Lifetime Data

Nominal lifetime 2500 hr
"""

# Sample markdown with good case (product name at top)
sample_markdown_good = """
# SIRIUS HRI 440 W +

SIRIUS HRI | High pressure discharge lamps designed to provide brilliant light effects.

![img-0.jpeg](img-0.jpeg)

## Areas of application

- Concert Lighting
- Club & Disco
- Stage & Theatre
- Studio, TV, & Film

## Product features and benefits

- Lightweight and compact reflector lamps with ECG
- High luminance through very short arc and high pressure

--- Page Separator ---

# Technical data

## General Product Information

| Product number (Americas) | 4062172273442 |
| :-- | :-- |
| Product name (Americas) | SIRIUS HRI 440W+ 2/CS 1/SKU |
| Family brand | SIRIUS HRI |
| Global order reference | SIRIUS HRI 440 W + |

## Electrical Data

| Nominal wattage | 440 W |
| :-- | :-- |
| Nominal voltage | 72.0 V |
| Nominal current | 6 A |

## Photometric Data

| Nominal luminous flux | 26000 lm |
| :-- | :-- |
| Color temperature | 8000 K |
| Color rendering index Ra | 90 |

## Lifetime Data

Nominal lifetime 2000 hr
"""


def test_llm_parser():
    """Test the LLM parser with sample data"""
    print("=" * 70)
    print("Testing LLM-Based Parser")
    print("=" * 70)

    # Initialize parser
    parser = LLMParserTool(
        LLMParserToolConfig(api_key=settings.mistral_api_key, model=settings.llm_model)
    )

    # Test 1: Problematic case
    print("\nTest 1: Extract from 'Global order reference' (no product name at top)")
    print("-" * 70)
    products = parser.run(sample_markdown_problematic, "test_problematic.pdf")

    if products:
        product = products[0]
        print(f"✓ Product parsed successfully!")
        print(f"  Product Name: {product.product_name}")
        print(f"  SKU: {product.sku}")
        print(f"  wattage: {product.wattage}")
        print(f"  Voltage: {product.voltage}")
        print(f"  Luminous Flux: {product.luminous_flux}")
        print(f"  Lifetime: {product.lifetime_hours} hours")
        print(f"\n  Expected product_name: 'SIRIUS HRI 420 W S'")

        if product.product_name == "SIRIUS HRI 420 W S":
            print("  ✓✓✓ CORRECT! Product name extracted properly!")
        elif "Lightweight" in product.product_name or "Product datasheet" in product.product_name:
            print(f"  ✗✗✗ WRONG! Got description/header instead of product name")
        else:
            print(f"  ⚠ Close, but not exact match")
    else:
        print("✗ No products found")

    # Test 2: Good case
    print("\n" + "=" * 70)
    print("Test 2: Extract from heading (product name at top)")
    print("-" * 70)
    products2 = parser.run(sample_markdown_good, "test_good.pdf")

    if products2:
        product = products2[0]
        print(f"✓ Product parsed successfully!")
        print(f"  Product Name: {product.product_name}")
        print(f"  SKU: {product.sku}")
        print(f"  wattage: {product.wattage}")
        print(f"  Voltage: {product.voltage}")
        print(f"  Luminous Flux: {product.luminous_flux}")
        print(f"  Lifetime: {product.lifetime_hours} hours")
        print(f"\n  Expected product_name: 'SIRIUS HRI 440 W +'")

        if product.product_name == "SIRIUS HRI 440 W +":
            print("  ✓✓✓ CORRECT! Product name extracted properly!")
        else:
            print(f"  ⚠ Close: got '{product.product_name}'")
    else:
        print("✗ No products found")

    print("\n" + "=" * 70)
    print("LLM Parser Testing Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_llm_parser()
