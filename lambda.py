#!/usr/bin/python
# marek kuczynski
# @marekq
# www.marek.rocks
# coding: utf-8

# import neccesary libraries
import boto3
from os import environ
from time import time
from re import search
from hashlib import md5
from datetime import datetime, timedelta
from random import randint
from boto3.dynamodb.conditions import Key, Attr
from urllib.parse import unquote

# take lambda environment variables for cognito
clientid    = environ['clientid']
userpoolid  = environ['userpoolid']

# set up connections with cognito and dynamodb using boto3
cognito     = boto3.client('cognito-idp')
dynamo      = boto3.resource('dynamodb').Table(environ['dynamotable'])

# return html with a 200 code, the client headers are printed by default
def return_html(body, title, head, cookie):

    # return a cookie header if neccesary
    if len(cookie) == 0:
        h    = {'Content-Type': 'text/html', 'charset': 'utf-8'}
    else:
        h    = {'Content-Type': 'text/html', 'charset': 'utf-8', 'Set-Cookie': cookie+' ; Secure; HttpOnly'}

    # return a http 200 response code
    return {
        'statusCode': 200, 
        'body': '<html><head><style>body {font-family: Arial, Helvetica, sans-serif;}</style></head><body><center><br><h1>'+title+'</h1><br><a href = "'+url+'/home">home</a> | <a href = "'+url+'/login">login</a> | <a href = "'+url+'/register">register</a> | <a href = "'+url+'/users">all users</a> | <a href = "'+url+'/profile">your profile</a> | <a href = "'+url+'/logout">logout</a> | '+auth+'<br><br><br>'+str(body)+'</center></body></html>', 
        'headers': h
    } 
    
# get the POSTed string username and password from the headers
def get_creds(para):
    user    = ''
    pasw    = ''
    
    # split the provided username and password
    for y in para.split('&'):
        if search('username', y):
            user    = unquote(y[9:])
        elif search('password', y):
            pasw    = unquote(y[9:])
         
    return user, pasw

# check if the cookie is valid based on the full cookie string, return the user
def check_cookie(x):
    user    = x.split('&')[0].split('=')[1]
    cookie  = x.split('&')[1].split('=')[1]

    # check if the cookie is present in dynamodb
    print('check_cookie: '+str(user)+' '+str(cookie))
    x       = dynamo.query(KeyConditionExpression = Key('user').eq(user), FilterExpression= Key('cookie').eq(str(cookie)))

    # set default username 'none' if no match found
    if x['Count'] == int(0):
        print('not found '+user+' '+cookie)
        return 'none'

    # else return the user for which the cookie was found
    else:
        print('found '+user+' '+cookie)   
        return user

# generate a random cookie for the user and write it to DynamoDB.
def make_cookie(user):

    # calculate the unix timestamp
    now     = int(time())
    ttl     = now + 259200

    # calculate the expiry string for the cookie
    c       = datetime.utcnow() + timedelta(days = 3)
    exp     = c.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # generate a random string for the cookie
    rand    = str(randint(1000, 100000) * now)
    cookie  = md5(rand.encode('utf-8')).hexdigest()

    # store the current cookie value in dynamodb
    dynamo.put_item(TableName = environ['dynamotable'], 
        Item = {
            'user'      : user,
            'cookie'    : cookie,
            'ttl'       : ttl
        }
    )
    
    # return the cookie string with expiry date
    x  = 'user='+str(user)+'&cookie='+cookie+'; expires='+exp

    return x

# POST register
def post_register(head, para):
    user, pasw  = get_creds(para)
    
    # the password cannot be shorter than 6 characters in cognito, usernames can be 1 character
    if len(user) > 1 and len(pasw) > 5:
        try:

            # create a new account for the user
            print(cognito.sign_up(Username = user, Password = pasw, ClientId = clientid, UserAttributes = [{'Name': 'email', 'Value': 'devnull@example.com'}]))
            print(cognito.admin_confirm_sign_up(Username = user, UserPoolId = userpoolid))

            # create a cookie and store it in dynamodb
            cookie  = make_cookie(user)

            # set the user as logged in
            global auth
            auth        = 'logged in as '+str(user)+'<br>'

            # return the cookie to the browser
            return return_html('created user '+user, 'created user '+user, '', cookie)
        
        except Exception as e:
            return return_html('error with registration '+str(e), '', head, '')
            
    else:
        return return_html('invalid user or password entered, this is what i received:\nusername: '+user+'\npassword: '+pasw, head, '')

# POST login
def post_login(head, para):
    user, pasw  = get_creds(para)
    
    # the password cannot be shorter than 6 characters in cognito, usernames can be 1 character. 'none' is a restricted username and disabled for registration.
    if len(user) > 1 and len(pasw) > 5 and user != 'none':
        
        # return a succesful login message or print the exception to the user (invalid credentials, wrong parsed characters, user does not exist)
        try:
            r = cognito.initiate_auth(ClientId = environ['clientid'],
                AuthFlow        = 'USER_PASSWORD_AUTH', 
                AuthParameters  = {'USERNAME' : user.strip(), 'PASSWORD' : pasw.strip()}
            )

            cookie              = make_cookie(user)

            # set the user as logged in
            global auth
            auth                = 'logged in as '+str(user)+'<br>' 

            x = return_html('logged in succesfully with '+str(user), 'logged in', '', cookie)
           
        except Exception as e:
            x = return_html('error with login '+str(e), '', '', '')

        return x
    
    else:
        return return_html('invalid user or password entered, this is what i received:\nusername: '+user+'\npassword: '+pasw, '', head, '')

# GET login
# GET registration 
def get_cred_page(head, txt, user):

    if user == 'none':
        body    = '''<form method="post">
        username \t <input type="text" name="username" /><br>
        password \t <input type="password" name="password" /><br>
        <input type="submit" /></form>'''

    else:
        body    = 'you are already logged in with user '+user+', do you want to <a href = "'+url+'/logout">logout</a> instead?'

    return return_html(body, txt, head, '')

# GET profile page
def get_profile_page(head, txt, user, cookie):  
    if user != 'none':  
        body    = 'Welcome to your profile '+str(user)+', it\'s great that you made an account.<br><br>You will see an updated profile page here soon, stay tuned.'
    else:
        body    = 'Please create an account or login using the links above.'

    return return_html(body, txt, head, '')

# check if the cookie is valid and return html
def get_cookie_status(cookie):
    if cookie != 'none': 
        user    = check_cookie(cookie)
    else:
        user    = 'none'

    if user != 'none':
        body    = 'logged in as '+str(user)+'<br>'
    else:
        body    = 'user not logged in<br>'
    
    return body, user

# GET home page
def get_home(head, para):
    body        = '<h1>Welcome to the Cognito demo page!</h1><br><br><img src="https://marek-serverless.s3.amazonaws.com/serverless-cognito.svg"><br><br><br>This demo was written by Marek Kuczynski in Python using Cognito, Lambda, API Gateway and Cognito.<br><br>It is using the Serverless Application Model and the sourcecode can be found <a href = "https://github.com/marekq/serverless-cognito" target="_blank">here</a>.<br><br>Checkout one of the menu options above to get started.'

    return return_html(body, 'home', head, '')

# GET logout
def get_logout(cookie, user):
    body        = 'logged out '+user
    cookie      = 'user='+str(user)+'&cookie='+cookie+'; expires=Thu, 01 Jan 1970 00:00:00 GMT'

    # set the user as logged out
    global auth
    auth        = 'user not logged in<br>'

    return return_html(body, 'logged out '+user, 'logged out '+user, cookie)

# GET users
def get_users(title, user):
    if user != 'none':
        b       = []
        x       = cognito.list_users(UserPoolId = userpoolid)
        body    = '<table width = "600"><tr><th>username</th><th>status</th><th>user create</th><th>user modify</th></tr><tr><td>'

        for y in x['Users']:
            b.append('</td><td>'.join((y['Username'], y['UserStatus'], y['UserCreateDate'].strftime("%m/%d/%Y %H:%M:%S"), y['UserLastModifiedDate'].strftime("%m/%d/%Y %H:%M:%S"))))

        body    += '</tr><tr><td>'.join(b)
        body    += '</tr></table>'

        return return_html(body, title, 'all users', '')
    else:
        return return_html('you need to login for this functionality', title, 'all users', '')

# lambda handler
def handler(event, context):
    # seth auth and url variables to global
    global auth
    global url

    # read the request variables from the client
    head    = str(event)
    meth    = str(event['httpMethod'])
    path    = str(event['path']).strip('/')
    para    = str(event['body'])
    host    = str(event['headers']['Host'])
    url     = str('https://'+host+'/Prod')

    # check if the cookie is valid
    try:
        cookie  = str(event['headers']['Cookie'])
        print('cookie '+cookie)

    # if no cookie is found, set cookie and user fields to blank
    except Exception as e:
        cookie  = 'none'
        print('cookie error '+str(e))

    auth, user    = get_cookie_status(cookie)
    print(path, meth, para, auth)

    # handle GET requests by returning an HTML page

    # register
    if meth == 'GET' and path == 'register':
        x   = get_cred_page(head, 'register here', user)

    # login
    elif meth == 'GET' and path == 'login':
        x   = get_cred_page(head, 'login here', user)

    # profile
    elif meth == 'GET' and path == 'profile':
        x   = get_profile_page(head, 'your profile', user, cookie)

    # logout
    elif meth == 'GET' and path == 'logout':
        x   = get_logout(cookie, user)

    # status page
    elif meth == 'GET' and path == 'status':
        x   = return_html('success', 'success', 'success', '')

    # list all users
    elif meth == 'GET' and path == 'users':
        x   = get_users('all users', user)

    # handle POST requests by submitting the query strings to the api using 'para'

    # register
    elif meth == 'POST' and path == 'register':
        x   = post_register(head, para)
        
    # login
    elif meth == 'POST' and path == 'login':
        x   = post_login(head, para)    

    # the home page, which default on any other request
    else:
        x   = get_home(head, para)

    # print the results and return them to the browser
    print('html '+str(x))
    return(x)
