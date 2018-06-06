import facebook
from datetime import datetime

APP_ID = input("App id:\n")
APP_SECRET = input("App_secret:\n")

# Identificador de acceso de usuario, obtenido desde https://developers.facebook.com/tools/explorer/393578891095032

short_lived_token = input("Introduce el identificador de acceso de usuario, obtenido con la cuenta de hackatonita desde \nhttps://developers.facebook.com/tools/explorer/393578891095032:\n")

graph = facebook.GraphAPI(short_lived_token)
response = graph.extend_access_token(APP_ID, APP_SECRET)
extended_token = response['access_token']
expiration = graph.debug_access_token(extended_token, APP_ID, APP_SECRET)['data']['expires_at']

print("Long lived token: " + extended_token)
print("Expiration date: {}".format(datetime.fromtimestamp(expiration)))
