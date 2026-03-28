import pandas as pd

# AI-related stocks and ETFs
AI_TICKERS = [
    # ETFs
    "BOTZ",  # Global X Robotics & AI ETF
    "AIQ",   # Global X AI & Technology ETF
    "CHAT",  # Roundhill Generative AI & Technology ETF
    "ARKQ",  # ARK Autonomous Technology & Robotics ETF
    "ROBO",  # ROBO Global Robotics and Automation ETF
    # Stocks
    "NVDA",  # NVIDIA
    "AMD",   # AMD
    "MSFT",  # Microsoft
    "GOOGL", # Alphabet
    "META",  # Meta
    "AMZN",  # Amazon
    "TSLA",  # Tesla
    "PLTR",  # Palantir
    "AI",    # C3.ai
    "SMCI",  # Super Micro Computer
    "ARM",   # Arm Holdings
]

# Nuclear power stocks and ETFs
NUCLEAR_TICKERS = [
    # ETFs
    "NLR",   # VanEck Uranium+Nuclear Energy ETF
    "URA",   # Global X Uranium ETF
    "URNM",  # Sprott Uranium Miners ETF
    # Stocks
    "CCJ",   # Cameco (uranium mining)
    "CEG",   # Constellation Energy (nuclear power)
    "VST",   # Vistra Energy
    "LEU",   # Centrus Energy
    "NNE",   # Nano Nuclear Energy
    "SMR",   # NuScale Power
    "OKLO",  # Oklo (next-gen nuclear)
]

# Additional hand-picked tickers
EXTRA_TICKERS = ["VOO", "VT", "NVDA"]


def get_sp500() -> list[str]:
    """Fetch current S&P 500 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url, storage_options={"User-Agent": "Mozilla/5.0"})
    symbols = tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()
    return symbols


def get_all_tickers() -> list[str]:
    """Return deduplicated union of all ticker groups."""
    sp500 = get_sp500()
    all_tickers = set(sp500) | set(AI_TICKERS) | set(NUCLEAR_TICKERS) | set(EXTRA_TICKERS)
    return sorted(all_tickers)
