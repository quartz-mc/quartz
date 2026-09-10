import uuid,msal,requests
from backend.debug import *
from backend.exceptions import *

CLIENT_ID = "28d059ea-5e3d-4ae0-a6bf-472c56a66ca0"
app = msal.PublicClientApplication(
    CLIENT_ID,
    authority="https://login.microsoftonline.com/consumers"
)

cache = []

def getCache():
    global cache
    cache = app.get_accounts()
    print("The cache is",cache)

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

def auth(msToken):
    # xbox time!

    info("Authenticating with Xbox Live...")

    response = requests.post("https://user.auth.xboxlive.com/user/authenticate",headers={
            "x-xbl-contract-version":"1",
            "Content-Type":"application/json"
        },
        json={
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType":"JWT",
            "Properties": {
                "AuthMethod":"RPS",
                "SiteName":"user.auth.xboxlive.com",
                "RpsTicket":f"d={msToken}"
            }
        })
    if response.status_code >= 300:
        warn("Failed to authenticate with Xbox! Raising for status.")
        response.raise_for_status()
    data = response.json()
    xbToken = data["Token"]

    # X-token time!

    info("Retrieving XSTS token")

    response = requests.post("https://xsts.auth.xboxlive.com/xsts/authorize",headers={
        "x-xbl-contract-version":"1",
        "Content-Type":"application/json",
    },json={
        "Properties":{
            "SandboxId":"RETAIL",
            "UserTokens":[xbToken]
        },
        "RelyingParty":"rp://api.minecraftservices.com/",
        "TokenType":"JWT"
    })
    if response.status_code >= 300:
        warn("Failed to authenticate with Xbox! Raising for status.")
        response.raise_for_status()
    data = response.json()
    xstsToken = data["Token"]
    xstsHashcode = data["DisplayClaims"]["xui"][0]["uhs"]

    identityToken = f"XBL3.0 x={xstsHashcode};{xstsToken}"

    # mc time! (auth)

    info("Authenticating with Minecraft")

    response = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox",headers={
        "Content-Type":"application/json"
    },json={
        "identityToken":identityToken
    })
    if response.status_code >= 300:
        warn("Failed to authenticate with Minecraft! Raising for status.")
        warn(response.text)
        response.raise_for_status()
    data = response.json()
    mcToken = data["access_token"]
    creds = Credentials("","",mcToken,"msa")

    info("Checking if the account owns Minecraft...")

    response = requests.get("https://api.minecraftservices.com/entitlements/mcstore",headers={
        "Authorization":f"Bearer {mcToken}"
    })
    if response.status_code >= 300:
        warn("Failed to verify ownership! Raising for status.")
        response.raise_for_status()
    data = response.json()
    if not any([x.get("name","malformed") == "game_minecraft" for x in data["items"]]):
        warn("Account does not own minecraft!")
        warn(f"mcstore entitlements are: {data}")
        return None
    info("Account owns Minecraft!")

    # mc time! (profile)

    info("Retrieving profile")

    response = requests.get("https://api.minecraftservices.com/minecraft/profile",headers={
        "Content-Type":"application/json",
        "Authorization":f"Bearer {mcToken}"
    })
    if response.status_code >= 300:
        warn("Failed to authenticate with Minecraft! Raising for status.")
        warn(response.text)
        response.raise_for_status()
    data = response.json()
    creds.username = data["name"]
    creds.uuid = data["id"]

    # raise NotImplementedError("Authentication is not supported. Please use a client mod until this feature is added.")

    return creds

def auth_new():
    info("Authenticating with microsoft...")

    result = app.acquire_token_interactive(scopes=[
        "xboxlive.signin"
    ])
    if not "access_token" in result:
        warn("Failed to authenticate with Microsoft! Result is dumped as follows.")
        warn(str(result))
        return None
    info("Successfully authenticated with Microsoft!")
    msToken = result["access_token"]

    return auth(msToken)