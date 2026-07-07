"""
50 benchmark questions across all GovData Analyser domains.
Each entry: (id, category, question, expected_domain)
"""

QUESTIONS = [
    # ── Housing ──────────────────────────────────────────────────────────────
    (1,  "Housing", "What is the median resale price in Tampines?", "housing"),
    (2,  "Housing", "Which HDB town has the highest resale prices?", "housing"),
    (3,  "Housing", "What are the most affordable HDB towns in Singapore?", "housing"),
    (4,  "Housing", "How have 4-room flat prices changed since 2020?", "housing"),
    (5,  "Housing", "What is the price trend for executive HDB flats?", "housing"),
    (6,  "Housing", "What is the price range for HDB flats in Woodlands?", "housing"),
    (7,  "Housing", "How much has the HDB median resale price increased from 2020 to 2025?", "housing"),
    (8,  "Housing", "What are the top 5 most expensive towns for HDB resale?", "housing"),
    (9,  "Housing", "Is there a price premium for high-floor HDB flats?", "housing"),
    (10, "Housing", "What is the typical price for a 5-room flat in Queenstown?", "housing"),
    (11, "Housing", "How many HDB resale transactions happened in 2023?", "housing"),
    (12, "Housing", "Which towns have seen the biggest HDB price increase recently?", "housing"),
    (13, "Housing", "What is the price range for 4-room flats in Jurong West?", "housing"),
    (14, "Housing", "What is the price per square metre for HDB flats by flat type?", "housing"),
    (15, "Housing", "What is the typical price for a 3-room flat in Yishun?", "housing"),
    (16, "Housing", "Compare HDB resale prices in Bishan vs Hougang", "housing"),
    (17, "Housing", "What flat types command the highest resale prices in Singapore?", "housing"),
    (18, "Housing", "How have HDB resale prices in Ang Mo Kio trended since 2022?", "housing"),

    # ── Labour ────────────────────────────────────────────────────────────────
    (19, "Labour", "What is Singapore's current unemployment rate?", "labour"),
    (20, "Labour", "How has the retrenchment rate changed since 2020?", "labour"),
    (21, "Labour", "What is the overall labour market health score for Singapore?", "labour"),
    (22, "Labour", "How many workers were retrenched in 2022?", "labour"),
    (23, "Labour", "What is the recruitment rate trend for Singapore?", "labour"),
    (24, "Labour", "Is Singapore's job market improving or deteriorating?", "labour"),
    (25, "Labour", "What are the long-term unemployment trends in Singapore?", "labour"),
    (26, "Labour", "How did COVID-19 affect Singapore's employment numbers?", "labour"),
    (27, "Labour", "Which year had the highest number of retrenchments?", "labour"),
    (28, "Labour", "Compare Singapore's unemployment rate in 2020 versus 2024", "labour"),
    (29, "Labour", "What does the composite labour health score indicate about workforce resilience?", "labour"),
    (30, "Labour", "What is the current long-term unemployment rate in Singapore?", "labour"),

    # ── Cross-Domain ──────────────────────────────────────────────────────────
    (31, "Cross-Domain", "Is there a correlation between HDB prices and unemployment rates?", "cross_domain"),
    (32, "Cross-Domain", "How does the labour market health affect HDB resale demand?", "cross_domain"),
    (33, "Cross-Domain", "Do high retrenchment periods lead to lower HDB property prices?", "cross_domain"),
    (34, "Cross-Domain", "What is the relationship between job market health and housing affordability?", "cross_domain"),
    (35, "Cross-Domain", "How have housing prices and employment trends diverged since 2020?", "cross_domain"),
    (36, "Cross-Domain", "Compare housing price growth with labour market recovery post-COVID", "cross_domain"),
    (37, "Cross-Domain", "Is Singapore's housing market decoupled from employment trends?", "cross_domain"),
    (38, "Cross-Domain", "What joint insights can we draw from Singapore's housing and labour data?", "cross_domain"),
    (39, "Cross-Domain", "How does unemployment affect HDB resale transaction volumes?", "cross_domain"),
    (40, "Cross-Domain", "What happens to HDB prices when retrenchments spike?", "cross_domain"),

    # ── Live City ─────────────────────────────────────────────────────────────
    (41, "Live City", "What is the current PSI reading in Singapore?", "environment"),
    (42, "Live City", "Is Singapore's air quality healthy right now?", "environment"),
    (43, "Live City", "What are the PM2.5 levels across different regions of Singapore?", "environment"),
    (44, "Live City", "Which region has the worst air quality today?", "environment"),
    (45, "Live City", "How does air quality vary between North and South Singapore?", "environment"),

    # ── Business ─────────────────────────────────────────────────────────────
    (46, "Business", "How many companies were registered in Singapore in 2023?", "business"),
    (47, "Business", "What are the current COE prices for Category A vehicles?", "business"),
    (48, "Business", "How has business registration changed post-COVID?", "business"),
    (49, "Business", "What is the trend for new company formations in Singapore?", "business"),

    # ── Demographics ─────────────────────────────────────────────────────────
    (50, "Demographics", "What are the population demographics and age distribution in Singapore?", "demographics"),
]
