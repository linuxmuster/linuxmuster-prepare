#!/usr/bin/python3
#
# lmn7-appliance.py
# thomas@linuxmuster.net
# 20180324
#

import getopt
import os
import re
import sys
import urllib.request

# help
def usage(rc):
    print('Downloads and installs linuxmuster-prepare package and initially prepares')
    print('a linuxmuster.net ubuntu appliance.\n')
    print('Usage: lmn7-appliance.py [options]')
    print('\n[options] are:\n')
    print('-t, --hostname=<hostname>   : Hostname to apply (optional, works only with')
    print('                              server profile).')
    print('-n, --ipnet=<ip/bitmask>    : Ip address and bitmask assigned to the host')
    print('                              (optional, default is 10.0.0.x/16, depending')
    print('                              on the profile).')
    print('-p, --profile=<profile>     : Host profile to apply, mandatory. Expected')
    print('                              values are "server", "opsi", "docker" or "ubuntu".')
    print('                              Profile name is also used as hostname, except for')
    print('                              "server" if set with -t.')
    print('-l, --pvdevice=<device>     : Device to use for lvm (server profile only).')
    print('-f, --firewall=<firewallip> : Firewall/gateway ip (default *.254).')
    print('-d, --domain=<domainname>   : Domainname (default linuxmuster.lan).')
    print('-u, --unattended            : Unattended mode, do not ask, use defaults.')
    print('-h, --help                  : Print this help.')
    sys.exit(rc)

# get cli args
try:
    opts, args = getopt.getopt(sys.argv[1:], "d:f:hl:n:p:t:u", ["domain=", "firewall=", "help", "pvdevice=", "ipnet=", "profile=", "hostname=", "unattended"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    usage(2)

# default values
unattended = ''
profile = ''
hostname = ''
domainname = ''
firewallip = ''
ipnet = ''
pvdevice = ''
profile_list = ['server', 'opsi', 'docker', 'ubuntu']

# evaluate options
for o, a in opts:
    if o in ("-u", "--unattended"):
        unattended = ' -u'
    elif o in ("-p", "--profile"):
        profile = a
    elif o in ("-t", "--hostname"):
        hostname = ' -t ' + a
    elif o in ("-l", "--pvdevice"):
        pvdevice = ' -l ' + a
    elif o in ("-d", "--domain"):
        domainname = ' -d ' + a
    elif o in ("-n", "--ipnet"):
        ipnet = ' -n ' + a
    elif o in ("-f", "--firewall"):
        firewallip = ' -f ' + a
    elif o in ("-h", "--help"):
        usage(0)
    else:
        assert False, "unhandled option"
        usage(1)

if not profile in profile_list or profile == '':
    usage(1)

profile = ' -p ' + profile

# repo data
url = 'http://fleischsalat.linuxmuster.org/lmn7'
pkgsremote = url + '/Packages'
pkgslocal = '/tmp/packages'
pkgname = 'linuxmuster-prepare'
rmpkgs = 'lxd lxd-client lxcfs lxc-common'

# return content of text file
def readTextfile(tfile):
    if not os.path.isfile(tfile):
        return False, None
    try:
        infile = open(tfile , 'r')
        content = infile.read()
        infile.close()
        return True, content
    except:
        print('Cannot read ' + tfile + '!')
        return False, None

print('### lmn7-prepare')

# get updates
print('## install software updates')
os.system('apt clean')
os.system('apt update')
os.system('DEBIAN_FRONTEND=noninteractive apt -y purge ' + rmpkgs)
os.system('DEBIAN_FRONTEND=noninteractive apt -y dist-upgrade')

# get lmn7 packages
print('## install linuxmuster-prepare package')
urllib.request.urlretrieve(pkgsremote, pkgslocal)
rc, content = readTextfile(pkgslocal)
debfile = re.findall(r'\nFilename: ./' + pkgname + '.*\n', content)[0].split('/')[1].replace('\n', '')
depends = re.findall(r'\nDepends: .*\nFilename: ./' + pkgname + '.*\n', content)[0].split('\n')[1].split(':')[1].replace(',', '')
os.system('DEBIAN_FRONTEND=noninteractive apt -y install ' + depends)
urllib.request.urlretrieve(url + '/' + debfile, '/tmp/' + debfile)
os.system('dpkg -i ' + '/tmp/' + debfile)

# invoke script
print('## invoke linuxmuster-prepare.py')
os.system('linuxmuster-prepare.py -i' + unattended + profile + hostname + domainname + firewallip + ipnet + pvdevice)