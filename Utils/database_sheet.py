import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define API scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Load credentials (your JSON key file)
creds = ServiceAccountCredentials.from_json_keyfile_name("compile-bot-creds.json", scope)

# Authorize client
client = gspread.authorize(creds)

# Correct spreadsheet ID from the URL
sheet_id = "1-Lk9E1_p0b_bFNk2jG5zsGilIX8ImM_1RLXpP5PRQR0"
sheet = client.open_by_key(sheet_id).sheet1

def TestAppend():
    # Append a row
    sheet.append_row(["1234567890", "Alice", 5])  # [discord_id, display_name, wins]

    # Read all rows
    rows = sheet.get_all_records()
    print(rows)

    # Update specific cell
    sheet.update_cell(2, 3, 10)  # row 2, col 3 → set wins = 10
