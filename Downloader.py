import shutil
import json
import os
import re
import base64
from zipfile import ZipFile
import faster_than_requests as requests
import PySimpleGUI as sg


class Minecraft:
    'minecraft class with all the details about modpack and the version info'

    def __init__(self, version, mp_name, mp_path):
        self.version = version
        self.mp_name = mp_name
        self.mp_path = mp_path
        self.ml_name = modloader()
        self.ml = self.version + '-' + self.ml_name
        self.img_path = mp_path + '/icon.png'


layout = [[sg.Text("Select the .zip file of the modpack"), sg.FileBrowse(file_types=(("Zip Files", '.zip'),))],
          [sg.Text("Select the folder to extract modpack into"),
           sg.FolderBrowse()],
          [sg.Button("Next"), sg.Button("Cancel")],
          [sg.ProgressBar(500, orientation='h', visible=False,
                          key='progressbar', style='winnative', size=(60, 10))],
          [sg.Output(size=(70, 30), key='output', visible=False)]]

window = sg.Window("Modpack Installer", layout)
progress_bar = window['progressbar']
output = window['output']


def mkdir_chdir(path):
    try:
        os.mkdir(path)
        os.chdir(path)
    except:
        print("Folder already exitst! Skipping...")
        os.chdir(path)


def get_data(jF_path):
    with open(jF_path) as json_file:
        # Getting data from the json file
        return json.load(json_file)


def extractor(zipPath, zipName):
    'Extracting the zip to another file with the modpack name'

    with ZipFile(zipPath) as zip:
        mkdir_chdir(zipName)
        zip.extractall()


def url_parse(projectID, fileID):
    file_url = 'https://addons-ecs.forgesvc.net/api/v2/addon/' + \
        str(projectID)+'/file/' + str(fileID)+'/download-url'

    url = requests.get2str(file_url)
    return url


def mods_install():
    i = 0
    progress_bar.Update(i, visible=True)
    output.Update(visible=True)
    for ID in data['files']:
        # parsing the url
        url = url_parse(ID['projectID'], ID['fileID'])

        file_name = os.path.basename(url.strip("'")).replace("%20", " ")

        if os.path.exists(os.getcwd() + '\\' + file_name):
            print("Skipping " + file_name + " because File already exists!")
        else:
            print("Downloading: " + file_name)
            requests.download(url, file_name)
        i = i + 500/len(data['files'])
        window.Refresh()
        progress_bar.Update(i)


def modloader():
    ml = str(data['minecraft']['modLoaders'][0]['id'])
    return ml


def add_overrides(path):
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            src_path = file_path.replace("\\overrides", "")
            print(file_path)
            shutil.move(file_path, src_path, copy_function=shutil.copytree)

        for name in dirs:
            if(name != 'overrides'):
                dir_path = os.path.join(root, name)
                src_path = dir_path.replace("\\overrides", "")
                print(dir_path)
                shutil.move(dir_path, src_path, copy_function=shutil.copytree)
            else:
                pass
    try:
        os.removedirs(os.getcwd() + '\\overrides')
        os.remove(os.getcwd() + 'modlist.html')
        os.remove(os.getcwd() + 'manifest.json')
    except:
        pass


def add_profile():

    app_data_path = os.getenv("APPDATA")
    os.chdir(app_data_path+"\\.minecraft\\")
    v_path = os.getcwd()+'\\versions\\'+minecraft.ml
    if(os.path.exists(v_path)):
        try:
            ram = sg.popup_get_text(
                "Enter The amount of ram you should allocate:", "")
        except:
            sg.popup("You did not specify ram, using default")
            ram = 2

        with open("launcher_profiles.json", 'r') as prof:
            launcher_data = json.load(prof)

        new_profile = {minecraft.mp_name: {
            "name": minecraft.mp_name,
            "icon": add_profile_img(minecraft.img_path),
            "gameDir": minecraft.mp_path,
            "lastVersionId": minecraft.ml,
            "type": "custom",
            "javaArgs": "-Xmx"+str(ram)+"G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"}
        }
        temp = launcher_data['profiles']
        temp.update(new_profile)
        launcher_data['profiles'].update(temp)
        with open("launcher_profiles.json", 'w') as prof:
            json.dump(launcher_data, prof)
    else:
        sg.PopupOK('Forge Is not installed!')

def add_profile_img(img_path):
    with open(img_path, 'rb') as image:
        encoded_str = str(base64.b64encode(image.read())).replace("b'","").replace("'","")
    browser_tag = 'data:image/png;base64,'
    return browser_tag + encoded_str

###########################################################################################################################
#                                   Entry Point for the Program Starts From Here                                          #
###########################################################################################################################


while True:
    event, values = window.read()

    if event in (None, "Cancel"):
        break

    zipPath = values['Browse']
    zipName = os.path.basename(values['Browse']).rstrip('.zip')

    folder = values['Browse0']

    # extracting to the folder specified
    mkdir_chdir(folder)

    # Extractor
    extractor(zipPath, zipName)

    # loading Data from json File

    data = get_data(os.getcwd() + '\\manifest.json')
    # Modloader name parsing
    path = folder + '/' + zipName
    minecraft = Minecraft(data['minecraft']['version'], data['name'], path)

    # Making Directories and Changing the current working directories
    mkdir_chdir('mods')
    mods_install()
    os.chdir('../')
    add_overrides(os.getcwd())
    if(sg.PopupYesNo("Do you wish to add to profile?") == "Yes"):
        add_profile()
        sg.PopupOK('Downloading Finished & profile has been added to launcher, Have Fun!')
    else:
        sg.PopupOK('Downloading Finished, Have Fun!')
    break
