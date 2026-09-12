import time,datetime
import uuid,msal,requests
from backend.debug import *
from backend.exceptions import *
from backend import config

def isoToEpoch(iso):
    return datetime.datetime.fromisoformat(iso).timestamp()

CLIENT_ID = "28d059ea-5e3d-4ae0-a6bf-472c56a66ca0"
WANTED_SCOPES = [
        "xboxlive.signin"
    ]
msal_cache = msal.SerializableTokenCache()

app = msal.PublicClientApplication(
    CLIENT_ID,
    authority="https://login.microsoftonline.com/consumers",
    token_cache=msal_cache
)

cacheFile = "caches/msal.bin"

if config.doesPathExist(cacheFile):
    with open(config.getPath(cacheFile),"r") as f:
        msal_cache.deserialize(f.read())
else:
    debug("MSAL Cache does not exist. This is probably a first launch.")

def saveCache():
    if not msal_cache.has_state_changed:
        debug("MSAL Cache has not changed state.")
        return
    with config.open(cacheFile,"w") as f:
        f.write(msal_cache.serialize())
    config.configSave("caches/others.json",others)

"""
`others.json` format
account is:
"msToken":{
    "xbToken":...
    "xbExpiry":...
    "xstsToken":...
    "xstsHashcode":...
    "xstsExpiry":...
    "mcToken":...
    "mcExpiry":...
}
"""
config.configRegister("caches/others.json","accounts",{})
config.configRegister("caches/others.json","last",None)
others = config.configLoad("caches/others.json")

cache = []

def getCache():
    global cache
    cache = app.get_accounts()
    print("The cache is",cache)
    return cache

class Credentials:
    def __init__(self,username,uuid,accessToken,userType,offline=True,demo=True):
        self.username = username
        self.uuid = uuid
        self.accessToken = accessToken
        self.userType = userType
        self.extras = "" # extra arguments
        self.offline = offline
        self.demo = demo
        self.dev = False

def offline(username):
    offlineUUID = uuid.uuid3(uuid.NAMESPACE_DNS,f"OfflinePlayer:{username}").hex
    accessToken = "0"
    userType = "legacy"
    return Credentials(username,offlineUUID,accessToken,userType)

MC_TOKEN_REFRESH_THRESHOLD = 6*60*60
OTHER_TOKEN_REFRESH_THRESHOLD = 5*60

def auth_getXbToken(msToken):
    if msToken in others:
        if "xbExpiry" in others[msToken] and others[msToken]["xbExpiry"]-OTHER_TOKEN_REFRESH_THRESHOLD > time.monotonic():
            debug("Fetched xbox token from cache.")
            return others[msToken]["xbToken"]
    else:
        others[msToken] = {}

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

    expiry = isoToEpoch(data["NotAfter"])

    others[msToken]["xbExpiry"] = expiry
    others[msToken]["xbToken"] = xbToken

    return xbToken

def auth_getXstsToken(msToken,xbToken):
    if msToken in others:
        if "xstsExpiry" in others[msToken] and others[msToken]["xstsExpiry"]-OTHER_TOKEN_REFRESH_THRESHOLD > time.monotonic():
            debug("Fetched Xsts token from cache.")
            return others[msToken]["xstsHashcode"],others[msToken]["xstsToken"]
    else:
        raise IllegalStateError("No account entry in cache after getting XbToken!")

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

    expiry = isoToEpoch(data["NotAfter"])

    others[msToken]["xstsExpiry"] = expiry
    others[msToken]["xstsHashcode"] = xstsHashcode
    others[msToken]["xstsToken"] = xstsToken

    return xstsHashcode,xstsToken

def auth_getMcToken(msToken,identityToken):
    if msToken in others:
        if "mcExpiry" in others[msToken] and others[msToken]["mcExpiry"]-MC_TOKEN_REFRESH_THRESHOLD > time.monotonic():
            debug("Fetched minecraft token from cache.")
            return others[msToken]["mcToken"]
    else:
        raise IllegalStateError("No account entry in cache after getting XbToken!")

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
    expiry = time.time() + data["expires_in"]

    others[msToken]["mcExpiry"] = expiry
    others[msToken]["mcToken"] = mcToken

    return mcToken

def auth(msToken):
    # xbox time!

    info("Authenticating with Xbox Live...")

    xbToken = auth_getXbToken(msToken)

    # X-token time!

    info("Retrieving XSTS token")

    xstsHashcode,xstsToken = auth_getXstsToken(msToken,xbToken)

    identityToken = f"XBL3.0 x={xstsHashcode};{xstsToken}"

    # mc time! (auth)

    info("Authenticating with Minecraft")

    mcToken = auth_getMcToken(msToken,identityToken)
    creds = Credentials("","",mcToken,"msa",offline=False,demo=False)

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

def auth_last():
    getCache()
    if len(cache) == 0: return None
    return auth_old(cache[-1])

def auth_old(account):
    info("Authenticating with existing Microsoft login...")
    
    result = app.acquire_token_silent(scopes=WANTED_SCOPES,account=account)
    warn(result)
    if not "access_token" in result:
        warn("Failed to authenticate with Microsoft! Result is dumped as follows.")
        warn(str(result))
        return None
    info("Successfully authenticated with Microsoft!")
    msToken = result["access_token"]

    return auth(msToken)

def auth_new():
    info("Authenticating with microsoft...")

    result = app.acquire_token_interactive(scopes=WANTED_SCOPES)
    warn(result)
    if not "access_token" in result:
        warn("Failed to authenticate with Microsoft! Result is dumped as follows.")
        warn(str(result))
        return None
    info("Successfully authenticated with Microsoft!")
    msToken = result["access_token"]

    return auth(msToken)

def shutdown():
    saveCache()