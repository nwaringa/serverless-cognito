#!/usr/bin/python
# marek kuczynski
# @marekq
# www.marek.rocks
# coding: utf-8

import boto3, json, pprint, re, os, time

# take lambda environment variables for cognito
clientid    = os.environ['clientid']
userpoolid  = os.environ['userpoolid']

# setup session with cognito
c           = boto3.client('cognito-idp')

# return html with a 200 code, the client headers are printed by default
def return_html(txt, title, head):
    # head  = pprint.PrettyPrinter().pformat(head)

    return {
        'statusCode': '200', 
        'body': '<center><h1>'+title+'</h1><a href = "./login">login</a> | <a href = "./register">register</a> | <a href = "https://marek.rocks">marek.rocks</a> | <a href = "https://github.com/marekq/serverless-cognito">sourcecode</a><br><br>'+str(txt)+'</center><br>'+str(head), 
        'headers': {'Content-Type': 'text/html', 'charset': 'utf-8'}
    } 
    
# get the POSTed string username and password from the headers
def get_creds(para):
    user    = ''
    pasw    = ''
    
    for y in para.split('&'):
        if re.search('username', y):
            user    = y[9:]
        elif re.search('password', y):
            pasw    = y[9:]
            
    return user, pasw
    
# post page for login
def post_login(head, para):
    user, pasw  = get_creds(para)
    
    # the password cannot be shorter than 6 characters in cognito, usernames can be 1 character
    if len(user) > 1 and len(pasw) > 5:
        
        # return a succesful login message or print the exception to the user (invalid credentials, wrong parsed characters, user does not exist)
        try:
            r   = c.initiate_auth(AuthFlow = 'USER_PASSWORD_AUTH', AuthParameters = {'USERNAME': str(user), 'PASSWORD': str(pasw)}, ClientId = clientid)
            return return_html(str('<h1>logged in succesfully with '+str(user)+'</h1>'+r['AuthenticationResult']['AccessToken']+'<br><br>'+r))

        except Exception as e:
            print(e)
            return return_html(str(e), 'error', '')
        
    return return_html('invalid user or password entered, this is what i received:\nusername: '+user+'\npassword: '+pasw, head)

# post page for register
def post_register(head, para):
    user, pasw  = get_creds(para)
    
    # the password cannot be shorter than 6 characters in cognito, usernames can be 1 character
    if len(user) > 1 and len(pasw) > 5:
        try:
            print(c.sign_up(Username = user, Password = pasw, ClientId = clientid, UserAttributes = [{'Name': 'email', 'Value': 'devnull@example.com'}]))  #, {'Name' : 'color', 'Value' : str(color)}]))
            print(c.admin_confirm_sign_up(UserPoolId = userpoolid, Username = user))

            return return_html('created user '+user, 'created user '+user, '')
        
        except Exception as e:
            return return_html(e, 'error', head)
            
    else:
        return return_html('invalid user or password entered, this is what i received:\nusername: '+user+'\npassword: '+pasw, he)

# return html for login and registration, optionally another field can be added through the txt variable
def get_cred_page(head, txt, opt):
    body    = '''<br><form method="post">
    username: \t <input type="text" name="username" /><br />
    password: \t <input type="password" name="password" /><br />'''
    body    += opt
    body    += '''<input type="submit" /></form><hr />'''
    
    return return_html(body, txt, head)

# lambda handler
def lambda_handler(event, context):
    head    = str(event)
    meth    = str(event['httpMethod'])
    path    = str(event['path']).strip('/')
    para    = str(event['body'])

    # handle get requests by returning an HTML page
    if meth == 'GET' and path == 'register':
        return get_cred_page(head, 'register here', '')

    elif meth == 'GET' and path == 'login':
        return get_cred_page(head, 'login here', '')
      
    # hande post requests by submitting the query strings to the api        
    elif meth == 'POST' and path == 'register':
        return post_register(head, para)
        
    elif meth == 'POST' and path == 'login':
        return post_login(head, para)    

    # if another request was submitted, return an error code
    else:
        return return_html('invalid request, try <a href="./login">login</a> instead', 'invalid request', head)