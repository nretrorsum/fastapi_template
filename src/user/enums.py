from enum import Enum


class UserSubscription(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

    def __str__(self) -> str:
        return self.value

class UserGender(str, Enum):
    MALE = 'MALE'
    FEMALE = 'FEMALE'

    def __str__(self) -> str:
        return self.value
