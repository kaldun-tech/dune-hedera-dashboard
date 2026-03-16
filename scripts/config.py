"""Configuration for Hedera data pipeline."""

import os
from dotenv import load_dotenv

load_dotenv()

# Hedera Mirror Node
HEDERA_MIRROR_URL = os.getenv(
    "HEDERA_MIRROR_URL",
    "https://mainnet-public.mirrornode.hedera.com"
)

# Dune API
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
DUNE_UPLOAD_URL = "https://api.dune.com/api/v1/table/upload/csv"
DUNE_USERNAME = os.getenv("DUNE_USERNAME", "your_username")

# Data settings
DAYS_TO_FETCH = 90
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Rate limiting
REQUESTS_PER_SECOND = 20
REQUEST_TIMEOUT = 30

# Transaction types mapping
TX_TYPE_CATEGORIES = {
    "CRYPTOTRANSFER": "crypto",
    "CRYPTOAPPROVEALLOWANCE": "crypto",
    "CRYPTODELETEALLOWANCE": "crypto",
    "CONSENSUSCREATETOPIC": "hcs",
    "CONSENSUSSUBMITMESSAGE": "hcs",
    "CONSENSUSUPDATETOPIC": "hcs",
    "CONSENSUSDELETETOPIC": "hcs",
    "TOKENCREATION": "token",
    "TOKENTRANSFERS": "token",
    "TOKENASSOCIATE": "token",
    "TOKENDISSOCIATE": "token",
    "TOKENMINT": "token",
    "TOKENBURN": "token",
    "CONTRACTCALL": "contract",
    "CONTRACTCREATEINSTANCE": "contract",
    "ETHEREUMTRANSACTION": "contract",
}

def get_tx_category(tx_name: str) -> str:
    """Map transaction name to category."""
    return TX_TYPE_CATEGORIES.get(tx_name, "other")
