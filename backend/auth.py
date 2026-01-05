import uuid

class Credentials:
    def __init__(self,username,uuid,accessToken,userType):
        self.username = username
        self.uuid = uuid
        self.accessToken = accessToken
        self.userType = userType
        self.extras = "" # extra arguments

def offline(username):
    offlineUUID = uuid.uuid3(uuid.NAMESPACE_DNS,f"OfflinePlayer:{username}").hex
    accessToken = "0"
    userType = "legacy"
    return Credentials(username,offlineUUID,accessToken,userType)