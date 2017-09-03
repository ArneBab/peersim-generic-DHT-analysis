from flask import send_file

def home_handler():
    '''
    Home handler, Return landing page
    '''
    return send_file('static/index.html')
