import sqlite3
import uuid
import hashlib
from datetime import datetime
from typing import Tuple

def sha3_256_to_base64(h: str) -> str:
    import base64
    b64 = base64.b64encode(hashlib.sha3_256(h.encode()).digest())
    return b64.decode()

class Database:
    def __init__(self, db='database.db'):
        self.db = db
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cursor = self.conn.cursor()
    def create_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ACCOUNT (UUID TEXT, HASH TEXT, USERNAME TEXT, GEMS INTEGER DEFAULT 0, CARD INTEGER DEFAULT 0)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS REDEEMCODE(CODE TEXT PRIMARY KEY, FROMDATE TEXT, TODATE TEXT, GEMSREWARD INTEGER)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS CODEUSED (USERID INTEGER, CODE INTEGER, STATUS TEXT DEFAULT "true", FOREIGN KEY (USERID) REFERENCES ACCOUNT (ROWID), FOREIGN KEY (CODE) REFERENCES REDEEMCODE (CODE))')
    def insert_user(self, username: str, passwd: str) -> bool:
        # Insert username and passwd into table 'ACCOUNT'. Before that, calculate SHA3-256(UUID+username+passwd) then insert
        # Check if username and password is exist in database
        self.cursor.execute("SELECT UUID, HASH FROM ACCOUNT WHERE USERNAME=?", (username,))
        ans = self.cursor.fetchone()
        if ans is not None: # Exist record with the same username
            UUID = ans[0]
            HASH_db = ans[1]
            HASH_insert = sha3_256_to_base64(UUID + username + passwd)
            if HASH_db == HASH_insert: # Exist record with the same username and password
                return False
        # Create new record with new UUID and HASH
        UUID = str(uuid.uuid4())
        HASH = sha3_256_to_base64(UUID + username + passwd)
        self.cursor.execute("INSERT INTO ACCOUNT VALUES (?, ?, ?, 0, 0)", (UUID, HASH, username))
        return True
    def login(self, username: str, passwd: str) -> Tuple[str, int, int] or None:
        # self.cursor.executescript(f"SELECT UUID, HASH, GEMS, CARD FROM ACCOUNT WHERE USERNAME='{username}';")
        # Just a minor change to speed up "prepare_statement"...
        self.cursor.execute(f"SELECT UUID, HASH, GEMS, CARD FROM ACCOUNT WHERE USERNAME='{username}'")
        ans = self.cursor.fetchone()
        if ans is None:
            return None # No account with that username
        UUID = ans[0]
        HASH_db = ans[1]
        HASH_login = sha3_256_to_base64(UUID + username + passwd)
        if HASH_db == HASH_login:
            return (UUID, ans[2], ans[3])
        return None # Wrong password
    def add_code(self, code: str, fromdate: str, todate: str, gems=int) -> bool:
        self.cursor.execute("SELECT CODE FROM REDEEMCODE WHERE CODE=?", (code,))
        ans = self.cursor.fetchone()
        if ans is not None:
            return False  # Code already exists, return False
        
        self.cursor.execute("INSERT INTO REDEEMCODE VALUES (?, ?, ?, ?)", (code, fromdate, todate, gems))
        return True
    def check_code(self, code: str, uuid_cookie: str, username: str) -> str:
        # First check if UUID exists in database, I want to input username directly in database...
        self.cursor.execute(f"SELECT ROWID FROM ACCOUNT WHERE UUID=? AND USERNAME=?", (uuid_cookie, username))
        user = self.cursor.fetchone()
        if user is None:
            return "No account with that username and uuid" # No account with that username and uuid
        
        # Second check if code is exist and in active
        self.cursor.execute(f"SELECT FROMDATE, TODATE, GEMSREWARD FROM REDEEMCODE WHERE CODE='{code}'")
        ans = self.cursor.fetchone()
        if ans is None:
            return "Code didn't exist"
        fromdate = ans[0]
        todate = ans[1]
        # Convert fromdate and todate to datetime objects
        fromdate = datetime.strptime(fromdate, "%d/%m/%Y")
        todate = datetime.strptime(todate, "%d/%m/%Y")
        current_date = datetime.now().date()
        # Convert current_date to a datetime object
        current_datetime = datetime.combine(current_date, datetime.min.time())
        # Check if current_date is within the range
        if not fromdate <= current_datetime <= todate:
            return "Code is outdated"
        
        # Third check if user apply redeemcode, if not: update CODEUSED database by add user[0] and code
        self.cursor.execute("SELECT STATUS FROM CODEUSED WHERE USERID=? AND CODE=?", (user[0], code))
        status = self.cursor.fetchone()
        if status is not None:
            return "Code used"
        self.cursor.execute("INSERT INTO CODEUSED VALUES (?, ?, 'true')", (user[0], code))
        # Update gems from user
        self.cursor.execute("UPDATE ACCOUNT SET GEMS=GEMS+? WHERE UUID=? AND USERNAME=?", (ans[2], uuid_cookie, username))
        return "Redeem Successfully"
    def get_gems_and_card(self, uuid: str, username: str) -> Tuple[int, int]:
        # Get GEMS and CARD value from ACCOUNT table
        self.cursor.execute("SELECT GEMS, CARD FROM ACCOUNT WHERE UUID=? AND USERNAME=?", (uuid, username))
        ans = self.cursor.fetchone()
        if ans is not None:
            return ans[0], ans[1]
        return None, None
    def exchange_card(self, uuid: str, username: str, gems: int) -> bool:
        # Exchange 160 GEMS => 1 CARD, if successfully return True, else return False
        # Get the current number of gems and cards for the user
        current_gems, current_cards = self.get_gems_and_card(uuid, username)
        gems = int(gems)
        # Check if the user has enough gems for the exchange
        if current_gems >= gems and gems%160==0:
            # Update the gems and cards in the database
            self.cursor.execute("UPDATE ACCOUNT SET GEMS=?, CARD=? WHERE UUID=? AND USERNAME=?", (current_gems - gems, current_cards + (gems//160), uuid, username))
            return True
        else:
            return False
    def __del__(self):
        self.conn.commit()
        self.cursor.close()
if __name__ == "__main__":
    db = Database()
    db.create_table()
    print(db.insert_user("1234", "1234"))
    input()
    UUID = db.login("1234", "1234")
    print(UUID)
    input()
    UUID = UUID[0]
    db.add_code("HELLO", "12/10/2023", "14/10/2023", 1600)
    print(db.check_code("HELLO", UUID, "1234"))
    print(db.get_gems_and_card(UUID, "1234"))
    print(db.exchange_card(UUID, "1234", 3*160))
    print(db.get_gems_and_card(UUID, "1234"))
