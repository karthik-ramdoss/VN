#!/usr/bin/python

#import httplib2
import sys
import commands


#'USAGE: python vn_splunk_rest_create_userrole.py --coreConf'

hostName = "localhost"
managementPort = "8089"
userName ="admin"
userPassword = "splunk"
RolesUri = "/services/authorization/roles"

role_name="nrole6"
imported_roles=["user","power"]
search_filter="venue_id=195 OR report_parameters.venue_id=195 OR Client=3"
ListOfUsersToSendEmail='rutvik@venuenext.com,wisdom_data@venuenext.com'



'''
def getSplunkRoles(userName,userPassword,hostName,managementPort,**kwargs):
    h = httplib2.Http(".cache", disable_ssl_certificate_validation=True)
    headers={'connection': 'close'}
    h.add_credentials(userName, userPassword)
    base_url="https://" + hostName + ":" + managementPort
    roles_uri="/services/authorization/roles"

    try:
        response, content = h.request(base_url + roles_uri, "GET", headers=headers)
        if (response['status'] >= '200' and response['status'] <= '204'):
            return content
        else:
            return response['status']
    except Exception, e:
        raise "Exception: " + str(e)
'''

def createSplunkRole(userName,userPassword,hostName,managementPort,**kwargs):

    url="https://" + hostName + ":" + managementPort + "/services/authorization/roles"
    cmd_execute="curl --silent -k -u " + userName+":"+userPassword +" "+ url

    for key,value in kwargs.iteritems():
        if type(value) is list:
            if key == 'name':
                raise Exception("Cannot have list in the role name field.")
            for v in value:
                cmd_execute=cmd_execute + " -d " + str(key)+"="+str(v)
        else:
            if key == 'name':
                role_name=str(value)
            cmd_execute=cmd_execute + " -d " + str(key)+"="+str(value)
        
            
    print cmd_execute
    result=commands.getoutput(cmd_execute)


    if "Error" and "already exists"in result:
        cmd_email='mailx -s "'+ "Error in Creating Role- "+hostName + '" ' + ListOfUsersToSendEmail +' < /dev/null'
        commands.getoutput(cmd_email)

        return result,cmd_execute
    elif "Error" in result and not "already exists" in result:
        cmd_email='mailx -s "'+ "Error in Creating Role- "+hostName + '" ' + ListOfUsersToSendEmail +' < /dev/null'
        commands.getoutput(cmd_email)
        raise Exception("Error in Creating role. Check Arguments ")
    else:
        cmd_email='mailx -s "'+ "Created Role Successfully - "+role_name+" "+hostName + '" ' + ListOfUsersToSendEmail + ' < /dev/null'
        commands.getoutput(cmd_email)
        return result,cmd_execute

'''
def getSplunkUsers(userName,userPassword,hostName,managementPort,**kwargs):
    
    h = httplib2.Http(".cache", disable_ssl_certificate_validation=True)
    headers={'connection': 'close'}
    h.add_credentials(userName, userPassword)
    base_url="https://" + hostName + ":" + managementPort
    users_uri="/services/authentication/users"

    try:

        response, content = h.request(base_url + users_uri, "GET", headers=headers)
        if (response['status'] >= '200' and response['status'] <= '204'):
            return content
        else:
            return response
    except Exception, e:
        raise Exception("Exception: " + str(e))

'''

def createSplunkUser(userName,userPassword,hostName,managementPort,**kwargs):
    url="https://" + hostName + ":" + managementPort + "/services/authentication/users"
    cmd_execute="curl --silent -k -u " + userName +":"+userPassword + " "+url 

    for key, value in kwargs.iteritems():
        if type(value) is list:
            if key == 'name':
                raise Exception("Cannot have list in the name field.")
            if key == 'password':
                raise Exception("Cannot have list in the password field.")
            for v in value:
                cmd_execute=cmd_execute + " -d " + str(key)+"="+str(v)
        else:
            if key == 'name':
                user_name=str(value)
            cmd_execute=cmd_execute + " -d " + str(key)+"="+str(value)
    print cmd_execute
    result=commands.getoutput(cmd_execute)       
    
    if "Error" and "already exists"in result:
        cmd_email='mailx -s "'+ "Error in Creating User- "+hostName + '" ' + ListOfUsersToSendEmail +' < /dev/null'
        commands.getoutput(cmd_email)
        return result,cmd_execute
    elif "Error" in result and not "already exists" in result:
        cmd_email='mailx -s "'+ "Error in Creating User- "+hostName + '" ' + ListOfUsersToSendEmail +' < /dev/null'
        commands.getoutput(cmd_email)
        raise Exception("Error in Creating User. Check arguments")
    else:
        cmd_email='mailx -s "'+ "Created User Successfully - "+user_name+" "+hostName + '" ' + ListOfUsersToSendEmail + ' < /dev/null'
        commands.getoutput(cmd_email)
        return result,cmd_execute




def echoString(stringToLog):
    return stringToLog





'''                                                                                                                                                           
try:                                                                                                                                                          
    result, cmd_execute=createSplunkRole(userName,userPassword,hostName,managementPort,name=role_name,imported_roles=imported_roles,srchFilter=search_filter)
except Exception,e:                                                                                                                                           
    print "Exception: " + str(e)                                                                                                                              
                                                                                                                                                              
'''



try:
    response = getSplunkUsers(userName,userPassword,hostName,managementPort)
    print response
except Exception ,e:
    print "Exception: "+str(e)


