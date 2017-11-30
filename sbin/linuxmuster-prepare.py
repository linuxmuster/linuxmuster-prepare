#!/usr/bin/python3
#
# linuxmuster-prepare.py
# thomas@linuxmuster.net
# 20171129
#

import configparser
import datetime
import getopt
import getpass
import netifaces
import os
import re
import socket
import sys

from IPy import IP


## functions start

# help
def usage(rc):
    print('Usage: linuxmuster-prepare.py [options]')
    print('\n [options] are:')
    print('\n -n, --hostname=<hostname>   : Assigns the given hostname (mandatory).')
    print('\n -i, --ipnet=<ip/bitmask>    : Ip address and bitmask assigned to the host')
    print('                               (optional, default is 10.0.0.x/16')
    print('                               depending on the profile).')
    print('\n -p, --profile=<profile>     : Host and software profile to apply. Allowed')
    print('                               values are "server", "opsi", "docker" or "none".')
    print('                               If option "-i" is not set an ip ending in')
    print('                               .1, .2 or .3 will be automatically assigned.')
    print('                               If "-p" is not set option "-i" has to be set.')
    print('\n -f, --firewall=<firewallip> : Firewall/gateway ip (default *.*.*.254).')
    print('\n -b, --dnsip=<dnsip>         : DNS server ip (default *.*.*.1).')
    print('\n -d, --domain=<domainname>   : Domainname (default linuxmuster.lan).')
    print('\n -r, --rootpw=<password>     : Root password (default "Muster!"). Only with -u.')
    print('\n -s, --swapsize=<size>       : Swapfile size in GB (default "2").')
    print('\n -u, --unattended            : Unattended mode, do not ask, use defaults.')
    print('\n -h, --help                  : Print this help.')
    sys.exit(rc)

# test internet connection by google dns
def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        #print ex.message
        return False

# print without linefeed
def printr(msg):
    print(msg, end='', flush=True)

# return datetime string
def dtStr():
    return "{:%Y%m%d%H%M%S}".format(datetime.datetime.now())

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

# write textfile
def writeTextfile(tfile, content, flag):
    try:
        outfile = open(tfile, flag)
        outfile.write(content)
        outfile.close()
        return True
    except:
        print('Failed to write ' + tfile + '!')
        return False

# replace string in file
def replaceInFile(tfile, search, replace):
    rc = False
    try:
        bakfile = tfile + '.bak'
        copyfile(tfile, bakfile)
        rc, content = readTextfile(tfile)
        rc = writeTextfile(tfile, content.replace(search, replace), 'w')
    except:
        print('Failed to write ' + tfile + '!')
        if os.path.isfile(bakfile):
            copyfile(bakfile, tfile)
    if os.path.isfile(bakfile):
        os.unlink(bakfile)
    return rc

# return detected network interfaces
def detectedInterfaces():
    iface_list = netifaces.interfaces()
    iface_list.remove('lo')
    iface_count = len(iface_list)
    if iface_count == 1:
        iface_default = iface_list[0]
    else:
        iface_default = ''
    return iface_list, iface_default

# return default network interface
def getDefaultIface():
    # first try to get a single interface
    iface_list, iface_default = detectedInterfaces()
    if iface_default != '':
        return iface_list, iface_default
    # second if more than one get it by default route
    route = "/proc/net/route"
    with open(route) as f:
        for line in f.readlines():
            try:
                iface, dest, _, flags, _, _, _, _, _, _, _, =  line.strip().split()
                if dest != '00000000' or not int(flags, 16) & 2:
                    continue
                return iface_list, iface
            except:
                continue
    return iface_list, iface_default

# test valid hostname
def isValidHostname(hostname):
    try:
        if (len(hostname) > 63 or hostname[0] == '-' or hostname[-1] == '-'):
            return False
        allowed = re.compile(r'[a-z0-9\-]*$', re.IGNORECASE)
        if allowed.match(hostname):
            return True
        else:
            return False
    except:
        return False

# test valid domainname
def isValidDomainname(domainname):
    try:
        for label in domainname.split('.'):
            if not isValidHostname(label):
                return False
        return True
    except:
        return False

# test valid ipv4 address
def isValidHostIpv4(ip):
    try:
        ipv4 = IP(ip)
        if not ipv4.version() == 4:
            return False
        ipv4str = IP(ipv4).strNormal(0)
        if (int(ipv4str.split('.')[0]) == 0 or int(ipv4str.split('.')[3]) == 0):
            return False
        for i in ipv4str.split('.'):
            if int(i) > 254:
                return False
        return True
    except:
        return False

## functions end


# get cli args
try:
    opts, args = getopt.getopt(sys.argv[1:], "hn:i:f:b:d:r:p:s:u", ["help", "hostname=", "ipnet=", "firewall=", "dnsip=", "domain=", "rootpw=", "profile=", "swapsize=", "unattended"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    usage(2)

# default values
unattended = False
profile_list = ['server', 'opsi', 'docker']
hostname = ''
profile = ''
serverip = ''
hostip = ''
firewallip = ''
dnsip = ''
opsiip = ''
ipnet = ''
iface = ''
ipset = False
fwset = False
dnsset = False
domainname = 'linuxmuster.lan'
rootpw = 'Muster!'
swapsize = '2'
sharedir = '/usr/share/linuxmuster-prepare'
templates = sharedir + '/templates'
repokey = sharedir + '/lmn7-repo.key'
cachedir = '/var/cache/linuxmuster'
prepini = cachedir + '/prepare.ini'
setupini = '/var/lib/linuxmuster/setup.ini'
updates = False
iniread = False

# exit if system is already set up
if os.path.isfile(setupini):
    print("Don't do this on a already configured system!")
    sys.exit(1)

# read previously created prepare.ini
if os.path.isfile(prepini):
    printr('## Reading default values from a previous run ... ')
    try:
        prep = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        prep.read(prepini)
        iface_ini = prep.get('setup', 'iface')
        domainname_ini = prep.get('setup', 'domainname')
        hostip_ini = prep.get('setup', 'hostip')
        hostname_ini = prep.get('setup', 'hostname')
        profile_ini = prep.get('setup', 'profile')
        firewallip_ini = prep.get('setup', 'firewallip')
        dnsip_ini = prep.get('setup', 'dnsip')
        bitmask_ini = prep.get('setup', 'bitmask')
        swapsize_ini = prep.get('setup', 'swapsize')
        iniread = True
        print('OK!')
    except:
        print('failed!')

# use values in case of success
if iniread:
    iface = iface_ini
    domainname = domainname_ini
    firewallip = firewallip_ini
    dnsip = dnsip_ini
    profile = profile_ini
    hostname = hostname_ini
    hostip = hostip_ini
    bitmask = bitmask_ini
    swapsize = swapsize_ini
    if hostip != '' and bitmask !='':
        ipnet = hostip + '/' + bitmask

# evaluate options
for o, a in opts:
    if o in ("-u", "--unattended"):
        unattended = True
    elif o in ("-s", "--swapsize"):
        swapsize = str(a)
    elif o in ("-p", "--profile"):
        if a in profile_list:
            profile = a
        elif a == 'none':
            profile = ''
        else:
            usage(1)
    elif o in ("-n", "--hostname"):
        hostname = a
    elif o in ("-r", "--rootpw"):
        rootpw = a
    elif o in ("-d", "--domain"):
        domainname = a
    elif o in ("-i", "--ipnet"):
        ipnet = a
        ipset = True
    elif o in ("-f", "--firewall"):
        firewallip = a
        fwset = True
    elif o in ("-b", "--dnsip"):
        dnsip = a
        dnsset = True
    elif o in ("-h", "--help"):
        usage(0)
    else:
        assert False, "unhandled option"
        usage(1)

# test values
if hostname == '' and profile != '':
    hostname = profile
if hostname != '' and profile == '':
    if hostname in profile_list:
        profile = hostname
if hostname == '':
    usage(1)
if ipnet == '' and profile == '':
    usage(1)
# override ini values if ipnet was set on cli
if ipset:
    if not fwset:
        firewallip = ''
    if not dnsset:
        dnsip = ''

# get network interfaces
iface_list, iface_default = getDefaultIface()
if len(iface_list) == 0:
    print('# No network interfaces found!')
    sys.exit(1)

os.system('clear')
print('### linuxmuster-prepare')

# prepare for which service (server, opsi, docker)
print('## network setup')
print('# Profile')
defaultprof = profile
if not unattended:
    while True:
        profile = input('Enter virtual machine profile ' + str(profile_list).replace("'", "") + ' [' + defaultprof + ']: ')
        profile = profile or defaultprof
        if (profile in profile_list) or profile == '':
            break
        else:
            print("Invalid entry!")
pkgs = ''
ipnr = ''
if profile == 'server':
    ipnr = '1'
    pkgs = 'linuxmuster-base7'
elif profile == 'opsi':
    ipnr = '2'
    pkgs = 'linuxmuster-opsi'
elif profile == 'docker':
    ipnr = '3'
    pkgs = 'docker docker-compose'

# network interface
print('# Interface')
if iface != '' and not iface in iface_list:
    iface = ''
if iface == '':
    iface = iface_default
if (unattended and iface == '') or not unattended:
    while True:
        iface = input('Enter network interface to use ' + str(iface_list) + ': ')
        iface = iface or iface_default
        if iface in iface_list:
            break
        else:
            print("Invalid entry!")

# ip address & netmask
print('# IP')
if ipnet == '':
    ipnet = '10.0.0.' + ipnr + '/16'
# correct ip address
if '.0/' in ipnet and ipnr != '':
    ipnet = ipnet.replace('.0/', '.' + ipnr + '/')
# if ip is still a network address
if '.0/' in ipnet:
    ipnet = ''
    defaultip = '10.0.0.1/16'
else:
    defaultip = ipnet
if (unattended and ipnet == '') or not unattended:
    while True:
        ipnet = input('Enter ip address with net or bitmask [' + defaultip + ']: ')
        ipnet = ipnet or defaultip
        try:
            n = IP(ipnet, make_net=True)
            break
        except ValueError:
            print("Invalid entry!")
else:
    n = IP(ipnet, make_net=True)
try:
    hostip = ipnet.split('/')[0]
except:
    print('Invalid network: ' + ipnet)
    sys.exit(1)
network = IP(n).strNormal(0)
bitmask = IP(n).strNormal(1).split('/')[1]
netmask = IP(n).strNormal(2).split('/')[1]
broadcast = IP(n).strNormal(3).split('-')[1]
o1, o2, o3, o4 = hostip.split('.')

# dns server ip
print('# DNS')
if dnsip == '':
    defaultip = o1 + '.' + o2 + '.' + o3 + '.1'
else:
    defaultip = dnsip
if unattended:
    if not isValidHostIpv4(defaultip):
        print('Invalid dns ip: ' + defaultip)
        sys.exit(1)
    dnsip = defaultip
else:
    while True:
        dnsip = input('Enter dns server ip address [' + defaultip + ']: ')
        dnsip = dnsip or defaultip
        if isValidHostIpv4(dnsip):
            break
        else:
            print("Invalid entry!")

# firewall ip
print('# Firewall')
if firewallip == '':
    defaultip = o1 + '.' + o2 + '.' + o3 + '.254'
else:
    defaultip = firewallip
if unattended == True:
    if not isValidHostIpv4(defaultip):
        print('Invalid firewall ip: ' + defaultip)
        sys.exit(1)
    firewallip = defaultip
else:
    while True:
        firewallip = input('Enter gateway/firewall ip address [' + defaultip + ']: ')
        firewallip = firewallip or defaultip
        if isValidHostIpv4(firewallip):
            break
        else:
            print("Invalid entry!")

# hostname
print('# Hostname')
if not isValidHostname(hostname):
    hostname = ''
if (unattended and hostname == '') or not unattended:
    if hostname == '':
        defaultname = 'ubuntu'
    else:
        defaultname = hostname
    while True:
        hostname = input('Enter hostname [' + defaultname + ']: ')
        hostname = hostname or defaultname
        if isValidHostname(hostname):
            break
        else:
            print("Invalid entry!")

# domainname
print('# Domainname')
if domainname == '':
    defaultdomain = 'linuxmuster.lan'
else:
    defaultdomain = domainname
if unattended == True:
    if not isValidDomainname(domainname):
        print('Invalid domainname: ' + domainname)
        sys.exit(1)
    domainname = defaultdomain
else:
    while True:
        domainname = input('Enter domainname [' + defaultdomain + ']: ')
        domainname = domainname or defaultdomain
        if isValidDomainname(domainname):
            break
        else:
            print("Invalid entry!")

# swap file
print('## Swapfile')
swapfile = '/swapfile'
gbsize = swapsize + 'G'
if os.path.isfile(swapfile):
    os.system('swapoff ' + swapfile)
    os.system('rm ' + swapfile)
    if unattended == True:
        try:
            os.system('fallocate -l ' + gbsize + ' ' + swapfile)
        except:
            print('Cannot create ' + swapfile + '!')
            sys.exit(1)
    else:
        while True:
            defaultsize = swapsize
            swapsize = input('Enter the size of the swapfile in GB [' + defaultsize + ']: ')
            swapsize = swapsize or defaultsize
            gbsize = swapsize + 'G'
            rc = os.system('fallocate -l ' + gbsize + ' ' + swapfile)
            if rc == 0:
                break
            else:
                print("Invalid entry!")
    os.system('chmod 600 ' + swapfile)
    os.system('mkswap ' + swapfile)
    os.system('swapon ' + swapfile)
    os.system('swapon --show')
else:
    print('No swapfile found, skipping this step!')

# root password
print('## Passwords')
if unattended == False or rootpw == '':
    while True:
        rootpw = getpass.getpass(prompt='Type a new root password: ', stream=None)
        rootpw_repeated = getpass.getpass(prompt='Type the password again: ', stream=None)
        if rootpw == rootpw_repeated:
            break
        else:
            print('passwords does not match!')
printr('# root ... ')
rc = os.system('echo "root:' + rootpw + '" | chpasswd')
if rc == 0:
    print('OK!')
else:
    print('Failed!')
if os.path.isdir('/home/linuxmuster'):
    printr('# linuxmuster ... ')
    rc = os.system('echo "linuxmuster:' + rootpw + '" | chpasswd')
    if rc == 0:
        print('OK!')
    else:
        print('Failed!')

# write configs
print('## writing configuration')
os.system('mkdir -p /etc/network/interfaces.d')
os.system('mkdir -p ' + cachedir)
if hostname == 'server':
    serverip = hostip
elif hostname == 'docker':
    dockerip = hostip
elif hostname == 'opsi':
    opsiip = hostip
else:
    serverip = dnsip
for item in os.listdir(templates):
    rc, content = readTextfile(templates + '/' + item)
    # extract oufile path from first line
    firstline = re.findall(r'# .*\n', content)[0]
    outfile = firstline.partition(' ')[2].replace('\n', '')
    # replace placeholders
    content = content.replace('@@iface@@', iface)
    #content = content.replace('@@serverip@@', serverip)
    #content = content.replace('@@opsiip@@', opsiip)
    #content = content.replace('@@dockerip@@', dockerip)
    content = content.replace('@@hostip@@', hostip)
    content = content.replace('@@hostname@@', hostname)
    content = content.replace('@@netmask@@', netmask)
    content = content.replace('@@bitmask@@', bitmask)
    content = content.replace('@@network@@', network)
    content = content.replace('@@profile@@', profile)
    content = content.replace('@@broadcast@@', broadcast)
    content = content.replace('@@firewallip@@', firewallip)
    content = content.replace('@@dnsip@@', dnsip)
    content = content.replace('@@domainname@@', domainname)
    content = content.replace('@@swapsize@@', swapsize)
    # add date string
    content = '# modified by linuxmuster-prepare at ' + dtStr() + '\n' + content
    # write outfile
    writeTextfile(outfile, content, 'w')
# hostname
writeTextfile('/etc/hostname', hostname + '.' + domainname, 'w')

# create ssh hostkeys
print('## ssh host keys')
hostkey_prefix = '/etc/ssh/ssh_host_'
crypto_list = ['dsa', 'ecdsa', 'ed25519', 'rsa']
os.system('rm -f /etc/ssh/*key*')
for a in crypto_list:
    printr(' * ' + a + ' host key:')
    try:
        os.system('ssh-keygen -t ' + a + ' -f ' + hostkey_prefix + a + '_key -N ""')
        print(' Success!')
    except:
        print(' Failed!')
        sys.exit(1)

# host specific software if internet connection is available
if internet():
    print('## Installing updates and host specific software')
    os.system('apt-key add ' + repokey)
    os.system('apt update')
    os.system('DEBIAN_FRONTEND=noninteractive apt -y dist-upgrade')
    os.system('DEBIAN_FRONTEND=noninteractive apt -y --allow-unauthenticated install ' + pkgs)
    os.system('apt clean && apt -y autoremove')
    updates = True

# print values
print('\n## The system has been prepared with the following values:')
print('# Profile  : ' + profile)
print('# Hostname : ' + hostname)
print('# Domain   : ' + domainname)
print('# IP       : ' + hostip)
print('# Netmask  : ' + netmask)
print('# Firewall : ' + firewallip)
print('# DNS      : ' + dnsip)
print('# Interface: ' + iface)
print('# Swapsize : ' + swapsize + 'G')

print('\n### Finished - a reboot is necessary!')

if not updates:
    print("\n### Don't forget to dist-upgrade the system before setup!")
