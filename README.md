# pydrive-demo
Setting up directory syncing with Google Drive using PyDrive

## Setup
The setup involves creating an authorization flow and setting up the local environment with the required libraries.

### Setting up authorization
To enable API calls by PyDrive to access the Google Drive content, you need to set up authentication.
1. Go to Google's developers' console and create a new project.
2. While in the dashboard of this newly created project, go to `Enable APIs & Services`.
3. Search for and enable the Google Drive API.
4. Now, back in the dashboard of the project, you need to create credentials so click on that.
5. It'll ask you some details about what API do you need the credentials for. Answer those while keeping in mind that this project will kind of be an application that will ask the user (you yourself in this case) to give permission to access the contents of their drive.
6. Enter other details like the app name, developer details, etc.
7. Under `Scopes`, add the ./auth/drive scope so that you can access and modify **all** your drive files. (Hence, BE CAREFUL while using this app!)
8. Under `Application Type` select `Desktop App`. Click `Done` and you should have a client ID ready.
9. From the project's OAuth Client IDs list, download the `client_secret` file.
10. From the `client_secret_xxx.json` file, fill in the client_id and client_secret in the [settings.yaml](settings.yaml) file.

Authorization is done.

### Setting up the local environment
Create a virtual environment using the [req.txt](req.txt) file.

## Using the sync service
[`main.py`](main.py) syncs (to an extent) the contents of the `LOCAL_DIR` directory (present locally) and the `SERVER_ID` directory ID obtained from a Google Drive URL. This service **DOES NOT** perform any destructive action! Only creates files & directories.

### What's happening in the background:
* We list out the files & dirs in the `LOCAL_DIR` and `SERVER_ID` (in Drive)
* We upload any new files on the PC and download any new files from the Drive folder
* For any conflicting files, no changes are made (for now...)
* Then, any new local directories are uploaded (recursively i.e. all their content is uploaded)
* Then any new server directories are downloaded (recursively i.e. all their content is downloaded)
* For directories that are already present in both locations (i.e. locally and on the server) we run the entire procedure again (to manage potential changes in them).

### Additional Modifications done:
* For Drive files that are created using services like Docs, Sheets, etc.:
  - The files don't have an extension when they are stored in the Drive.
  - Such files can be identified using their `mimeType` attribute. 
  - Accordingly, when listing server files of such types, appropriate extensions are added (using the `EXTENSIONS` dictionary) to prevent unnecessary duplication due to extension mismatch

## TODOs
* When two files with the same name are found, conflict resolution can be performed by breaking ties in the following order
  - Last modified (The newer file would be kept) - would require deletion!
  - Size - in case the modified time is same, keep the larger file (rationale: editing PDFs, adding annotations would always increase file size)
  - Instead, maybe show the size as well as last modified time to the user and ask which copy(ies) to retain.
* How to handle renaming?
  - Maybe keep track of any missing files and cross reference that with the new files (based on extensions) 
    - would require indexing to keep track of what file was there the last time.
    - instead of indexing, maybe just compare files between the server and the local directory 
  - Give the user the new and missing files (extension-wise) and ask which copy to keep or whether to keep both of them.
