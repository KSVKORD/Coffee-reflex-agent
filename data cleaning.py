import re
import pandas as pd
import numpy as np

df = pd.read_excel("r_espresso Bean & Brew Database (Responses).xlsx")

# Preview columns
print(df.columns)

## Step1-Keep only the required fields
needed_columns = [
    "Bean/blend name",
    "Origin",
    "Roast level",
    "Cost per 100 g",
    "Rating",
    "Currency",
    "Roaster's country",
    "Tasting notes",

]

df_sub = df[needed_columns].copy()
print("After selecting needed columns:", df_sub.shape)
print("Rows after selecting needed columns:", len(df_sub))

## Step2-Fix missing Currency in df_sub using Roaster's country
# Normalize country names
country_norm = df_sub["Roaster's country"].astype(str).str.lower().str.strip()

# Raw currency as string
currency_raw = df_sub["Currency"].astype(str)

# Currency considered "missing" if empty
missing_currency_mask = df_sub["Currency"].isna() | (currency_raw.str.strip() == "")

# Case 1: Missing currency AND US roaster -> assume USD ("$")
us_mask = missing_currency_mask & (country_norm == "united states")
df_sub.loc[us_mask, "Currency"] = "$"

# Case 2: Missing currency AND non-US roaster -> mark as "unknown"
non_us_missing_mask = missing_currency_mask & (country_norm != "united states")
df_sub.loc[non_us_missing_mask, "Currency"] = "unknown"

print("Filled Currency for US roasters:", us_mask.sum())
print("Marked Currency as 'unknown' for non-US missing:", non_us_missing_mask.sum())
print("Currency value counts after filling:")
print(df_sub["Currency"].value_counts(dropna=False))


## Step3-Filter to USD only
usd_mask = df_sub["Currency"].astype(str).str.contains(
    r"^\s*\$|usd", case=False, na=False
)

df_usd = df_sub[usd_mask].copy()
df_usd.reset_index(drop=True, inplace=True)

print("Rows before USD filter:", len(df_sub))
print("Rows after USD filter (df_usd):", len(df_usd))


## Step4-Normalize bean name & origin
# Bean name: raw + lowercased normalized version
df_usd["Bean/blend name"] = df_usd["Bean/blend name"].astype(str).str.strip()
df_usd["bean_name_norm"] = df_usd["Bean/blend name"].str.lower()

# Origin: raw + lowercased normalized version
df_usd["Origin"] = df_usd["Origin"].astype(str).str.strip()
df_usd["origin_norm"] = df_usd["Origin"].str.lower()


## Step5-Classify roast level
# Convert roast descriptions into small set
def classify_roast(level):
    if pd.isna(level):
        return "unknown"
    if 1 <= level <= 3:
        return "light"
    if 4 <= level <= 5:
        return "medium"
    if 6 <= level <= 7:
        return "dark"
    return "unknown"

df_usd["roast_group"] = df_usd["Roast level"].apply(classify_roast)

print("Roast_group counts (USD-only):")
print(df_usd["roast_group"].value_counts(dropna=False))

df_usd["Roast level"] = df_usd["Roast level"].astype(object)
df_usd.loc[df_usd["Roast level"].isna(), "Roast level"] = "unknown"


## Step6-Clean cost and compute percentile
df_usd["Cost per 100 g"] = pd.to_numeric(df_usd["Cost per 100 g"], errors="coerce")

cost_valid = df_usd["Cost per 100 g"].dropna()

print("Valid cost count (USD-only):", len(cost_valid))
print("\nCost per 100 g (USD-only, valid only) summary:")
print(cost_valid.describe())

p5 = cost_valid.quantile(0.05)
p95 = cost_valid.quantile(0.95)

print(f"\n5th percentile (p5): {p5:.2f}")
print(f"95th percentile (p95): {p95:.2f}")

# Main cluster & expensive outliers just for info
main_mask = (cost_valid >= p5) & (cost_valid <= p95)
main_cost = cost_valid[main_mask]
expensive_cost = cost_valid[cost_valid > p95]

print("Main cluster count:", main_mask.sum())
print("Expensive outlier count:", len(expensive_cost))
print("Expensive outliers:")
print(expensive_cost.sort_values(ascending=False))


## Step7-Classify price level
cheap_threshold = main_cost.quantile(0.33)
print(f"\nCheap threshold within main cluster: {cheap_threshold:.2f}")

def classify_price(cost):
    if pd.isna(cost):
        return "unknown"       # no cost info
    if cost > p95:
        return "expensive"
    if cost <= cheap_threshold:
        return "cheap"
    return "medium"

df_usd["price_level"] = df_usd["Cost per 100 g"].apply(classify_price)

print("Price_level counts (USD-only):")
print(df_usd["price_level"].value_counts(dropna=False))

# Fill empty slot into unknown
df_usd["Cost per 100 g"] = df_usd["Cost per 100 g"].astype(object)
df_usd.loc[df_usd["Cost per 100 g"].isna(), "Cost per 100 g"] = "unknown"

## Step8-Catalog tasting keywords from data exploration
# Put most frequent words into a catalog manually, then add some that are helpful
TASTE_KEYWORD_BANK = {
    "chocolate",
    "dark chocolate",
    "milk chocolate",
    "chocolatey",
    "low acidity",
    "high acidity",
    "acidity",
    "caramel",
    "nutty",
    "hazelnut",
    "fruit",
    "fruity",
    "berry",
    "dark cherry",
    "cherry",
    "sweet",
    "rich",
    "syrupy",
    "full body",
    "medium body",
    "light body",
    "body",
}

def extract_taste_keywords(note_text: str):
    text = str(note_text).lower().strip()
    extracted = []

    # Phrase-first matching
    for phrase in sorted(TASTE_KEYWORD_BANK, key=lambda x: len(x.split()), reverse=True):
        if phrase in text:
            extracted.append(phrase)

    extracted = sorted(set(extracted))

    if len(extracted) == 0:
        return ["unknown"]

    return extracted


# Normalize original tasting notes
df_usd["Tasting notes"] = df_usd["Tasting notes"].fillna("").astype(str).str.strip()
df_usd["tasting_notes_norm"] = df_usd["Tasting notes"].str.lower()

# Apply extractor
df_usd["tasting_keywords"] = df_usd["tasting_notes_norm"].apply(extract_taste_keywords)

# Build  cleaned notes
def build_clean_note(keyword_list):
    if keyword_list == ["unknown"]:
        return "unknown"
    return ", ".join(keyword_list)

df_usd["tasting_notes_clean"] = df_usd["tasting_keywords"].apply(build_clean_note)

# Normalize unknown rows
unknown_mask = df_usd["tasting_keywords"].apply(lambda ks: ks == ["unknown"])

df_usd.loc[unknown_mask, "Tasting notes"] = "unknown"
df_usd.loc[unknown_mask, "tasting_notes_clean"] = "unknown"
df_usd.loc[unknown_mask, "tasting_keywords"] = df_usd.loc[unknown_mask, "tasting_keywords"].apply(
    lambda _: ["unknown"]
)

print(df_usd[["Tasting notes", "tasting_notes_clean", "tasting_keywords"]].head(10))

## Step9-Build final cleaned and save
clean_cols = [
    "Bean/blend name",
    "bean_name_norm",
    "Origin",
    "origin_norm",
    "Roast level",
    "roast_group",
    "Cost per 100 g",
    "price_level",
    "Rating",
    "Tasting notes",
    "tasting_notes_clean",
    "tasting_keywords",
    "Currency",
    "Roaster's country",
]

clean_df = df_usd[clean_cols].copy()

print("\nCleaned catalog shape:", clean_df.shape)
print(clean_df.head())

clean_df.to_csv("coffee_beans_cleaned_for_agent.csv", index=False)
print("Saved")