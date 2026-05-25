import json
import uuid
import random
from datetime import datetime

from constants import SERVER_URL, DEFAULT_SEED_COUNT, COUNTRY_CODES

MALE_FIRST = [
    "Ahmed", "Mohamed", "Ali", "Hussain", "Ibrahim", "Ismail", "Hassan",
    "Abdulla", "Yoosuf", "Adam", "Moosa", "Nashid", "Naushad", "Shiyam",
    "Aslam", "Faisal", "Shamoon", "Naazim", "Rishwan", "Ashraf", "Musthafa",
    "Nasir", "Naseer", "Saeed", "Shakeeb", "Shifaz", "Zuhair", "Zaid",
    "Yameen", "Asif", "Inash", "Shaheen", "Faris", "Nabeel",
]

FEMALE_FIRST = [
    "Mariyam", "Fathimath", "Aishath", "Aminath", "Khadheeja", "Hawwa",
    "Shifza", "Zuhura", "Noora", "Amina", "Shaheena", "Moomina", "Niuma",
    "Ameena", "Hafsa", "Malsa", "Saara", "Shaina", "Sajida", "Shaufa",
    "Jumana", "Eeman", "Layan", "Iba", "Shaa", "Nahidha", "Aisha",
    "Fathun", "Nasra", "Mariya",
]

LAST_NAMES = [
    "Ahmed", "Ali", "Hassan", "Hussain", "Ibrahim", "Ismail", "Mohamed",
    "Abdulla", "Adam", "Moosa", "Naseer", "Latheef", "Waheed", "Rasheed",
    "Haleem", "Hameed", "Sameer", "Shaheem", "Shafeeq", "Shakeeb",
    "Nasheed", "Naeem", "Imad", "Saeed", "Manik", "Didi", "Fulhu",
    "Najeeb", "Jameel", "Shareef", "Habeeb", "Faiz", "Nazim",
]

DHIVEHI_MALE_FIRST = [
    "\u0787\u07a6\u0789\u07aa\u078b\u07aa", "\u0789\u07aa\u0780\u07a6\u0787\u07b0\u0789\u07aa\u078b\u07aa", "\u0787\u07a6\u078d\u07a9", "\u0780\u07aa\u0790\u07ac\u0787\u07a8\u0782\u07b0",
    "\u0787\u07a8\u0784\u07b0\u0783\u07a7\u0780\u07a8\u0789\u07b0", "\u0787\u07a8\u0790\u07b0\u0789\u07a7\u0783\u07a8\u078d\u07b0", "\u0780\u07a6\u0790\u07a6\u0782\u07b0", "\u0787\u07a6\u0784\u07b0\u078b\u07aa\ufdf2",
    "\u0794\u07ab\u0790\u07aa\u078a\u07b0", "\u0787\u07a7\u078b\u07a6\u0789\u07b0",
]

DHIVEHI_FEMALE_FIRST = [
    "\u0789\u07a6\u0783\u07a8\u0794\u07a6\u0789\u07b0", "\u078a\u07a7\u078c\u07a8\u0789\u07a6\u078c\u07aa", "\u0787\u07a6\u0787\u07a8\u079d\u07a6\u078c\u07aa", "\u0787\u07a6\u0789\u07a9\u0782\u07a6\u078c\u07aa",
    "\u079a\u07a6\u078b\u07a9\u0796\u07a7\u0783\u07a7", "\u0780\u07a6\u0787\u07b0\u0788\u07a7", "\u0792\u07aa\u0780\u07aa\u0783\u07a7", "\u0782\u07ab\u0783\u07a7",
    "\u0787\u07a7\u0789\u07a8\u0782\u07a7", "\u079d\u07a6\u0780\u07a9\u0782\u07a7",
]

DHIVEHI_LAST = [
    "\u0787\u07a6\u0780\u07aa\u0789\u07aa\u078b\u07aa", "\u0787\u07a6\u078d\u07a9", "\u0780\u07a6\u0790\u07a6\u0782\u07b0", "\u0780\u07aa\u0790\u07ac\u0787\u07a8\u0782\u07b0",
    "\u0787\u07a8\u0784\u07b0\u0783\u07a7\u0780\u07a8\u0789\u07b0", "\u0789\u07aa\u0780\u07a6\u0787\u07b0\u0789\u07aa\u078b\u07aa", "\u0787\u07a6\u0784\u07b0\u078b\u07aa\ufdf2",
    "\u078d\u07a6\u078c\u07a9\u078a\u07b0", "\u0788\u07a6\u0780\u07a9\u078b\u07aa", "\u0783\u07a6\u079d\u07a9\u078b\u07aa",
]

ISLANDS = [
    ("Male'", "\u0789\u07a7\u078d\u07ac", "K", "\u0786"), ("Addu", "\u0787\u07a6\u0787\u07b0\u078b\u07ab", "S", "\u0790"),
    ("Fuvahmulah", "\u078a\u07aa\u0788\u07a6\u0787\u07b0\u0789\u07aa\u078d\u07a6\u0787\u07b0", "Gn", "\u078f"), ("Hithadhoo", "\u0780\u07a8\u078c\u07a6\u078b\u07ab", "S", "\u0790"),
    ("Kulhudhuffushi", "\u0786\u07aa\u0785\u07aa\u078b\u07aa\u0787\u07b0\u078a\u07aa\u0781\u07a8", "HDh", "\u0780\u078b"),
    ("Thinadhoo", "\u078c\u07a8\u0782\u07a6\u078b\u07ab", "GDh", "\u078e\u078b"),
    ("Villingili", "\u0788\u07a8\u078d\u07a8\u078e\u07a8\u078d\u07a8", "Gn", "\u078f"),
    ("Naifaru", "\u0782\u07a6\u0787\u07a8\u078a\u07a6\u0783\u07aa", "Lh", "\u0785"),
    ("Mahibadhoo", "\u0789\u07a6\u0780\u07a8\u0784\u07a6\u078b\u07ab", "ADh", "\u0787\u078b"),
    ("Eydhafushi", "\u0787\u07ad\u078b\u07a6\u078a\u07aa\u0781\u07a8", "B", "\u0784"),
]

WARDS = [
    ("Maafannu", "M", "\u0789"), ("Henveiru", "H", "\u0780"),
    ("Galolhu", "G", "\u078e"), ("Machchangolhi", "Ma", "\u0789\u07a6"),
    ("Hulhumale'", "H", "\u0780"), ("Villimale'", "V", "\u0788"),
]

ADDRESS_LINES = [
    ("Sosun Magu", "\u0790\u07af\u0790\u07a6\u0782\u07b0 \u0789\u07a6\u078e\u07aa"), ("Ameenee Magu", "\u0787\u07a6\u0789\u07a9\u0782\u07a9 \u0789\u07a6\u078e\u07aa"),
    ("Chandhanee Magu", "\u0797\u07a6\u0782\u07b0\u078b\u07a6\u0782\u07a9 \u0789\u07a6\u078e\u07aa"), ("Fareedhee Magu", "\u078a\u07a6\u0783\u07a9\u078b\u07a9 \u0789\u07a6\u078e\u07aa"),
    ("Majeedhee Magu", "\u0789\u07a6\u0782\u07a9\u078b\u07a9 \u0789\u07a6\u078e\u07aa"), ("Buruzu Magu", "\u0784\u07aa\u0783\u07aa\u0792\u07aa \u0789\u07a6\u078e\u07aa"),
    ("Mulee-aage", "\u0789\u07aa\u078d\u07a9\u0787\u07a7\u078e\u07ac"), ("Gaskara", "\u078e\u07a6\u0790\u07b0\u0786\u07a6\u0783\u07a6"),
    ("Fehi Mahchangolhi", "\u078a\u07ac\u0780\u07a8 \u0789\u07a6\u0780\u07aa\u0797\u07a6\u0782\u07b0\u078e\u07ae\u0785\u07a8"),
]

_HOUSE_NAMES = [
    "Blue Light", "Ocean Villa", "Sunset", "Palm", "Coral", "Seabreeze",
    "Paradise", "Lagoon", "Shell", "Star", "Moonlight", "Sunrise",
    "Peacock", "Coconut", "Banyan", "Hibiscus", "Jasmine", "Lily",
]

users: dict[str, dict] = {}
_avatar_cache: dict[str, str] = {}


def _random_date(start_year=1960, end_year=2005) -> str:
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{month}/{day}/{year}"


def _random_mobile() -> str:
    return f"{random.choice([7, 9])}{random.randint(100000, 999999)}"


def _make_maldivian_address() -> str:
    addr = random.choice(ADDRESS_LINES)
    island = random.choice(ISLANDS)
    ward = random.choice(WARDS)
    house = random.choice(_HOUSE_NAMES)
    num = random.randint(1, 99)
    return json.dumps({
        "AddressLine1": house,
        "AddressLine2": f"{addr[0]} {num}",
        "Road": addr[0],
        "AtollAbbreviation": island[2],
        "AtollAbbreviationDhivehi": island[3],
        "IslandName": island[0],
        "IslandNameDhivehi": island[1],
        "HomeNameDhivehi": "",
        "Ward": ward[0],
        "WardAbbreviationEnglish": ward[1],
        "WardAbbreviationDhivehi": ward[2],
        "Country": "Maldives",
        "CountryISOThreeDigitCode": "462",
        "CountryISOThreeLetterCode": "MDV",
    })


def generate_user(user_type: str | None = None) -> dict:
    if user_type is None:
        user_type = random.choices(
            ["Maldivian", "Work Permit Holder", "Foreigner"],
            weights=[60, 25, 15],
        )[0]

    is_male = random.choice([True, False])
    gender = "M" if is_male else "F"

    if is_male:
        first_name = random.choice(MALE_FIRST)
        first_name_dhivehi = random.choice(DHIVEHI_MALE_FIRST)
    else:
        first_name = random.choice(FEMALE_FIRST)
        first_name_dhivehi = random.choice(DHIVEHI_FEMALE_FIRST)

    middle_name = random.choice(MALE_FIRST + FEMALE_FIRST) if random.random() > 0.6 else ""
    last_name = random.choice(LAST_NAMES)
    middle_name_dhivehi = random.choice(DHIVEHI_MALE_FIRST + DHIVEHI_FEMALE_FIRST) if middle_name else ""
    last_name_dhivehi = random.choice(DHIVEHI_LAST)

    full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
    full_name_dhivehi = f"{first_name_dhivehi} {middle_name_dhivehi} {last_name_dhivehi}".replace("  ", " ").strip()

    birthdate = _random_date()
    mobile = _random_mobile()

    if user_type == "Maldivian":
        idnumber = f"A{random.randint(100000, 999999)}"
        passport_number = ""
        is_workpermit_active = "False"
        country_name = "Maldives"
        country_code, country_code_alpha3, country_dialing_code = COUNTRY_CODES[country_name]
    elif user_type == "Work Permit Holder":
        idnumber = f"WP{random.randint(100000, 999999)}"
        passport_number = f"{random.choice('ABCDEFGHJKLMNP')}{random.randint(1000000, 9999999)}"
        is_workpermit_active = random.choice(["True", "False"])
        country_name = random.choice(["Bangladesh", "India", "Sri Lanka", "Nepal", "Philippines"])
        country_code, country_code_alpha3, country_dialing_code = COUNTRY_CODES[country_name]
    else:
        idnumber = f"{random.choice('ABCDEFGHJKLMNP')}{random.randint(1000000, 9999999)}"
        passport_number = idnumber
        is_workpermit_active = "False"
        country_name = random.choice(["United Kingdom", "Germany", "France", "Italy", "China", "Japan", "Australia", "USA"])
        country_code, country_code_alpha3, country_dialing_code = COUNTRY_CODES[country_name]

    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"

    verified = random.choice(["True", "False"])
    verification_type = "biometric" if verified == "True" else random.choice(["in-person", "NA"])

    last_verified_date = ""
    if verified == "True":
        last_verified = datetime(random.randint(2019, 2024), random.randint(1, 12), random.randint(1, 28),
                                 random.randint(8, 18), random.randint(0, 59), random.randint(0, 59))
        last_verified_date = last_verified.strftime("%m/%d/%Y %I:%M:%S %p")

    updated_at = datetime(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28),
                          random.randint(8, 18), random.randint(0, 59), random.randint(0, 59))
    updated_at_str = updated_at.strftime("%m/%d/%Y %I:%M:%S %p")

    permanent_address = _make_maldivian_address()

    return {
        "sub": str(uuid.uuid4()),
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "full_name": full_name,
        "first_name_dhivehi": first_name_dhivehi,
        "middle_name_dhivehi": middle_name_dhivehi,
        "last_name_dhivehi": last_name_dhivehi,
        "full_name_dhivehi": full_name_dhivehi,
        "gender": gender,
        "idnumber": idnumber,
        "email": email,
        "birthdate": birthdate,
        "passport_number": passport_number,
        "is_workpermit_active": is_workpermit_active,
        "updated_at": updated_at_str,
        "country_dialing_code": country_dialing_code,
        "country_code": country_code,
        "country_code_alpha3": country_code_alpha3,
        "verified": verified,
        "verification_type": verification_type,
        "permanent_address": permanent_address,
        "user_type_description": user_type,
        "mobile": mobile,
        "photo": f"{SERVER_URL}/user/photo",
        "country_name": country_name,
        "last_verified_date": last_verified_date,
        "name": full_name,
        "avatar": f"{SERVER_URL}/user/photo",
        "nickname": first_name,
    }


def seed_users(count: int = DEFAULT_SEED_COUNT):
    for _ in range(count):
        user = generate_user()
        users[user["sub"]] = user
    test_user = {
        "sub": "3b46dc4b-f565-420b-af8f-9312c86e40cb",
        "first_name": "CSC", "middle_name": "Test User", "last_name": "18",
        "full_name": "CSC Test User 18",
        "first_name_dhivehi": "\u0790\u07a9\u0787\u07ac\u0790\u07b0\u0790\u07a9",
        "middle_name_dhivehi": "\u078c\u07ac\u0790\u07b0\u078c\u07b0 \u0794\u07ab\u0790\u07a6\u0783\u07a6",
        "last_name_dhivehi": "18",
        "full_name_dhivehi": "\u0790\u07a9\u0787\u07ac\u0790\u07b0\u0790\u07a9 \u078c\u07ac\u0790\u07b0\u078c\u07b0 \u0794\u07ab\u0790\u07a6\u0783\u07a6 18",
        "gender": "M", "idnumber": "A900318", "email": "csc318@gmail.com",
        "birthdate": "10/22/1993", "passport_number": "LA19E7432",
        "is_workpermit_active": "False", "updated_at": "1/2/1995 12:00:00 AM",
        "country_dialing_code": "+960", "country_code": "462", "country_code_alpha3": "MDV",
        "verified": "False", "verification_type": "NA",
        "permanent_address": json.dumps({
            "AddressLine1": "asd", "AddressLine2": "", "Road": "",
            "AtollAbbreviation": "K", "AtollAbbreviationDhivehi": "\u0786",
            "IslandName": "Male'", "IslandNameDhivehi": "\u0789\u07a7\u078d\u07ac",
            "HomeNameDhivehi": "", "Ward": "Dhaftharu",
            "WardAbbreviationEnglish": "Dhaftharu", "WardAbbreviationDhivehi": "",
            "Country": "Maldives", "CountryISOThreeDigitCode": "462", "CountryISOThreeLetterCode": "MDV",
        }),
        "user_type_description": "Maldivian", "mobile": "7730018",
        "photo": f"{SERVER_URL}/user/photo", "country_name": "Maldives",
        "last_verified_date": "", "name": "CSC Test User 18",
        "avatar": f"{SERVER_URL}/user/photo", "nickname": "CSC",
    }
    users[test_user["sub"]] = test_user


seed_users()
