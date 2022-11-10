import os
import humanize

# to check the md5Checkum if needed
import hashlib

from datetime import datetime
from dateutil.tz import tzutc
from dateutil import parser

# MIME type - download type mapping
MIME_LOCAL_MAPPING = {
    "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
}

EXTENSIONS = {
    "application/vnd.google-apps.document": ".docx",
    "application/vnd.google-apps.spreadsheet": ".xlsx",
    "application/vnd.google-apps.presentation": ".pptx",
}


# the contents of this folder will be synced with the server_id folder
LOCAL_DIR = "/home/devin/UCSD/Q1"

# the contents of this folder in drive will be synced with the contents of the to_sync folder
SERVER_DIR = "************"


from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


gauth = GoogleAuth()
drive = GoogleDrive(gauth)

def names_match(local_name, server_obj):
    if local_name==server_obj["title"]:
        # direct match for "ordinary" files
        return True 
    else:
        # check for extensions
        if server_obj['mimeType'] in MIME_LOCAL_MAPPING:
            if local_name.endswith("docx") or local_name.endswith("xlsx") \
                    or local_name.endswith("pptx"):
                # get rid of the extension and then match
                if local_name[:-5] == server_obj["title"]:
                    return True
    
        return False

def upload(f_up, parent_id):
    """
    f_up: a list of files to upload
    parent_id: the id of the dir on the server to upload the file into
    """

    for f in f_up:
        gfile = drive.CreateFile(
                        {
                            "parents": [{"id": f"{parent_id}"}],
                            "title": os.path.split(f)[1],
                        }
                    )
        gfile.SetContentFile(f)
        gfile.Upload()
        print(f"Uploaded file: {f}")

def download(f_down, local_dest):
    """ 
    Download the list of files `f_down` into the local directory 
    `local_dest`
    """

    for f in f_down:
        file_id = f["id"]
        gfile = drive.CreateFile(
            {
            "id": file_id
            })

        download_type = None
        if f["mimeType"] in MIME_LOCAL_MAPPING:
            download_type = MIME_LOCAL_MAPPING[f["mimeType"]]

        if download_type == None:
            dest_file_path = os.path.join(local_dest, f["title"])
            gfile.GetContentFile(f"{dest_file_path}")
        else:
            dest_file_path = os.path.join(local_dest, f["title"]+EXTENSIONS[f["mimeType"]])
            gfile.GetContentFile(f"{dest_file_path}", mimetype=download_type)

        print(f"Downloaded file: {dest_file_path}")



def recursive_download(server_dir_obj, local_dest):
    """
    server_dir_obj: The server directory that needs to be downloaded
    local_dest: the local directory in which the contents need to be downloaded
    """

    dir_list = drive.ListFile(
        {
            "q": f"'{server_dir_obj['id']}' in parents and trashed=false" # and mimeType='application/vnd.google-apps.folder'
        }
    ).GetList()

    s_files = []
    s_dirs = []

    # first separate out the files and folders
    for d in dir_list:
        info = d.metadata
        if info['mimeType'] !=  'application/vnd.google-apps.folder':
            s_files.append(d)
        else:
            s_dirs.append(d)

    # create the local dir 
    local_dir_path = os.path.join(local_dest, server_dir_obj['title'])
    os.makedirs(local_dir_path)
    print(f"Created new local dir: {local_dir_path}")

    # download all the files to the newly created dir
    download(s_files, local_dir_path) 

    # recurse for new subdirs
    for d in s_dirs:
        recursive_download(d, local_dir_path)

    return

def recursive_upload(local_dir, server_dir):
    """
    local_dir: The local directory which needs to be created on the server
                Its contents need to be uploaded too.
    server_dir: The server dir id in which this new directory is to be created 
    """

    gFolder = drive.CreateFile(
        {
            "title": os.path.split(local_dir)[1], 
            "parents": [{'id': server_dir}],
            "mimeType": "application/vnd.google-apps.folder"
        }
    )
    # create the directory on the server
    gFolder.Upload()
    print(f"Directory {local_dir} created on the server.")
    
    # get the ID of the newly created directory
    # list the contents of the parent
    server_content_list = drive.ListFile(
        {
            "q": f"'{server_dir}' in parents and trashed=false" # and mimeType='application/vnd.google-apps.folder'
        }
    ).GetList()

    
    # get the ID of the directory
    new_server_dir = None
    for d in server_content_list:
        info = d.metadata
        if info['mimeType'] ==  'application/vnd.google-apps.folder':
            if info["title"] == os.path.split(local_dir)[1]:
                new_server_dir = info["id"]


    if new_server_dir == None:
        print(f"There was an error creating the dir {local_dir}")
        return

    # list the contents of the local dir
    l_files = []
    l_dirs = []

    # list out the files and dirs present locally
    for d in os.listdir(local_dir):
        if os.path.isdir(os.path.join(local_dir, d)):
            l_dirs.append(os.path.join(local_dir, d))
        else:
            l_files.append(os.path.join(local_dir, d))

    # upload the files
    upload(l_files, new_server_dir) 

    # for local subdirs, recurse
    for d in l_dirs:
        recursive_upload(d, new_server_dir)

    return

def sync_files(l_files, s_files, dest_id, local_dir):
    """"
    l_files: list of full local file paths
    s_files: list of server file objects
    dest_id: id of the folder to sync the files with
    local_dir: local directory where the files are to be synced
    """

    # get the current folder (to download new files from the server)

    curr_local_dir = local_dir

    s_names = []
    for s in s_files:
        if s["mimeType"] in MIME_LOCAL_MAPPING:
            # for office files
            s_names.append(s.metadata["title"]+EXTENSIONS[s["mimeType"]])
        else:
            # for "ordinary" files
            s_names.append(s.metadata["title"])

    l_names = []
    for l in l_files:
        l_names.append(os.path.split(l)[1])

    # conflicts i.e. file is already present on the server
    for idx, l in enumerate(l_names):
        for idx2, s in enumerate(s_names):
            if names_match(l, s_files[idx2]):
                l_t = datetime.fromtimestamp(os.path.getmtime(l_files[idx])).replace(tzinfo=tzutc())
                s_t = parser.parse(s_files[idx2].metadata['modifiedDate'])

                if l_t != s_t:
                    print(f"Resolve conflict for the file: {l_files[idx]}")

                    if l_t > s_t:
                        # local file is newer
                        # Replace the server file with the local one
                        pass
                    else:
                        # server file is newer
                        # Replace the local file with the server copy
                        pass


    # first upload new files
    to_upload = []
    for idx, l in enumerate(l_names):
        if l not in s_names:
            to_upload.append(l_files[idx])
    print("Files sending for upload:", to_upload)
    upload(to_upload, dest_id)


    # then download new files
    to_download = []
    for idx, s in enumerate(s_names):
        if s not in l_names:
            to_download.append(s_files[idx])
    print("Files incoming for download:", [x['title'] for x in to_download])
    download(to_download, curr_local_dir)

    return
    # NOTE: Possible modification: Compare file sizes and give the user a choice to leave things as is.

def sync_dirs(server_dir, local_dir):
    
    # list out the folders in the directory that has an id of drive_root_dir_id
    dir_list = drive.ListFile(
        {
            "q": f"'{server_dir}' in parents and trashed=false" # and mimeType='application/vnd.google-apps.folder'
        }
    ).GetList()

    s_files = []
    s_dirs = []

    # first separate out the files and folders
    # print("=======================")
    # print("Server contents:")
    for d in dir_list:
        info = d.metadata
        if info['mimeType'] !=  'application/vnd.google-apps.folder':
            s_files.append(d)
            # print("[FILE]", end=' ')
        else:
            s_dirs.append(d)
            # print("[DIR]", end=' ')
        # print(info['title'], ": {}".format(humanize.naturalsize(info['fileSize'])) if 'fileSize' in info else "")
    # print("=======================")

    l_files = []
    l_dirs = []

    # print("=======================")
    # print("Local contents:")
    # list out the files and dirs present locally
    for d in os.listdir(local_dir):
        if os.path.isdir(os.path.join(local_dir, d)):
            l_dirs.append(os.path.join(local_dir, d))
            # print("[DIR]", end=' ')
        else:
            l_files.append(os.path.join(local_dir, d))
            # print("[FILE]", end=' ')
        # print(d)
    # print("=======================")
        

    # print("Local dirs:", l_dirs )
    # print("Local files:", l_files )
    # print("Server dirs:", [x['title'] for x in s_dirs])
    # print("Server files:", [x['title'] for x in s_files] )

    # first sync files
    sync_files(l_files, s_files, dest_id=SERVER_DIR, local_dir=local_dir)

    l_dnames = []
    s_dnames = []
    for d in s_dirs:
        s_dnames.append(d.metadata['title'])
    for d in l_dirs:
        l_dnames.append(os.path.split(d)[1])

    # create any new dirs required
    # for idx, d in enumerate(s_dnames):
    #     if d not in l_dnames:   # directory absent locally
    #         # download_dir(d)
    #         recursive_download(s_dirs[idx], local_dir)


    for idx, d in enumerate(l_dnames):
        if d not in s_dnames:   # directory not on the server
            # upload_dir(d)
            recursive_upload(l_dirs[idx], server_dir)


    # for conflicting directories, recurse
    for idx, s in enumerate(s_dnames):
        for idx2, l in enumerate(l_dnames):
            if s == l:
                # dir is present both locally and on the server
                
                # local address of dir
                child_dir = l_dirs[idx2]
                
                # get server ID of dir 'd' = child_server_id
                child_server_id = s_dirs[idx].metadata["id"]

                sync_dirs(child_server_id, child_dir)

    return


if __name__=="__main__":

    sync_dirs(server_dir = SERVER_DIR, local_dir = LOCAL_DIR)