import os

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
drive = GoogleDrive(gauth)

# the root directory on your local machine
root_dir = "<>"

# the id of the same directory on drive
drive_root_dir_id = "<>"

# list out the folders in the directory that has an id of drive_root_dir_id
dir_list = drive.ListFile(
    {
        "q": f"'{drive_root_dir_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"
    }
).GetList()

for d in dir_list:
    if os.path.isdir(os.path.join(root_dir, d["title"])):
        # for every sub-directory in the drive dir

        # get the list of files in the sub-dir
        existing_files_list = drive.ListFile(
            {"q": f"'{d['id']}' in parents and trashed=false"}
        ).GetList()

        # extract the names of the files from all the metadata
        online_files = [x["title"] for x in existing_files_list]
        
        # list out the files currently present on the machine in the same sub-dir
        offline_files = os.listdir(os.path.join(root_dir, d["title"]))

        files_uploaded_yet = False

        # iterate over all the offline files, check if they are present in the corresponding
        # drive folder. If they are not, upload them
        for x in offline_files:
            if x in online_files:
                continue
            else:
                print(f"Uploading {x} from {d['title']}")

                # first 'create' the file and provide any metadata you want. Here, just
                # the location (using 'parents' key) and the file name (using 'title' key)
                # have been added. There are a lot of other metadata keys that can be set as
                # per the requirement.
                gfile = drive.CreateFile(
                    {
                        "parents": [{"id": f"{d['id']}"}],
                        "title": os.path.split(os.path.join(root_dir, d["title"], x))[1],
                    }
                )
                # if the title key is not set manually, the title will be set to whatever path is
                # passed into the SetContentFile() function as argument (this can include slashes so
                # better to specify the name beforehand)
                gfile.SetContentFile(os.path.join(root_dir, d["title"], x))
                gfile.Upload()
                files_uploaded_yet = True

        if not files_uploaded_yet:
            print(f"All files up to date in {d['title']}")
