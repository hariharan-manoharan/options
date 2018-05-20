
#imports everything from the application folder
from application import app

app.secret_key = '$JLmL!eCQXyajbdu2LCJ&Vwqs2JGagg3B&FRfexCmKBV'

#starts the server, debug mode is on
app.debug = False
app.run(host='0.0.0.0')
