import os

_PORT = int(os.environ.get("PORT", 5000))
_HOST = os.environ.get("HOST", "0.0.0.0")
_raw_server_url = os.environ.get("SERVER_URL", "")
if not _raw_server_url:
    _raw_server_url = f"http://localhost:{_PORT}"
if "0.0.0.0" in _raw_server_url:
    _raw_server_url = _raw_server_url.replace("0.0.0.0", "localhost")
SERVER_URL = _raw_server_url.rstrip("/")
ACCESS_TOKEN_TTL = 3600
ID_TOKEN_TTL = 300
AUTH_CODE_TTL = 600
DEFAULT_SEED_COUNT = int(os.environ.get("SEED_COUNT", 30))

COUNTRY_CODES = {
    "Maldives": ("462", "MDV", "+960"),
    "Bangladesh": ("050", "BGD", "+880"),
    "India": ("356", "IND", "+91"),
    "Sri Lanka": ("144", "LKA", "+94"),
    "Nepal": ("524", "NPL", "+977"),
    "Philippines": ("608", "PHL", "+63"),
    "United Kingdom": ("826", "GBR", "+44"),
    "Germany": ("276", "DEU", "+49"),
    "France": ("250", "FRA", "+33"),
    "Italy": ("380", "ITA", "+39"),
    "China": ("156", "CHN", "+86"),
    "Japan": ("392", "JPN", "+81"),
    "Australia": ("036", "AUS", "+61"),
    "USA": ("840", "USA", "+1"),
}
