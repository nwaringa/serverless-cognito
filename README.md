serverless-cognito
==================
Authenticate your users through Cognito, Lambda, API Gateway and DynamoDB. The script will set a local cookie in the browser and prompt for reauthentication by the user if needed. The cookies are stored in a DynamoDB table that is part of the deployment. All user accounts are safely stored using Cognito. You can easily deploy the solution using the [Serverless Application Repository](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:517266833056:applications~serverless-cognito).

Installation
------------

Run 'build.sh' in the root folder to automatically deploy to your account. You can also use the [Serverless Application Repository](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:517266833056:applications~serverless-cognito). 

Once you want to remove the service, simply delete the CloudFormation stack in your AWS account. 

Roadmap
-------

- [ ] Add change password functionality for users.
- [ ] Add email or SMS validation for new accounts. 
- [ ] Increase cookie security (better random generation and secure storage in browser)
- [ ] Add a fully functional profile with some user data.
- [ ] Handle authentication using a custom authorizer in API Gateway. 

Contact
-------

In case of questions or bugs, please raise an issue or reach out to @marekq!
