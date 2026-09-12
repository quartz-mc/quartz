import requests,time
from backend import brand

def apiGet(endpoint:str,params=None):
    headers = {
        "User-Agent":f"quartz-mc/{brand.brand.brand}/{brand.brand.version} (xenith.contact.mail@gmail.com)"
    }
    response = requests.get(endpoint,params,headers=headers)
    # print(response.headers)
    remaining = int(response.headers.get("X-Ratelimit-Remaining",30))
    total = int(response.headers.get("X-Ratelimit-Limit",30))
    reset = int(response.headers.get("X-Ratelimit-Reset",5))
    if reset == 0: reset = 60
    if reset > 1000000: # probably a timestamp or an error
        reset = reset-time.time()
        if reset > 1000000 or reset < 0: # definitely an error
            reset = 300
    perSecond = remaining/reset/2.0
    timeout = max(0.1,1/perSecond)
    print("...anti-ratelimit timeout is",timeout,f"({remaining} requests left out of {total})")
    time.sleep(timeout)
    return response

def apiPost(endpoint:str,params=None):
    headers = {
        "User-Agent":f"quartz-mc/{brand.brand.brand}/{brand.brand.version} (xenith.contact.mail@gmail.com)"
    }
    response = requests.get(endpoint,params,headers=headers)
    remaining = response.headers.get("x-ratelimit-remaining",30)
    reset = response.headers.get("x-ratelimit-reset")
    if reset > 1000000: # probably a timestamp or an error
        reset = time.time()-reset
        if reset > 1000000 or reset < 0: # definitely an error
            reset = 300
    perSecond = remaining/reset/2.0
    time.sleep(max(0.1,1/perSecond))
    return response