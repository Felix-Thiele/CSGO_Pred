from CollectData import collect_all, update


task = "update"


if task == "download":
    collect_all(300, "CSGO_Games")
elif task == "update":
    update("CSGO_Games")