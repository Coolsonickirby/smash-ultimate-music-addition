import toml, os, sys, subprocess, yaml, json, codecs, shutil
from utils import *
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from shutil import copyfile
from ftplib import FTP, error_perm

def credits():
    printTitle("Smash Ultimate Music Addition Script")
    print("Main Script Writer:%22s" % "Coolsonickirby/Random")
    print("Add Song Section:%33s" % "Coolsonickirby/Random & soneek")
    print("Research:%17s" % "soneek")
    print("\tTools Used:")
    print("\t\tprc2json:%35s" % "arthur!")
    print("\t\tXMSBT_cli:%34s" % "IcySon55, exelix11")
    print("\t\tbgm-smash-property:%25s" % "jam1garner")

credits()
printTitle("Starting the Main Script")
music_folder = inputDefault("Enter the music folder name (music): ", "music")

if os.path.exists("output"):
    printTitle("Removing output folder")
    shutil.rmtree("output", ignore_errors=True)
    printSuccess("Deleted output folder!")

if os.path.exists("tmp"):
    shutil.rmtree("tmp", ignore_errors=True)


printTitle("Creating output and tmp folders")
try:
    os.makedirs("output/ui/message")
except:
    printWarning("output/ui/message already exists!")
try:
    os.makedirs("output/ui/param")
except:
    printWarning("output/ui/param already exists!")
try:
    os.makedirs("output/stream;/sound/bgm")
except:
    printWarning("output/stream;/sound/bgm already exists!")
try:
    os.makedirs("output/sound/config")
except:
    printWarning("output/sound/config already exists!")
try:
    os.makedirs("tmp")
except:
    printWarning("tmp already exists!")

printSuccess("Created output and tmp folders!")

latest_id = 11003
new_songs_added = 0

bgm_property = []
ui_bgm_db = []
ui_gametitle_db = []
all_songs_in_db = []
all_titles_in_db = []
order_library = {}
bgm_xmsbt_root = Element("xmsbt")
title_xmsbt_root = Element("xmsbt")
config_toml = {}
config_series = {}
ftp_info = toml.load("config_ftp.toml")
used_ftp = False

#region Setting up Info
# Convert bgm_property.bin to bgm_prop.yaml
printTitle("Converting bgm_property.bin")
subprocess.call(["tools/bgm-property.exe", "files/bgm_property.bin", "tmp/bgm_prop.yaml"])
printSuccess("Converted bgm_property!")

# Convert ui_bgm_db.prc and ui_gametitle_db.prc to json files
printTitle("Converting prc files")
print("Starting ui_bgm_db.prc conversion")
convertPrcToJson("files/ui_bgm_db.prc", "tmp/ui_bgm_db.json")
printSuccess("Converted ui_bgm_db!")
print("Starting ui_gametitle_db.prc conversion")
convertPrcToJson("files/ui_gametitle_db.prc", "tmp/ui_gametitle_db.json")
printSuccess("Converted ui_gametitle_db!")

# Opens converted yaml and stores it in array
printTitle("Reading bgm_property")
with open("tmp/bgm_prop.yaml", 'r') as stream:
    try:
        bgm_property = yaml.safe_load(stream)
        printSuccess("Read bgm_property!")
    except yaml.YAMLError as exc:
        printError(exc)
        exit()

# Opens the decompressed prc files above and stores it in it's respective array variable
printTitle("Reading prc files")
print("Reading ui_bgm_db")
with open("tmp/ui_bgm_db.json") as json_file:
    ui_bgm_db = json.load(json_file)
printSuccess("Read ui_bgm_db successfully!")

print("Reading ui_gametitle_db")
with open("tmp/ui_gametitle_db.json") as json_file:
    ui_gametitle_db = json.load(json_file)
printSuccess("Read ui_gametitle_db successfully!")
#endregion

#region Adding all songs and gametitles to arrays for dupe reasons
printTitle("Adding all current songs to database")
for x in bgm_property:
    value = x["name_id"]
    if value.startswith("0x"):
        all_songs_in_db.append(value)
    else:
        all_songs_in_db.append(hash(value.replace("ui_", "")))
printSuccess("Added all current songs to database!")

printTitle("Adding all gametitles to database")
for x in ui_gametitle_db["struct"]["list"]["struct"]:
    game_title = x["hash40"][0]["#text"]
    if game_title.startswith("0x"):
        all_titles_in_db.append(game_title)
    else:
        all_titles_in_db.append(hash(game_title))
printSuccess("Added all current gametitles to database!")
#endregion

#region Loading all config files
printTitle("Loading all config files")
for subdir, dirs, files in os.walk(music_folder):
    for filename in files:
        filepath = subdir + os.sep + filename

        if filename.endswith(".toml"):
            config_array = toml.load(filepath)
            config_toml.update(config_array)
            if "series" in config_array:
                config_series.update(config_array["series"])
            printSuccess("Loaded %s" % filename)
printSuccess("Loaded all config files!")
#endregion

#region Adding new gametitles
if bool(config_series):
    printTitle("Adding new gametitles")
    for x in config_series:

        entry = config_series[x]

        if hash(x) in all_titles_in_db:
            printWarning("Ignoring %s as it is already in the database" % x)
            continue

        if "display_name" not in entry:
            printWarning("display_name key not found in %s! Defaulting to \"Missing\"" % x)

        ui_series_id = "ui_series_none"
        name_id = entry["name_id"] if "name_id" in x else x.replace("ui_gametitle_", "")

        if "ui_series_id" in entry:
            if entry["ui_series_id"].startswith("0x"):
                ui_series_id = entry["ui_series_id"]
            else:
                ui_series_id = hash(entry["ui_series_id"])


        new_title = {
          "@index": "0",
          "hash40": [
            {
              "@hash": "ui_gametitle_id",
              "#text": "%s" % x if x.startswith("0x") else hash(x)
            },
            {
              "@hash": "ui_series_id",
              "#text": "%s" % ui_series_id
            }
          ],
          "string": {
            "@hash": "name_id",
            "#text": "%s" % name_id
          },
          "bool": {
            "@hash": "0x1c38302364",
            "#text": "%s" % entry["some_bool"] if "some_bool" in x else "True"
          },
          "int": {
            "@hash": "release",
            "#text": "%s" % entry["release"] if "release" in entry else "1"
          }
        }

        title = SubElement(title_xmsbt_root, "entry", {"label": "tit_%s" % name_id})
        value = SubElement(title, "text")
        value.text = entry["display_name"] if "display_name" in entry else "Missing"

        ui_gametitle_db["struct"]["list"]["struct"].append(new_title)
        printSuccess("Added %s to gametitle database!" % x)
#endregion

#region Adding Order & Incidence Library
for x in config_toml:
    item = {
        hash("ui_%s" % x): {

        }
    }

    for y in range(16):
        if "order%d" % y in config_toml[x]:
            item[hash("ui_%s" % x)].update({"order%d" % y: config_toml[x]["order%d" % y]})
        if "incidence%d" % y in config_toml[x]:
            item[hash("ui_%s" % x)].update({"incidence%d" % y: config_toml[x]["incidence%d" % y]})

    order_library.update(item)
#endregion

# Look for and add music files
printTitle("Adding Music")
for subdir, dirs, files in os.walk(music_folder):
    files_nus3audio = []

    for n in range(len(files)):
        if files[n].endswith(".nus3audio") and hash(files[n][:-10]) not in all_songs_in_db:
            files_nus3audio.append(files[n]) 
    
    for filename in files_nus3audio:
        filepath = subdir + os.sep + filename
        
        info = {}

        if filename.endswith(".nus3audio") and hash(filename[:-10]) not in all_songs_in_db:
            copyfile(filepath, "output/stream;/sound/bgm/%s" % filename)
            info["file_name"] = filename[:-10]
            copyfile("files/base.nus3bank", "output/stream;/sound/bgm/%s.nus3bank" % info["file_name"])
            if info["file_name"] in config_toml:
                song_info = config_toml[info["file_name"]]
                info.update(song_info)

            latest_id += 1
            new_songs_added += 1
            print("Adding %s" % info["file_name"])
            print("\t - ID: %d" % latest_id)
            
            if "title" in info:
                print("\t - Title: %s" % info["title"])

            if "record_type" in info:
                print("\t - Record Type: %s" % info["record_type"])

            if "special_category" in info:
                print("\t - Special Category: %s" % info["special_category"])
            
            add_song_to_files(ui_bgm_db, bgm_property, bgm_xmsbt_root, info, latest_id)
            printSuccess("Successfully added %s" % info["file_name"] )
        elif hash(filename[:-10]) in all_songs_in_db:
            printWarning("Ignoring %s (already in the game)" % filename[:-10])
printSuccess("Added Music!")

#region Reordering Songs and updating incidences
for x in ui_bgm_db["struct"]["list"][6:]:
    for y in x["struct"]:
        try:
            current_hash = y["hash40"]["#text"] if y["hash40"]["#text"].startswith("0x") else hash(y["hash40"]["#text"])
            if current_hash in order_library:
                for z in range(16):
                    y["short"][z]["#text"] = order_library[current_hash]["order%d" % z] if "order%d" % z in order_library[current_hash] else y["short"][z]["#text"]
                    y["ushort"][z]["#text"] = order_library[current_hash]["incidence%d" % z] if "incidence%d" % z in order_library[current_hash] else y["ushort"][z]["#text"]
        except:
            printError("Failed parsing playlist %s!" % x["@hash"])
#endregion

# Save modified bgm_property
printTitle("Saving bgm_property")
with open("tmp/bgm_prop.yaml", 'w') as file:
    yaml.dump(bgm_property, file)
subprocess.call(["tools/bgm-property.exe", "tmp/bgm_prop.yaml", "output/sound/config/bgm_property.bin"])
printSuccess("Saved bgm_property!")

# Save modified ui_bgm_db and ui_gametitle_db
printTitle("Saving prc files")
print("Saving ui_bgm_db")
convertArrayToPrc(ui_bgm_db, "output/ui/param/database/ui_bgm_db.prc")
printSuccess("Saved ui_bgm_db!")
print("Saving ui_gametitle_db")
convertArrayToPrc(ui_gametitle_db, "output/ui/param/database/ui_gametitle_db.prc")
printSuccess("Saved ui_gametitle_db!")

# Save new MSBT File
printTitle("Applying XMSBT Patches to msbt files")
print("Applying patch to msg_bgm.msbt")
copyfile("files/msg_bgm.msbt", "output/ui/message/msg_bgm.msbt")
applyXMSBTPatch(bgm_xmsbt_root, "output/ui/message/msg_bgm.msbt")
printSuccess("Patch applied to msg_bgm.msbt successfully!")
if len(list(title_xmsbt_root)) > 0:
    print("Applying patch to msg_title.msbt")
    copyfile("files/msg_title.msbt", "output/ui/message/msg_title.msbt")
    applyXMSBTPatch(title_xmsbt_root, "output/ui/message/msg_title.msbt")
    printSuccess("Patch applied to msg_title.msbt successfully!")
else:
    copyfile("files/msg_title.msbt", "output/ui/message/msg_title.msbt")
    printWarning("No new gametitles detected. Ignoring msg_title.msbt")


printTitle("Deleting tmp folder")
shutil.rmtree("tmp", ignore_errors=True)
printSuccess("Deleted tmp folder successfully!")

yes_response = ["yes", "y", "true"]
invalid_paths_delete = ["/", "./", ".", "", " "]

if bool(ftp_info):
    printTitle("FTP Transfer")
    connect = ftp_info["ftp_autoconnect"] if "ftp_autoconnect" in ftp_info else "N" 
    
    if connect.lower() not in yes_response:
        connect = inputDefault("Would you like to connect and transfer the output folder with FTP? (y/N) ", "N")

    if connect.lower() in yes_response:
        used_ftp = True
        ftp = FTP()
        print("Connecting to FTP Server...")
        try:
            printSuccess(ftp.connect(ftp_info["ftp_server"], ftp_info["ftp_port"]))
            print("Logging in...")
            printSuccess(ftp.login(ftp_info["ftp_username"], ftp_info["ftp_password"]))

            if ftp_info["ftp_clean_dir"].lower() in yes_response and ftp_info["ftp_path_upload"] not in invalid_paths_delete:
                
                if ftp_info["ftp_clean_dir_no_prompt"].lower() in yes_response:
                    make_sure = 'y'
                else:
                    make_sure = inputDefault("ARE YOU SURE YOU WANT TO DELETE EVERYTHING IN %s ? (y/N) " % ftp_info["ftp_path_upload"], "N")
                
                if make_sure.lower() in yes_response:
                    try:
                        remove_ftp_dir(ftp, ftp_info["ftp_path_upload"])
                    except:
                        pass
            elif ftp_info["ftp_path_upload"] in invalid_paths_delete:
                printError("Will not clean an invalid path. If need be, then edit the script manually.")

            print("Navigating to %s" % ftp_info["ftp_path_upload"])
            try:
                ftp.mkd(ftp_info["ftp_path_upload"])
            except error_perm as e:
                if not e.args[0].startswith('550'): 
                    raise
            ftp.cwd(ftp_info["ftp_path_upload"])

            print("Starting Upload")
            placeFiles(ftp, "output")
        except:
            e = sys.exc_info()[0]
            printError("Couldn't Connect to FTP Server. Reason: %s" % e)


printTitle("Final Information")
print("Music Folder Used: %15s" % music_folder)
print("New Songs Added: %17d" % new_songs_added)
print("Output Folder: %19s" % "output")
if used_ftp:
    print("FTP Path Upload: %15s" % ftp_info["ftp_path_upload"])