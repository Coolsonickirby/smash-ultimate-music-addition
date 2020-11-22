import binascii, struct, math
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from colorama import Fore
from colorama import Style
import subprocess, json
from ftplib import FTP, error_perm


def remove_ftp_dir(ftp, path):
    for (name, properties) in ftp.mlsd(path=path):
        if name in ['.', '..']:
            continue
        elif properties['type'] == 'file':
            ftp.delete(f"{path}/{name}")
        elif properties['type'] == 'dir':
            remove_ftp_dir(ftp, f"{path}/{name}")
    ftp.rmd(path)

def placeFiles(ftp, path):
    for name in os.listdir(path):
        localpath = os.path.join(path, name)
        if os.path.isfile(localpath):
            print("Uploading %s" % name)
            ftp.storbinary('STOR ' + name, open(localpath,'rb'))
            printSuccess("Uploaded %s" % name)
        elif os.path.isdir(localpath):
            print("Making directory %s" % name)
            try:
                ftp.mkd(name)
            except error_perm as e:
                if not e.args[0].startswith('550'): 
                    raise
            ftp.cwd(name)
            placeFiles(ftp, localpath)
            ftp.cwd("..")

def convertPrcToJson(prc_input, json_output):
    subprocess.call(["dotnet", "tools/prc2json/prc2json.dll", "-d", "%s" % prc_input, "-o", "%s" % json_output, "-l", "tools/ParamLabels.csv"])

def convertArrayToPrc(array, prc_output):
    with open("tmp/hold.json", "w") as outfile:
        json.dump(array, outfile)
    subprocess.call(["dotnet", "tools/prc2json/prc2json.dll", "-a", "tmp/hold.json", "-o", "%s" % prc_output, "-l", "tools/ParamLabels.csv"])

def applyXMSBTPatch(xmsbt, msbt_location):
    xmsbt_string = tostring(xmsbt, encoding='utf-16', method='xml').decode('utf-16')
    with open("tmp/hold.xmsbt", "w", encoding='utf-16') as handle:
        handle.write(xmsbt_string)
    subprocess.call(["tools/XMSBT_cli/XMSBT_cli.exe", "tmp/hold.xmsbt", "%s" % msbt_location])

def printSuccess(message):
    print(f'{Fore.GREEN}' + message + f'{Style.RESET_ALL}')

def printError(message):
    print(f'{Fore.RED}' + message + f'{Style.RESET_ALL}')

def printWarning(message):
    print(f'{Fore.YELLOW}' + message + f'{Style.RESET_ALL}')

def printTitle(message):
    print("------------------ %s ------------------" % message)

def read_from_hex_offset(file, hex_offset, bytes_to_read):
    offset = int(hex_offset, base=16)
    file.seek(offset)
    return file.read(bytes_to_read)

def write(filename,data,offset):
    try:
        f = open(filename,'r+b')
    except IOError:
        f = open(filename,'wb')
    f.seek(offset)
    f.write(data)
    f.close()

def insertHashValue(hash_name, value):
    return {
        "@hash": hash_name,
        "#text": value
    }

def hash(string):
    string_crc32 = binascii.crc32(string.encode())
    hash40 = "0x%02x%08x" % (len(string), string_crc32 % ( 1 << 32 ))    
    return hash40

def inputDefault(inputPrompt, default):
    text = input(inputPrompt)
    if text == "":
        text = default
    return text

def setup_info(song_info, info):
    if "title" in song_info:
        info["title"] = song_info["title"]
    
    if "authors" in song_info:
        info["authors"] = '\n'.join(song_info["authors"])
    
    if "copyright" in song_info:
        info["copyright"] = '\n'.join(song_info["copyright"])
    
    if "order" in song_info:
        info["order"] = song_info["order"]
    
    if "incidence" in song_info:
        info["incidence"] = song_info["incidence"]

    for a in range(16):
        if "order%d" % a in song_info:
            info["order%d" % a] = song_info["order%d" % a]

        if "incidence%d" % a in song_info:
            info["incidence%d" % a] = song_info["incidence%d" % a]

    if "special_category" in song_info:
        info["special_category"] = song_info["special_category"]
    
    if "record_type" in song_info:
        info["record_type"] = song_info["record_type"]
    
    if "game_title" in song_info:
        info["game_title"] = song_info["game_title"]

    if "info1" in song_info:
        info["info1"] = song_info["info1"]
    
    if "playlist" in song_info:
        info["playlist"] = song_info["playlist"]
    
    if "volume" in song_info:
        info["volume"] = song_info["volume"]
    
    if "album_order" in song_info:
        info["album_order"] = song_info["album_order"]



def create_struct_for_playlist(info, order_num):
    struct_arr = {"@index": "%d" % order_num}

    # Adds the hash40 fields
    struct_arr["hash40"] = insertHashValue("ui_bgm_id", hash("ui_%s" % info["file_name"]))

    # Adds the short and ushort fields
    struct_arr["short"] = []
    struct_arr["ushort"] = []

    for a in range(16):
        current_order = order_num

        if "order%d" % a in info:
            current_order = info["order%d" % a]
        elif "order" in info:
            current_order = info["order"]

        short_order = {"@hash": "order%d" % a, "#text": "%d" % current_order}
        struct_arr["short"].append(short_order)

        incidence_num = 1500

        if "incidence%d" % a in info:
            incidence_num = info["incidence%d" % a]
        elif "incidence" in info:
            incidence_num = info["incidence"]

        ushort_incidence = {"@hash": "incidence%d" % a, "#text": "%d" % incidence_num}
        struct_arr["ushort"].append(ushort_incidence)
    
    return struct_arr

def get_highest_ids(ui_bgm_db):
    msg_id_latest = 0
    save_no_latest = 0
    test_disp_order_latest = 0
    menu_value_latest = 0

    for x in ui_bgm_db["struct"]["list"][0]["struct"]:
        try:
            if int(x["string"]["#text"]) > msg_id_latest:
                msg_id_latest = int(x["string"]["#text"])
                save_no_latest = int(x["short"][0]["#text"])
                test_disp_order_latest = int(x["short"][1]["#text"])
                menu_value_latest = int(x["int"]["#text"])
        except:
            pass

    return {
        "msg_id": msg_id_latest + 1,
        "save_no": save_no_latest + 1,
        "test_disp_order": test_disp_order_latest + 1,
        "menu_value": menu_value_latest + 1
    }

def add_song_to_files(ui_bgm_db, bgm_property, xmsbt, info, nus3bank_id):
    
    if "authors" in info:
        info["authors"] = '\n'.join(info["authors"])
    
    if "copyright" in info:
        info["copyright"] = '\n'.join(info["copyright"])
    
    #region BGM Struct 0
    struct_0_index = int(ui_bgm_db["struct"]["list"][0]["struct"][-1]["@index"]) + 1

    latest_ids = get_highest_ids(ui_bgm_db)

    game_title = "ui_gametitle_none"

    if "game_title" in info:
        if info["game_title"].startswith("0x") == False:
            game_title = hash(info["game_title"])
        else:
            game_title = info["game_title"]

    bgm_struct_0 = {
        "@index": struct_0_index,
        "hash40": [
            insertHashValue("ui_bgm_id", hash("ui_%s" % info["file_name"])),

            insertHashValue("stream_set_id", hash(info["file_name"].replace("bgm_", "set_"))),
            
            insertHashValue("rarity", "0x0cfa5acb4d"),

            insertHashValue("record_type", info["record_type"] if "record_type" in info else "record_original" ),

            insertHashValue("ui_gametitle_id", game_title),
            
            insertHashValue("ui_gametitle_id_1", ""),
            
            insertHashValue("ui_gametitle_id_2", ""),
            
            insertHashValue("ui_gametitle_id_3", ""),
            
            insertHashValue("ui_gametitle_id_4", ""),

            insertHashValue("0x0ff71e57ec", ""),

            insertHashValue("0x14341640b8", ""),

            insertHashValue("0x1560c0949b", "")
        ],
        "string": insertHashValue("name_id", latest_ids["msg_id"]),
        "short": [
            insertHashValue("save_no", latest_ids["save_no"]),
            insertHashValue("test_disp_order", info["album_order"] if "album_order" in info else latest_ids["test_disp_order"])
        ],
        "int": insertHashValue("menu_value", latest_ids["menu_value"]),
        "bool": [
            insertHashValue("jp_region", "True"),
            insertHashValue("other_region", "True"),
            insertHashValue("possessed", "False"),
            insertHashValue("prize_lottery", "False"),
            insertHashValue("count_target", "True"),
            insertHashValue("0x187162d1e8", "False"),
            insertHashValue("0x18db285704", "True"),
            insertHashValue("0x16fe9a28fe", "True"),
            insertHashValue("is_dlc", "False"),
            insertHashValue("is_patch", "False"),
        ],
        "uint": insertHashValue("shop_price", "0"),
        "byte": insertHashValue("menu_loop", "1")
    }


    ui_bgm_db["struct"]["list"][0]["struct"] = [bgm_struct_0] + ui_bgm_db["struct"]["list"][0]["struct"]
    #endregion

    #region BGM Stuct 2
    struct_2_index = int(ui_bgm_db["struct"]["list"][2]["struct"][-1]["@index"]) + 1

    bgm_struct_2 = {
        "@index": struct_2_index,
        "hash40": [
            insertHashValue("stream_set_id", hash(info["file_name"].replace("bgm_", "set_"))),
            insertHashValue("special_category", info["special_category"] if "special_category" in info else "" )
        ]
    }
    for x in range(16):
        if x == 0:
            bgm_struct_2["hash40"].append(insertHashValue("info%d" % x, hash(info["file_name"].replace("bgm", "info"))))
        else:
            bgm_struct_2["hash40"].append(insertHashValue("info%d" % x, hash(info["info%d" % x]) if ("info%d" % x) in info else ""))


    ui_bgm_db["struct"]["list"][2]["struct"].append(bgm_struct_2)
    #endregion

    #region BGM Struct 3
    struct_3_index = int(ui_bgm_db["struct"]["list"][3]["struct"][-1]["@index"]) + 1
    bgm_struct_3 = {
        "@index": struct_3_index,
        "hash40": [
            insertHashValue("info_id", hash(info["file_name"].replace("bgm_", "info_"))),
            insertHashValue("stream_id", hash(info["file_name"].replace("bgm_", "stream_"))),
            insertHashValue("condition", "sound_condition_none"),
            insertHashValue("condition_process", "0x1b9fe75d3f")
        ],
        "int": [
            insertHashValue("start_frame", "0"),
            insertHashValue("change_fadein_frame", "0"),
            insertHashValue("change_start_delay_frame", "0"),
            insertHashValue("change_fadeout_frame", "55"),
            insertHashValue("change_stop_delay_frame", "0"),
            insertHashValue("menu_change_fadein_frame", "0"),
            insertHashValue("menu_change_start_delay_frame", "0"),
            insertHashValue("menu_change_fadeout_frame", "55"),
            insertHashValue("0x1c6a38c480", "0"),
        ]
    }
    ui_bgm_db["struct"]["list"][3]["struct"].append(bgm_struct_3)
    #endregion

    #region BGM Struct 4
    struct_4_index = int(ui_bgm_db["struct"]["list"][4]["struct"][-1]["@index"]) + 1
    bgm_struct_4 = {
        "@index": struct_4_index,
        "hash40": insertHashValue("stream_id", hash(info["file_name"].replace("bgm_", "stream_"))),
        "string": [
            insertHashValue("data_name0", info["file_name"].replace("bgm_", "")),
            insertHashValue("data_name1", ""),
            insertHashValue("data_name2", ""),
            insertHashValue("data_name3", ""),
            insertHashValue("data_name4", ""),
            insertHashValue("end_point", "00:00:33.869"),
            insertHashValue("0x17c3bb5007", ""),
            insertHashValue("0x168fd4b6b0", "00:00:22.025"),
            insertHashValue("start_point0", ""),
            insertHashValue("start_point1", ""),
            insertHashValue("start_point2", ""),
            insertHashValue("start_point3", ""),
            insertHashValue("start_point4", "")
        ],
        "byte": insertHashValue("loop", "1"),
        "ushort": insertHashValue("fadeout_frame", "400")
    }
    ui_bgm_db["struct"]["list"][4]["struct"].append(bgm_struct_4)
    #endregion

    #region Add Song to Playlist
    if "playlist" in info:
        for playlist in info["playlist"]:
            found_playlist = False
            for x in ui_bgm_db["struct"]["list"][6:]:
                if x["@hash"] == playlist or x["@hash"] == hash(playlist):
                    struct_arr = create_struct_for_playlist(info, len(x["struct"]))
                    found_playlist = True
                    x["struct"].append(struct_arr)
            if found_playlist == False:
                printWarning("\t Couldn't find %s - Creating it" % playlist)
                new_entry = {
                    "@size": "0",
                    "@hash": hash(playlist),
                    "struct": [create_struct_for_playlist(info, info["order"] if "order" in info else 0)]
                }
                ui_bgm_db["struct"]["list"].append(new_entry)
            
    #endregion

    if "title" in info:
        title = SubElement(xmsbt, "entry", {"label": "bgm_title_%s" % latest_ids["msg_id"]})
        value = SubElement(title, "text")
        value.text = info["title"]
    if "authors" in info:
        authors = SubElement(xmsbt, "entry", {"label": "bgm_author_%s" % latest_ids["msg_id"]})
        value = SubElement(authors, "text")
        value.text = info["authors"]
    if "copyright" in info:
        copyright_entry = SubElement(xmsbt, "entry", {"label": "bgm_copyright_%s" % latest_ids["msg_id"]})
        value = SubElement(copyright_entry, "text")
        value.text = info["copyright"]

    # Get values from nus3audio directly (for bgm_property)
    print("\t - Parsing %s.nus3audio" % info["file_name"])
    nus3audio_file = open("output/stream;/sound/bgm/%s.nus3audio" % info["file_name"], "rb")
    
    # Move to song offset value
    nus3audio_file.seek(int("0x38", base=16))
    
    # Store song offset for returning later
    song_offset = int.from_bytes(nus3audio_file.read(1), "little")

    # Jump from song offset value to actual song
    nus3audio_file.seek(song_offset)

    # Get song type (Lopus or IDSP)
    song_format = nus3audio_file.read(4)

    total_samples = 0
    loop_start_samples = 0
    loop_end_samples = 0
    sample_rate = 48000

    if song_format == b'OPUS':
        printSuccess("\t OPUS song detected! Parsing Information for bgm_property")
        # Skip to total samples
        nus3audio_file.seek(song_offset + 8)
        total_samples = struct.unpack(">I", nus3audio_file.read(4))[0]

        # Skip channels
        nus3audio_file.read(4)

        # Read the Sample Rate, Loop Start, and Loop End
        sample_rate = struct.unpack(">I", nus3audio_file.read(4))[0] 
        loop_start = struct.unpack(">I", nus3audio_file.read(4))[0]
        loop_end = struct.unpack(">I", nus3audio_file.read(4))[0]
    elif song_format == b'IDSP':
        print("\t IDSP song detected! Parsing Information for bgm_property")

        # Skip to sample rate
        nus3audio_file.seek(song_offset + 12)
        # Read Sample Rate
        sample_rate = struct.unpack(">I", nus3audio_file.read(4))[0]

        # Read the Total Samples, Loop Start, and Loop End
        total_samples = struct.unpack(">I", nus3audio_file.read(4))[0]
        loop_start = struct.unpack(">I", nus3audio_file.read(4))[0]
        loop_end = struct.unpack(">I", nus3audio_file.read(4))[0]


    loop_start_ms = int((loop_start / sample_rate) * 1000)
    loop_end_ms = int((loop_end / sample_rate) * 1000)
    total_samples_ms = int((total_samples / sample_rate) * 1000)

    print("\t - Sample Rate: %20s" % sample_rate)
    print("\t - Loop Start: %21s" % loop_start)
    print("\t - Loop Start (ms): %16s" % loop_start_ms)
    print("\t - Loop End: %23s" % loop_end)
    print("\t - Loop End (ms): %18s" % loop_end_ms)
    print("\t - Total Samples: %18s" % total_samples)
    print("\t - Total Samples (ms): %13s" % total_samples_ms)
    
    bgm_property_entry = {
        'name_id': info["file_name"].replace("bgm_", ""),
        "loop_start_ms": loop_start_ms,
        "loop_start_sample": loop_start,
        "loop_end_ms": loop_end_ms,
        "loop_end_sample": loop_end,
        "total_time_ms": total_samples_ms,
        "total_samples": total_samples
    }

    bgm_property.append(bgm_property_entry)
    
    nus3bank_path = "output/stream;/sound/bgm/%s.nus3bank" % info["file_name"]
    
    write(nus3bank_path, int(nus3bank_id).to_bytes(4, byteorder='little', signed=False), int("0xC4", base=16))
    
    if "volume" in info:
        write(nus3bank_path, struct.pack("<f", float(info["volume"])), int("0x3D38", base=16))