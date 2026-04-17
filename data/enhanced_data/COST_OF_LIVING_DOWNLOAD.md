# Cost of Living Data - Download Instructions

## Source 1: Kaggle - Numbeo Cost of Living (Recommended)
1. Visit: https://www.kaggle.com/datasets/prasertk/numbeo-cost-of-living-2024
   OR: https://www.kaggle.com/datasets/ahmedshahriar/numbeo-cost-of-living-index
2. Download CSV file
3. Save to: `data/enhanced_data/numbeo_cost_of_living.csv`

## Source 2: Numbeo Direct
1. Visit: https://www.numbeo.com/cost-of-living/rankings_by_country.jsp
2. Scrape or manually copy data
3. Columns needed:
   - Country
   - Consumer Price Index
   - Rent Index
   - Consumer Price Plus Rent Index
   - Restaurant Price Index
   - Groceries Index

## Source 3: World Bank PPP (Alternative)
1. Visit: https://data.worldbank.org/indicator/PA.NUS.PPPC.RF
2. Download "Price level ratio of PPP conversion factor"
3. Save to: `data/enhanced_data/world_bank_ppp.csv`

## Expected Columns
- country: Country name
- consumer_price_index: Overall cost index
- rent_index: Accommodation costs
- restaurant_price_index: Dining costs
- groceries_index: Food prices

## Last Updated
2026-04-16
