import pandas as pd
import ast
import random

# Import cleaned data
def load_data(path="coffee_beans_cleaned_for_agent.csv"):
    df = pd.read_csv(path)

    # Normalize text columns for safety
    df["bean_name_norm"] = df["bean_name_norm"].astype(str).str.lower().str.strip()
    df["origin_norm"] = df["origin_norm"].astype(str).str.lower().str.strip()

    # Convert tasting_keywords from string to list
    def parse_kw(x):
        if isinstance(x, list):
            return x
        if isinstance(x, str):
            s = x.strip()
            if s == "" or s.lower() == "unknown":
                return ["unknown"]
            try:
                v = ast.literal_eval(s)
                if isinstance(v, list):
                    return [str(t).lower().strip() for t in v]
                else:
                    return ["unknown"]
            except Exception:
                return ["unknown"]
        return ["unknown"]

    df["tasting_keywords"] = df["tasting_keywords"].apply(parse_kw)

    return df
# Setting up keywords

TASTE_KEYWORD_BANK = {
    "dark chocolate",
    "milk chocolate",
    "chocolate",
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
    "finish",
    "clean finish",
}

ROAST_KEYWORDS = {
    "light": "light",
    "light roast": "light",
    "medium": "medium",
    "medium roast": "medium",
    "dark": "dark",
    "dark roast": "dark",
}

PRICE_KEYWORDS = {
    "cheap": "cheap",
    "budget": "cheap",
    "inexpensive": "cheap",
    "medium price": "medium",
    "mid price": "medium",
    "expensive": "expensive",
    "premium": "expensive",
}

RATING_WORDS = {"best", "top", "top-rated", "top rated", "highly rated"}

# token/phrase extractor, which converts them into (tokens_set, lowercased_text)
def extract_tokens(text):
    text = text.lower().strip()
    words = text.split()

    # up to 2-word phrases
    phrases = []
    for i in range(len(words)):
        for j in range(i + 1, min(i + 3, len(words) + 1)):
            phrases.append(" ".join(words[i:j]))

    tokens = set(words + phrases)
    return tokens, text



# Rule-based recommendation logic
def recommend_beans(user_text, df):
    """
    Simple reflex agent:
    Priority:
      1. bean name
      2. taste
      3. origin
      4. roast
      5. price
      6. rating preference
    Fallback:
      - if no preferences detected or
      - no beans matched filters
        then return 5 random beans among the highest-rated group
    """
    tokens, text = extract_tokens(user_text)

    # High priority bean name
    bean_matches = []
    for name in df["bean_name_norm"].unique():
        if name and name in text:
            bean_matches.append(name)

    if bean_matches:
        results = df[df["bean_name_norm"].isin(bean_matches)]
        return results, "matched by bean name"

    results = df.copy()

    # Taste keyword
    taste_terms = [t for t in tokens if t in TASTE_KEYWORD_BANK]

    for t in taste_terms:
        results = results[results["tasting_keywords"].apply(lambda ks: t in ks)]


    # Origin
    origin_terms = []
    for t in tokens:
        if df["origin_norm"].str.contains(t, na=False).any():
            origin_terms.append(t)

    for t in origin_terms:
        results = results[results["origin_norm"].str.contains(t, na=False)]


    # Roast level
    roast_pref = None
    for t in sorted(tokens, key=len, reverse=True):
        if t in ROAST_KEYWORDS:
            roast_pref = ROAST_KEYWORDS[t]
            break

    if roast_pref is not None:
        results = results[results["roast_group"] == roast_pref]

    # Price
    price_pref = None
    for t in sorted(tokens, key=len, reverse=True):
        if t in PRICE_KEYWORDS:
            price_pref = PRICE_KEYWORDS[t]
            break

    if price_pref is not None:
        results = results[results["price_level"] == price_pref]


    # Rating preference
    wants_top = any(w in text for w in RATING_WORDS)
    if wants_top and len(results) > 0:
        results = results.sort_values("Rating", ascending=False)


    # Detection to no preference
    has_preferences = (
        bool(taste_terms)
        or bool(origin_terms)
        or roast_pref is not None
        or price_pref is not None
        or wants_top
    )

    if not has_preferences:
        # Return 5 random beans from the highest rated group
        top_rating = df["Rating"].max()
        top_df = df[df["Rating"] == top_rating]
        return top_df.sample(n=min(5, len(top_df))), "no preferences detected – showing random top-rated beans"



    # If filter result in no beans
    if len(results) == 0:
        top_rating = df["Rating"].max()
        top_df = df[df["Rating"] == top_rating]
        return top_df.sample(n=min(5, len(top_df))), "no matches – showing random top-rated beans"


    # Normal cases
    return results, "matched by filters"


# Interaction loop

def main():
    df = load_data()

    print("Coffee Bean Reflex Agent")
    print("Type what you want (e.g. 'cheap chocolatey medium roast from Ethiopia').")
    print("Type 'quit' to exit.")

    while True:
        user_text = input("\nYou: ").strip()
        if user_text.lower() == "quit":
            print("Agent: Goodbye.")
            break

        if user_text == "":
            print("Agent: Please describe the coffee you want, or 'quit' to exit.")
            continue

        results, reason = recommend_beans(user_text, df)

        print(f"Agent ({reason}):")

        # show up to 5 beans
        for _, row in results.head(5).iterrows():
            print(f"- {row['Bean/blend name']}")
            print(f"  Origin: {row['Origin']}")
            print(f"  Roast: {row['roast_group']}")
            print(f"  Price level: {row['price_level']}")
            print(f"  Rating: {row['Rating']}")
            print(f"  Tasting: {row['tasting_notes_clean']}")
            print()

if __name__ == "__main__":
    main()
