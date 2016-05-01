#!/usr/bin/env python

""" GitScanner
    Scans GitHub for public repos and gists
"""
__author__ = "Sanjay Parab"


import re
import sys
import requests
import argparse


# Global parameters
GITHUB_TOKEN = None
EMAIL_PASSWORD = None
LIST_PUB_REPO = False
LIST_PUB_GIST = False 
LIST_ORG_MEMBER = False 
ORG_NAME = None
FROM_EMAIL = None
SEND_KUDOS = False
SEND_NOTIFICATION = False
NOTIFICATION_TEMPLATE = None
KUDOS_TEMPLATE = None

# Define git urls
items_per_page = 30 
git_members = {}

def show_config_parms():
    print "Github token     = ", GITHUB_TOKEN
    print "Email Password   = ", EMAIL_PASSWORD 
    print "List Public Repo  = ", LIST_PUB_REPO
    print "List Public Gists =" , LIST_PUB_GIST
    print "List Org Members  =", LIST_ORG_MEMBER 
    print "Org Name          =", ORG_NAME 
    print "From Email        =", FROM_EMAIL 
    print "Send Kudos        =", SEND_KUDOS
    print "Send Notification = " , SEND_NOTIFICATION 
    print "Notification Template = " , NOTIFICATION_TEMPLATE
    print "Kudos Template        =" , KUDOS_TEMPLATE 


# Function to determine max number of pages for org memberlist
def get_max_pages(url,token):
    r = requests.get(url, auth=('token' , token))
    if r.status_code != 200:
       print "Unable to fetch Org memberlist"
       exit()
    if 'link' in r.headers:
       max_pg_number = int(r.headers['link'].split(',')[1].split('>')[0].split('=')[1])
       return max_pg_number
    else :
       print "Unable to retrieve Org Memberlist"
       exit()

# Function to determine max number of pages for memberi repo list
def get_max_repo_gist_pages(url, token):
    max_pg_number = 1
    if token :  
       r = requests.get(url, auth=('token' , token))
    else:
       r = requests.get(url)

    try :
         max_pg_number = int(r.headers['link'].split(',')[1].split('>')[0].split('=')[1])
    except:
        pass
    return max_pg_number

def get_user_info(username,id):
    email_id = 'nobody@example.com'
    git_user_url = 'https://api.github.com/users/' + username    
    
    resp = requests.get(git_user_url, auth=('token', GITHUB_TOKEN))
     
    if resp.status_code != 200:
       print "Not looking good..."
       return 'noreply@example.com'
    email_id = resp.json()['email']
    return email_id, resp.json()['public_repos'] , resp.json()['public_gists']

def get_public_repos(username, id ):
    repos=[]
    git_repo_link_url = 'https://api.github.com/user/' + str(id)  + '/repos?page=1'
    r = requests.get(git_repo_link_url, auth=('token', GITHUB_TOKEN))

    if r.status_code != 200:
       print "Unable to fetch member repo..."
       print r.status_code
       return None 
    
    # Retrieve last page index 
    max_repo_pages = get_max_repo_gist_pages(git_repo_link_url, GITHUB_TOKEN)
    
    json_data = r.json()
    page = 1
    print "Public repos for " + username + " are:" 

    try : 
        while page <= max_repo_pages :
              page_url = 'https://api.github.com/user/' + str(id)  + '/repos?page=' + str(page)
              repolist = requests.get(page_url, auth=('token' , GITHUB_TOKEN))
              try:
                  index = 0
                  while index < items_per_page : 
                      repos.append(r.json()[index]['html_url'])
                      index = index + 1
              except Exception, e:
                   break
              page = page + 1 
    except:
         return repos 
    return repos

def get_public_gists(username, id ):
    gists=[]
    git_gists_link_url = 'https://api.github.com/users/' + username  + '/gists?page=1'
    g_r = requests.get(git_gists_link_url, auth=('token', GITHUB_TOKEN))

    if g_r.status_code != 200:
       print "Unable to fetch member gists..."
       print g_r.status_code
       return None 

    # Retrieve last page index 
    g_max_repo_pages = get_max_repo_gist_pages(git_gists_link_url, GITHUB_TOKEN)
    
    g_json_data = g_r.json()
    g_page = 1
    print "\nPublic gists for " + username + " are:" 

    try : 

        while g_page <= g_max_repo_pages :
              g_page_url = 'https://api.github.com/users/' + username + '/gists?page=' + str(g_page)
              gistlist = requests.get(g_page_url, auth=('token' , GITHUB_TOKEN))
              if gistlist.status_code != 200:
                 print "Unable to fetch gistlist"
                 return 

              try:
                  g_index = 0
                  while g_index < items_per_page : 
                      gists.append(gistlist.json()[g_index]['html_url'])
                      g_index = g_index + 1
              except Exception, e:
                   break
              g_page = g_page + 1 
    except:
         return gists 
    return gists   

def get_git_members(org):

    #Create empty dictionary 
    members = {}
    git_mbr_pg1 = 'https://api.github.com/orgs/'+ org  +'/members?page=1'
    git_mbr_url = 'https://api.github.com/orgs/'+ org + '/members'
    last_page = int (get_max_pages(git_mbr_pg1,GITHUB_TOKEN))
    page = 0 
    
    while page <= last_page :
        page_url = git_mbr_url + '?page=' + str(page)
        r = requests.get(page_url, auth=('token', GITHUB_TOKEN))
  
        if r.status_code != 200:
           print "Unable to retrieve data. Quiting..."
           outfile.close()
           exit()
 
        json_data = r.json()
        index = 0
        try: 
            while index < items_per_page :

                  git_members[json_data[index]['login']] = json_data[index]['id'] 
                  members.update({json_data[index]['login']:json_data[index]['id']})
                  #print "\n Getting public repos for user  : " + json_data[index]['login'] 
                  index = index + 1
        except IndexError :
            if ( last_page - page >= 2 ):
                exit()
            pass
        except:
            raise
        page = page + 1

    return members

def process_args(args):

    #Define Global parameters to be updated
    global GITHUB_TOKEN , EMAIL_PASSWORD , LIST_PUB_REPO
    global LIST_PUB_GIST, LIST_ORG_MEMBER, ORG_NAME 
    global FROM_EMAIL, SEND_KUDOS, SEND_NOTIFICATION
    global NOTIFICATION_TEMPLATE, KUDOS_TEMPLATE

    #Process Arguments 
    parser = argparse.ArgumentParser(version='1.0')
    parser.add_argument("-r", "--repository" , help="List Public Repository", action="store_true",dest='list_pub_repos')
    parser.add_argument("-g", "--gist" , help="List Public Gist", action="store_true",dest='list_pub_gists')
    parser.add_argument("-m", "--member" , help="List Org Members", action="store_true",dest='list_org_members')
    parser.add_argument("-n", "--email" , help="Send Email Notification", action="store_true", dest='send_notification')
    parser.add_argument("-k", "--kudos" , help="Send Kudos Email Notification to member with no public gists and/or repos", action="store_true", dest='send_kudos')
    parser.add_argument("-o", "--org" , help="Github Org name ", action="store", dest='org_name')
    parser.add_argument("-c", "--config" , type=argparse.FileType('r'), help="Path to configuration file ", dest='config_file')
    parser.add_argument("-t", "--token", help="Github Access Token" , action="store",dest='github_token')
    parser.add_argument("-s", "--sender-email" , help=" Email notifier id. e.g security@example.com", action="store",dest='from_email') 
    parser.add_argument("-p", "--email-password" , help="Password to send Email Notifications ", action="store",dest='email_password') 
    args_selected = parser.parse_args(args)
    print "Scanning GitHub Oragnization : " , args_selected.org_name
    
    token_dict={}
    if args_selected.config_file:
       for line in args_selected.config_file.readlines():
              key,value = line.strip().split('=')
              token_dict[key]=value
   
    if 'GITHUB_TOKEN' in token_dict:
        GITHUB_TOKEN = token_dict['GITHUB_TOKEN']
    if 'EMAIL_PASSWORD' in token_dict:
        EMAIL_PASSWORD =  token_dict['EMAIL_PASSWORD']
          
    if args_selected.org_name and (args_selected.github_token or args_selected.config_file): 
       ORG_NAME = args_selected.org_name
       if GITHUB_TOKEN == None: 
          GITHUB_TOKEN = args_selected.github_token
       if EMAIL_PASSWORD == None:
          EMAIL_PASSWORD = args_selected.email_password

       SEND_KUDOS = args_selected.send_kudos
       LIST_PUB_REPO = args_selected.list_pub_repos
       LIST_PUB_GIST = args_selected.list_pub_gists
       LIST_ORG_MEMBER = args_selected.list_org_members
       #print "Will do something...:)"
       local_members={}
       local_members = get_git_members(ORG_NAME)
       if LIST_PUB_REPO or LIST_PUB_GIST:

          for login in sorted(local_members): 
              # Get user email , public_gists and public_repo count
              user_email , pub_repo , pub_gist = get_user_info(login, local_members[login])
              if ( pub_repo == 0 and pub_gist == 0 ):
                   if SEND_KUDOS:
                      print "Awesome job %s !!!" %login
                   continue
              if ( pub_repo == 0 and LIST_PUB_REPO and LIST_PUB_GIST == False ):
                   continue
              if ( pub_gist == 0 and LIST_PUB_GIST and LIST_PUB_REPO == False ):
                   continue

              print "\n============================================================================="
              print "\n Getting public repos for user  : " + login 
              print " Email id                       : " + user_email
              
              if LIST_PUB_REPO :
                 print " Number of Public Repos         : " + str(pub_repo)
              if LIST_PUB_GIST:
                 print " Number of Public Gists         : " + str(pub_gist)
              print "\n============================================================================="
              if pub_repo > 0 and LIST_PUB_REPO :
                 member_repos = get_public_repos(login, local_members[login]) 
                 for repo in member_repos:
                     print repo
              if pub_gist > 0 and LIST_PUB_GIST:
                 member_gists = get_public_gists(login,local_members[login])
                 for value in member_gists:
                     print value

              print "\n=============================================================================\n"
          return
          
       if LIST_ORG_MEMBER  :
          for login in sorted(local_members):
              print login

    else:
       print "Are you nuts ? Pleaes provide Org name, Github token and/or configuration file"
       exit(1)
    
if __name__ == "__main__":

   process_args(sys.argv[1:])
   exit(0)


  