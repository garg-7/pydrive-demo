# pydrive-demo
Accessing Google Drive (listing and upload) using PyDrive

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

## Using the upload service
The sample service present in [backup.py](backup.py) is written to upload the files present in the sub-directories of a certain folder to the Google Drive folder by the same name. The directory structure for the sub-directories will be preserved. 

What's happening in the background:
* It lists out the sub-directories in the directory (in Google Drive) whose directory ID is entered.
* For every sub-dir on the remote, it attempts to list out the files present in the local sub-directory by the same name.
* If such a local sub-directory is found, it iterates over all the files present in it. If any of these files is not on the Drive, it uploads it.
* This is done for all the sub-directories of the parent (whose ID is passed in).
* If no new files are present, it just says that all files are up to date.
