import pandas as pd
import numpy as np
from faker import Faker
import random
import os
import warnings
warnings.filterwarnings('ignore')

fake = Faker()
random.seed(42)
np.random.seed(42)

os.makedirs('output', exist_ok=True)
print('Imports OK')


#---
## 1. Generate Synthetic Enterprise Sales Data
#
#Simulates a real-world data dump with **intentional data quality issues** you are likely to encounter:
#
#| # | Issue | What it looks like |
#|---|-------|--------------------|
#| 1 | Missing values | NaN in `Industry`, `ACV_USD`, `Close_Date` |
#| 2 | Inconsistent categories | `'emea'`, `'EMEA '`, `'Emea'` all meaning the same thing |
#| 3 | Duplicate rows | Same `Opportunity_ID` appears twice |
#| 4 | Outliers / data entry errors | ACV of $0 or $9,999,999 |
#| 5 | Date format inconsistency | Mix of `YYYY-MM-DD` and `DD/MM/YYYY` |
#| 6 | Free-text field noise | Stage names with trailing spaces or mixed case |
#| 7 | Logical inconsistency | `Close_Date` before `Created_Date` |

N = 800  # number of rows before injecting duplicates

# --- Reference data ---
regions_clean     = ['AMER', 'EMEA', 'APAC']
# Issue 2: region name variants that will need normalising
regions_dirty     = ['AMER', 'amer', 'EMEA', 'emea', 'EMEA ', 'Emea', 'APAC', 'apac', 'APac']

products          = ['AutoCAD', 'Revit', 'Fusion 360', 'Inventor', 'Civil 3D', 'BIM 360', 'Forma']
contract_types    = ['EBA', 'Flex', 'Subscription']
industries        = ['Architecture', 'Engineering', 'Construction', 'Manufacturing',
                     'Media & Entertainment', 'Government', 'Energy']

# Issue 6: stage name variants
stages_dirty      = ['Prospecting', 'prospecting', 'Qualification', 'Qualification ',
                     'Proposal', 'PROPOSAL', 'Negotiation', 'Closed Won',
                     'closed won', 'Closed Lost', 'CLOSED LOST']
stages_valid      = ['Prospecting', 'Qualification', 'Proposal', 'Negotiation',
                     'Closed Won', 'Closed Lost']

countries_by_region = {
    'AMER': ['United States', 'Canada', 'Brazil', 'Mexico'],
    'EMEA': ['United Kingdom', 'Germany', 'France', 'Netherlands', 'Poland', 'UAE'],
    'APAC': ['Australia', 'Japan', 'Singapore', 'India', 'South Korea']
}

def random_date(start_year=2023, end_year=2025, fmt='%Y-%m-%d'):
    start = pd.Timestamp(f'{start_year}-01-01')
    end   = pd.Timestamp(f'{end_year}-12-31')
    delta = (end - start).days
    dt    = start + pd.Timedelta(days=random.randint(0, delta))
    return dt.strftime(fmt)

sales_reps = [fake.name() for _ in range(40)]

rows = []
for i in range(N):
    region_raw  = random.choice(regions_dirty)
    region_norm = region_raw.strip().upper()
    country     = random.choice(countries_by_region.get(region_norm, ['Unknown']))
    product     = random.choice(products)
    ctype       = random.choice(contract_types)
    stage       = random.choice(stages_dirty)

    # ACV: mostly realistic, some outliers (Issue 4)
    acv_roll = random.random()
    if acv_roll < 0.02:
        acv = 0                          # data entry error
    elif acv_roll < 0.04:
        acv = 9_999_999                  # likely a placeholder
    elif ctype == 'EBA':
        acv = round(random.uniform(150_000, 2_000_000), 2)
    elif ctype == 'Flex':
        acv = round(random.uniform(10_000, 500_000), 2)
    else:
        acv = round(random.uniform(5_000, 300_000), 2)

    # Dates — mix of formats (Issue 5)
    fmt_created = random.choice(['%Y-%m-%d', '%Y-%m-%d'])
    fmt_close   = random.choice(['%Y-%m-%d', '%d/%m/%Y'])
    created_date = random_date(2023, 2024, fmt_created)
    close_date   = random_date(2024, 2025, fmt_close)

    # Issue 7: ~3% of rows have close_date BEFORE created_date
    if random.random() < 0.03:
        close_date = random_date(2022, 2022, fmt_close)

    row = {
        'Opportunity_ID' : f'OPP-{10000 + i}',
        'Account_Name'   : fake.company(),
        'Region'         : region_raw,            # dirty
        'Country'        : country,
        'Industry'       : random.choice(industries) if random.random() > 0.08 else np.nan,  # Issue 1
        'Product'        : product,
        'Contract_Type'  : ctype,
        'Stage'          : stage,                  # dirty
        'ACV_USD'        : acv if random.random() > 0.05 else np.nan,  # Issue 1
        'TCV_USD'        : round(acv * random.uniform(1, 3), 2) if acv and acv < 9_000_000 else np.nan,
        'Created_Date'   : created_date,
        'Close_Date'     : close_date,             # mixed formats + logical errors
        'Sales_Rep'      : random.choice(sales_reps),
        'Notes'          : fake.sentence() if random.random() > 0.7 else np.nan,
    }
    rows.append(row)

df_raw = pd.DataFrame(rows)

# Issue 3: inject ~30 duplicate rows
dupes = df_raw.sample(30, random_state=1)
df_raw = pd.concat([df_raw, dupes], ignore_index=True).sample(frac=1, random_state=7).reset_index(drop=True)

print(f'Raw dataset: {df_raw.shape[0]} rows × {df_raw.shape[1]} columns')
df_raw.head(10)

df_raw.to_csv('output/enterprise_sales_raw.csv', index=False)
print('Saved → output/enterprise_sales_raw.csv')
