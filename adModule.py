#!/usr/bin/python3
# -*- coding: utf-8 -*-

# class for interacting with actve directory using ldap

# import class and constants (0.9.7+)
from ldap3 import Server, Connection, SIMPLE, SYNC, ASYNC, SUBTREE, ALL, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE, Tls
import ssl
import sys 

class ad :
    """ Simple class for interaction with active Directory using ldap """
    def __init__(self):
        """ Initialize common variables and load config from ? what file """
        
    def connect (self,user,password,server) :
        """
        Create server object and connection with it,
        latter accessible as \"s\" and \"c\" inside \"ad\" object
        """
        # define an unsecure LDAP server, requesting info on DSE and schema
        self.s = Server(server, use_ssl=True , get_info = ALL, tls=Tls(validate=ssl.CERT_NONE))  
        self.c = Connection(self.s, auto_bind = True, client_strategy = SYNC, user=user, \
             password=password, authentication=SIMPLE, check_names=True)

    def disconnect (self) :
        """
        Closes connection with current server
        """
        try :
            self.c.unbind()
            return True
        except:
            return False

    def createUser(self,dn,attr) :
        """
        Create user with dn and attr
        Password is stored in attr['password']
        """
        unicode_pass='"'+str(attr['password'])+'"'
        ready_pass=unicode_pass.encode('utf-16-le')
        del attr['password']
        self.c.add(dn,['top','person','organizationalPerson','user'],attr)
        self.c.modify(dn,{'unicodePwd':(MODIFY_REPLACE,ready_pass)})
        self.c.modify(dn,{'userAccountControl':(MODIFY_REPLACE,512)})

        return True

    def resetPassword(self,dn,password) :
        """
        Reset password for user with supplied dn
        """
        unicode_pass='"'+str(password)+'"'
        ready_pass=unicode_pass.encode('utf-16-le')
        self.c.modify(dn,{'unicodePwd':(MODIFY_REPLACE,ready_pass)})
        return True

    def searchUsers(self,attr,value,request,baseDn):
        """
        Search users in baseDN, filtered by attr with specific value.
        Returns list of users and requested atributes. Attributes specified
        by list of names in \"'request\"
        """
        users=[]
        ldapFilter='(&(objectCategory=person)(objectClass=user)('+str(attr)+'='+str(value)+'))'
        self.c.search(search_base=baseDn,search_filter=ldapFilter,search_scope=SUBTREE,attributes=request)
        for record in self.c.response :
            if record['type'] == 'searchResEntry' :
                users.append(record['attributes'])
        return users

    def searchOrgUnits(self,attr,value,request,baseDn):
        """
        Search users in baseDN, filtered by attr with specific value.
        Returns list of users and requested atributes. Attributes specified
        by list of names in \"'request\"
        """
        ou=[]
        #print('(&(objectCategory=organizationalUnit)('+attr+'='+value+'))')
        ldapFilter='(&(objectCategory=organizationalUnit)('+str(attr)+'='+str(value)+'))'
        self.c.search(search_base=baseDn,search_filter=ldapFilter,search_scope=SUBTREE,attributes=request)
        for record in self.c.response :
            #print(record)
            if record['type'] == 'searchResEntry' :
                ou.append(record['attributes'])
        return ou

    def addToGroup (self,user,group):
        """
        Add user to group. Both specified by distinguished name
        """
        try:
            self.c.modify(group,{'member':(MODIFY_ADD,user)})
            return True
        except:
            return False

    def removeFromGroup (self,user,group):
        """
        Remove user from group. Both specified by distinguished name
        """
        try:
            self.c.modify(group,{'member':(MODIFY_DELETE,user)})
            return True
        except:
            return False

    def modifyAttribute (self,attribute,newValue,adObject,mod=MODIFY_REPLACE):
        """
        Modify any attribute. Replace old attribute by default
        """
        #print(str(attribute)+" "+str(adObject)+" "+str(newValue))
        try:
            self.c.modify(adObject,{attribute:(mod,newValue)})
            print(str(attribute)+" "+str(adObject)+" "+str(newValue))
            return True
        except:
            print("ooops")
            return False
