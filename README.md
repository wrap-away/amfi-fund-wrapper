# amfi-fund-wrapper

Fetch Mutual Fund information from AMFI.

Tested on Python 3.8+.

## Usage

```python
import amfi

for scheme_type, scheme_sub_type in amfi.get_all_mfs().items():
    for scheme_sub_type_name, fund_houses in scheme_sub_type.items():
        for fund_house_name, funds in fund_houses:
            for fund in funds:
                print(f'{scheme_type} {scheme_sub_type_name} {fund_house_name} {fund.SchemeName}')

# Check out amfi/nav.py
```

## Format

```
    Dictionary of all mutual funds.
    {
        <scheme_type: Open/Close/Interval>: {
            <scheme_sub_type: Money Market/Liquid/etc>: {
                <fund_house_name>: [
                    <Fund>
                    ...
                ]
            }
        }
    }

    <Fund>:
    @dataclass
    class Fund:
        SchemeCode: str
        SchemeName: str
        ISINDivPayoutGrowth: str
        ISINDivReinvestment: str
        NAV: str
        Date: str
```