# import the required libraries
from __future__ import print_function
import pickle
import os.path
import io
import shutil

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import docxcompose.composer
from docx import Document as Document_compose
import tools


REPERTOIRE = "../google/"
SCOPES = ['https://www.googleapis.com/auth/drive']
CLE = "client_secret.json"
DOWNLOAD = True

def get_credentials():
    """Ouvre les authorisations pour l'accès à l'API Google Docs/Drive"""
    # Variable self.creds will
    # store the user access token.
    # If no valid token found
    # we will create one.
    creds = None

    # The file token.pickle stores the
    # user's access and refresh tokens. It is
    # created automatically when the authorization
    # flow completes for the first time.

    # Check if file token.pickle exists
    if os.path.exists('token.pickle'):
        # Read the token from the file and
        # store it in the variable self.creds
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials are available,
    # request the user to log in.
    if not creds or not creds.valid:

        # If token is expired, it will be refreshed,
        # else, we will request a new one.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(REPERTOIRE + CLE, SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the access token in token.pickle
    # file for future usage
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

    return creds


def download_file_docx(service, file_id, file_name):
    request = service.files().export_media(fileId=file_id,
                                                mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    fh = io.BytesIO()

    # Initialise a downloader object to download the file
    downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
    done = False

    try:
        # Download the data in chunks
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)

        # Write the received data to the file
        with open(file_name, 'wb') as f:
            shutil.copyfileobj(fh, f)

        print(f"Fichier {file_name} téléchargé")
        # Return True if file Downloaded successfully
        return True

    except:
        # Return False if something went wrong
        print(f"Pb: fichier {file_name} non téléchargé")
        return False


def main():
    # Récupère la liste des fiches à télécharger
    fiches = tools.get_download_information()

    # Se connecte à google
    creds = get_credentials()

    # Connect to the API service (ici le drive)
    service = build('drive', 'v3', credentials=creds)

    # Lit les fichiers dispo sur le drive
    # results = service.files().list(pageSize=100, fields="files(id, name)").execute()
    # items = results.get('files', [])
    # print(*items, sep="\n", end="\n\n")

    # Download d'un fichier
    if DOWNLOAD:
        print("***Etape 1*** Téléchargement des fiches depuis google drive")
        nbre_telecharge = 0
        for f in fiches:
            f_id = fiches[f]["idf"] # "1Ddks5BOdAVCA6p4nFAbDx0PqQ71-pKirSu-nrdQ0JLQ" # input("Enter file id: ")
            f_name = REPERTOIRE + f"{f}.docx" # nom du fichier
            if os.path.exists(f_name):
                os.remove(f_name) # supprime le fichier
            res = download_file_docx(service, f_id, f_name)
            if res:
                nbre_telecharge += 1

        print(f"** Fin avec {nbre_telecharge} fichiers téléchargés / {len(fiches)}**")

    print("***Etape 2*** Création d'une compilation des ressources")
    compilation_ressources = Document_compose()
    compilation_saes = Document_compose()
    composer_ressources = docxcompose.composer.Composer(compilation_ressources)
    composer_saes = docxcompose.composer.Composer(compilation_saes)


    count = 0
    for f in fiches:
        f_name = REPERTOIRE + f"{f}.docx"
        docu = Document_compose(f_name)
        docu.add_page_break()

        if "R" in f:
            composer_ressources.append(docu)
        else:
            composer_saes.append(docu)

    print(count)
    composer_ressources.save("ressources.docx")
    composer_saes.save("saes.docx")


if __name__=="__main__":
    main()
