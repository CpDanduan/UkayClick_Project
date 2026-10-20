import hashlib
from repositories.json_repository import load_users, save_users

class User:
    def __init__(self, username: str, password_hash: str, role: str = "Staff"):
        self.__username = username
        self.__password_hash = password_hash
        self.__role = role

    @property
    def username(self) -> str:
        return self.__username

    @property
    def role(self) -> str:
        return self.__role

    def login(self, password: str) -> bool:
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == self.__password_hash

    def logout(self) -> None:
        return None

    def get_username(self) -> str:
        return self.__username

    def to_dict(self) -> dict:
        return {"username": self.__username, "password_hash": self.__password_hash, "role": self.__role}

class Authentication:
    def __init__(self):
        self.__users = [User(x["username"], x["password_hash"], x.get("role", "Staff")) for x in load_users()]

    def username_exists(self, username: str) -> bool:
        return any(u.username.lower() == username.strip().lower() for u in self.__users)

    def register(self, username: str, password: str, confirm: str):
        username = username.strip()
        if not username or not password: return False, "Username and password are required."
        if password != confirm: return False, "Passwords do not match."
        if self.username_exists(username): return False, "Username already exists."
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        user = User(username, password_hash)
        self.__users.append(user)
        save_users([u.to_dict() for u in self.__users])
        return True, "Account created successfully."

    def authenticate(self, username: str, password: str):
        for user in self.__users:
            if user.username == username.strip() and user.login(password):
                return user
        return None
