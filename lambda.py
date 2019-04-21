#!/usr/bin/python
# marek kuczynski
# @marekq
# www.marek.rocks
# coding: utf-8

import boto3, re, os, time
from random import randint
from boto3.dynamodb.conditions import Key, Attr

# take lambda environment variables for cognito
clientid    = os.environ['clientid']
userpoolid  = os.environ['userpoolid']
c           = boto3.client('cognito-idp')
d           = boto3.resource('dynamodb').Table(os.environ['dynamotable'])

# return html with a 200 code, the client headers are printed by default
def return_html(txt, title, head, cookie):
    if len(cookie) == 0:
        h    = {'Content-Type': 'text/html', 'charset': 'utf-8'}
    else:
        h    = {'Content-Type': 'text/html', 'charset': 'utf-8', 'Set-Cookie': cookie}

    return {
        'statusCode': '200', 
        'body': '<html><body><center><h1>'+title+'</h1>'+auth+'<a href = "./login">login</a> | <a href = "./register">register</a> | <a href = "./profile">your profile</a> | <a href = "https://github.com/marekq/serverless-cognito">sourcecode</a><br><br>'+str(txt)+'</center><br>'+str(cookie)+'<br></body></html>', 
        'headers': h
    } 
    
# get the POSTed string username and password from the headers
def get_creds(para):
    user    = ''
    pasw    = ''
    
    for y in para.split('&'):
        if re.search('username', y):
            user    = unquote(y[9:])
        elif re.search('password', y):
            pasw    = unquote(y[9:])
         
    return user, pasw
    
# post page for login
def post_login(head, para):
    user, pasw  = get_creds(para)
    
    # the password cannot be shorter than 6 characters in cognito, usernames can be 1 character
    if len(user) > 1 and len(pasw) > 5:
        
        # return a succesful login message or print the exception to the user (invalid credentials, wrong parsed characters, user does not exist)
        try:
            r = c.initiate_auth(ClientId = os.environ['clientid'],
                AuthFlow = 'USER_PASSWORD_AUTH', 
                AuthParameters = {'USERNAME' : user.strip(), 'PASSWORD' : pasw.strip()}
            )
            
            cookie      = make_cookie(user)
            
            x = return_html('<h1>logged in succesfully with '+str(user)+'</h1>'+str(r['ResponseMetadata'])+'<br>', '', '', cookie)

        except Exception as e:
            x = return_html('error with login '+str(e), '', '', '')

        return x
    
    else:
        return return_html('invalid user or password entered, this is what i received:\nusername: '+user+'\npassword: '+pasw, '', head, '')

def check_cookie(x):
    user    = x.split('&')[0].split('=')[1]
    cookie  = x.split('&')[1].split('=')[1]

    print('check_cookie: '+str(user)+' '+str(cookie))
    x       = d.query(KeyConditionExpression = Key('user').eq(user), FilterExpression= Key('cookie').eq(str(cookie)))

    if x['Count'] == int(0):
        print('not found '+user+' '+cookie)
        return 'none'

    else:
        print('found '+user+' '+cookie)   
        return user

def make_cookie(user):
    cookie  = str(randint(1000, 100000))
            
    # store the current cookie value in dynamodb
    d.put_item(TableName = os.environ['dynamotable'], 
        Item = {
            'user'      : user,
            'cookie'    : cookie
        }
    )
    
    x  = 'user='+str(user)+'&cookie='+cookie

    return x

# post page for register
def post_register(head, para):
    user, pasw  = get_creds(para)
    
    # the password cannot be shorter than 6 characters in cognito, usernames can be 1 character
    if len(user) > 1 and len(pasw) > 5:
        try:
            print(c.sign_up(Username = user, Password = pasw, ClientId = clientid, UserAttributes = [{'Name': 'email', 'Value': 'devnull@example.com'}]))
            print(c.admin_confirm_sign_up(Username = user, UserPoolId = userpoolid))

            cookie  = make_cookie(user)

            # return the cookie to the browser
            return return_html('created user '+user, 'created user '+user, '', cookie)
        
        except Exception as e:
            return return_html('error with registration '+str(e), '', head, '')
            
    else:
        return return_html('invalid user or password entered, this is what i received:\nusername: '+user+'\npassword: '+pasw, head, '')

# return html for login and registration, optionally another field can be added through the opt variable
def get_cred_page(head, txt):
    body    = '''<br><form method="post">
    username: \t <input type="text" name="username" /><br />
    password: \t <input type="password" name="password" /><br />
    <input type="submit" /></form><hr />'''
    
    return return_html(body, txt, head, '')

def get_profile_page(head, txt, user, cookie):    
    if auth != '':
        body    = '<br><br>logged in as '+str(user)+' using cookie: '+str(cookie)+'<br><br>'
    else:
        body    = '<br><br>failed login as '+str(user)+'<br><br>'

    return return_html(body, txt, head, '')

def get_cookie_status(cookie):
    user    = check_cookie(cookie)

    if user != 'none':
        body    = '<br>logged in as '+str(user)+'<br>'
    else:
        body    = '<br>failed login as '+str(user)+'<br>'   
    
    return body

# lambda handler
def handler(event, context):
    head    = str(event)
    meth    = str(event['httpMethod'])
    path    = str(event['path']).strip('/')
    para    = str(event['body'])
    print('head ', head)

    global auth
    try:
        cookie  = str(event['headers']['Cookie'])
        print('cookie '+cookie)
        auth    = get_cookie_status(cookie)

    except Exception as e:
        cookie  = ''
        print('cookie error '+str(e))
        auth    = 'none'

    print(path, meth, para, auth)

    # handle get requests by returning an HTML page
    if meth == 'GET' and path == 'register':
        x   = get_cred_page(head, 'register here')

    elif meth == 'GET' and path == 'profile':
        x   = get_profile_page(head, 'your profile', auth, cookie)

    elif meth == 'GET' and path == 'login':
        x   = get_cred_page(head, 'login here')
      
    # hande post requests by submitting the query strings to the api        
    elif meth == 'POST' and path == 'register':
        x   = post_register(head, para)
        
    elif meth == 'POST' and path == 'login':
        x   = post_login(head, para)    

    # if another request was submitted, return an error code
    else:
        x   = return_html('invalid request, try <a href="/login">login</a> instead', 'invalid request', head, '')

    print('html '+str(x))
    return(x)
