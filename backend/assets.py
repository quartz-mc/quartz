import json,urllib.request,os

def download(target="assets/objects",index="assets/index/index.json"):
    print("\n# Downloading assets\n")
    with open(index,"r") as f:
        js = json.load(f)
    objs = js["objects"]
    length = len(objs)
    i = 0
    for key,object in objs.items():
        i += 1
        hash = object["hash"]
        os.makedirs(os.path.join(target,f"{hash[:2]}"),exist_ok=True)
        if os.path.exists(os.path.join(target,f"{hash[:2]}/{hash}")): continue
        print(f"- Downloading asset {hash} ({i}/{length}; {(i/length)*100}%)")
        urllib.request.urlretrieve(f"https://resources.download.minecraft.net/{hash[:2]}/{hash}",os.path.join(target,f"{hash[:2]}/{hash}"))