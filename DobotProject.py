from __future__ import print_function
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from serial.tools import list_ports
from PIL import Image
from pydobot import Dobot
import numpy as np

import RPi.GPIO as GPIO
import time

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    #id of the Dobot Images folder
    dobot_folder_drive_id = '1uot6fLxmLA172BxzXr-HZaXcjKCCKtTE'

    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
   
    
    page_token = service.changes().getStartPageToken().execute().get('startPageToken')
    image_id= None
    print('Upload a PNG image to the Dobot Images folder in Google Drive')
    while(True):
        response = service.changes().list(pageToken=page_token,
                                                spaces='drive').execute()
        page_token= response.get('newStartPageToken')   
        change_found= False
        
        for change in response.get('changes'):
            #if the file is not a png delete file
            if ("png" not in change.get('file').get('name')):
                print('File that was uploaded was not a PNG')
                print('Deleting invalid file from Google Drive')
                deleteFile(service, change.get('file').get('id'))
                turnOnLight()
                return
        
            
            results = service.files().list( q="mimeType = 'image/png'",
                                            pageSize=10, fields="nextPageToken, files(id, name, parents)").execute()
            

            items = results.get('files', [])

            if not items:
                print('File that was uploaded was not a PNG')
                turnOnLight()
            else:
                for item in items:
                    if(item['parents'][0]==dobot_folder_drive_id):
                        change_found=True
                        #at this point, a png was uploaded to the correct folder
                        #thus, drawing can begin
                        print('PNG image successfully uploaded')
                        print('File: name: {}, id: {}'.format(item['name'], item['id']))
                        image_id= item['id']
                        print('Drawing Image')
                        try:
                            dobot()
                        except:
                            print('Could not draw image')
                            turnOnLight()
                            
                        print('Drawing Complete')
                        break
                    else:
                        print("Picture not added to correct folder")
                        turnOnLight()
                        
        if(change_found==True):
            break
    print('Deleting image from Google Drive')       
    deleteFile(service, image_id)
    
def deleteFile(service, file_id):
    try:
        service.files().delete(fileId=file_id).execute()
        print ('File Deleted')
    except:
        print ('Could not delete file')
    
def dobot():
    port = list_ports.comports()[0].device
    device = Dobot(port=port, verbose=True)

    (x, y, z, r, j1, j2, j3, j4) = device.pose()
    y+=50
    device.move_to(x , y, z, r, wait=False)
    x-=15
    device.move_to(x , y, z, r, wait=False)
    x+=30
    y+=20
    device.move_to(x , y, z, r, wait=False)
    x+=30
    y-=20
    device.move_to(x , y, z, r, wait=False)
    x-=15
    device.move_to(x , y, z, r, wait=False)
    y-=50
    device.move_to(x , y, z, r, wait=False)
    x-=30
    device.move_to(x , y, z, r, wait=False)

    device.move_to(x, y, z, r, wait=True)  # we wait until this movement is done before continuing

    device.close()
    
def turnOnLight():
    print('Light is on')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18,GPIO.OUT)
    GPIO.output(18,GPIO.HIGH)
    time.sleep(10)
    GPIO.output(18,GPIO.LOW)
               
if __name__ == '__main__':
    main()

