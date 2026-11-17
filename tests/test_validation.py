from app.core.validation import parse_number,parse_range
from app.core.models import NumericRange

def test_decimal_comma(): assert parse_number('1,60') == 1.6
def test_interval(): assert parse_range('41,25 - 41,80') == NumericRange(41.25,41.8)
def test_single_value(): assert parse_range('20,5') == NumericRange(20.5,20.5)
