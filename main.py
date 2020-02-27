from CollectData import collect_all, update


task = "download"


if task == "download":
    collect_all(300, "CSGO_Games")
elif task == "update":
    update("CSGO_Games")