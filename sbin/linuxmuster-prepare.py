#!/usr/bin/python3
#
# linuxmuster-prepare.py
# thomas@linuxmuster.net
# 20180420
#

import configparser
import datetime
import getopt
import getpass
import netifaces
import os
import pathlib
import re
import reconfigure
import socket
import sys

from IPy import IP
from reconfigure.configs import FSTabConfig
from reconfigure.items.fstab import FilesystemData


# global values
hostname = ''
serverip = ''
hostip = ''
firewallip = ''
ipnet = ''
ipnet_default = '10.0.0.'
bitmask_default = '16'
ipnet_babo = '10.16.1.'
bitmask_babo = '12'
iface = ''
iface_default = ''
network = ''
bitmask = ''
netmask = ''
broadcast = ''
domainname = 'linuxmuster.lan'
swapsize = '2'
pkgs = ''
ipnr = ''
rootpw_default = 'Muster!'
rootpw = 'Muster!'
profile_list = ['server', 'opsi', 'docker', 'ubuntu']
user_list = ['linuxmuster', 'opsiadmin']
profile = ''
pvdevice = ''
vgname = 'vg_srv'
lvmvols = [('var', '10G', '/var'), ('linbo', '40G', '/srv/linbo'), ('global', '10G', '/srv/samba/global'), ('default-school', '100%FREE', '/srv/samba/schools/default-school')]
quotamntopts = 'user_xattr,acl,usrjquota=aquota.user,grpjquota=aquota.group,jqfmt=vfsv0,barrier=1'
unattended = False
# ipset = False
fwset = False
initial = False
setup = False
reboot = False
force = False
updates = False
iniread = False
createcert = False
setup_mode = ''
sharedir = '/usr/share/linuxmuster/prepare'
templates = sharedir + '/templates'
repokey = sharedir + '/lmn7-repo.key'
libdir = '/var/lib/linuxmuster'
prepini = libdir + '/prepare.ini'
setupini = libdir + '/setup.ini'
dockerdir = '/srv/docker'
srvpkgs = 'lvm2'
xenialpkgs = 'resolvconf ifupdown'
bionicpkgs = 'netplan.io net-tools'
issuepkgs = [['xenial', xenialpkgs], ['bionic', bionicpkgs]]
swapfile = '/swap.img'


## functions start

# help
def usage(rc):
    print('Usage: linuxmuster-prepare.py [options]')
    print('\n [options] are:\n')
    print('-x, --force                 : Force run on an already configured system.')
    print('-i, --initial               : Prepare the appliance initially for rollout.')
    print('-s, --setup                 : Further appliance setup (network, swapsize).')
    print('                              Note: You have to use either -i or -s.')
    print('-t, --hostname=<hostname>   : Hostname to apply (optional, works only with')
    print('                              server profile).')
    print('-n, --ipnet=<ip/bitmask>    : Ip address and bitmask assigned to the host')
    print('                              (optional, default is 10.0.0.x/16, depending')
    print('                              on the profile).')
    print('-p, --profile=<profile>     : Host profile to apply, mandatory. Expected')
    print('                              values are "server", "opsi", "docker" or "ubuntu".')
    print('                              Profile name is also used as hostname, except for')
    print('                              "server" if set with -t.')
    print('-c, --createcert            : Create self signed server cert (to be used only')
    print('                              in setup mode and with docker profile).')
    print('-l, --pvdevice=<device>     : Initially sets up lmv on the given device (server profile only).')
    print('-f, --firewall=<firewallip> : Firewall/gateway ip (default *.*.*.254).')
    print('-d, --domain=<domainname>   : Domainname (default linuxmuster.lan).')
    print('-r, --serverip=<serverip>   : Ip address of the server (only in unattended mode).')
    print('-w, --swapsize=<size>       : Swapfile size in GB (default "2").')
    print('-a, --rootpw=<password>     : Set root password (only with -s).')
    print('-b, --reboot                : Reboots finally (only in unattended mode).')
    print('-u, --unattended            : Unattended mode, do not ask, use defaults.')
    print('-e, --default               : Sets default (10.0.0.0/16) network addresses, triggers')
    print('                              setup and unattended modes, needs profile (uses saved')
    print('                              profile from initial run if not given).')
    print('-o, --do-it-like-babo       : Like above, but uses babo (10.0.0.0/16) network addresses.')
    print('-h, --help                  : Print this help.')
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

# get issue name
def getIssue():
    rc, content = readTextfile('/etc/issue')
    issue = content.split(' ')[1]
    if issue > '17.10' or issue == 'Bionic':
        return 'bionic'
    else:
        return 'xenial'

# get issue specific packages
def getIssuePkgs():
    issue = getIssue()
    for item in issuepkgs:
        if item[0] == issue:
            return item[1]

# profile setup (server, opsi, docker)
def do_profile(profile):
    print('## Profile')
    defaultprof = profile
    if not unattended:
        while True:
            profile = input('Enter host profile ' + str(profile_list).replace("'", "") + ' [' + defaultprof + ']: ')
            profile = profile or defaultprof
            if (profile in profile_list) or profile == '':
                break
            else:
                print("Invalid entry!")
    if profile == 'server':
        ipnr = '1'
        pkgs = 'linuxmuster-base7 ' + srvpkgs
    elif profile == 'opsi':
        ipnr = '2'
        pkgs = 'linuxmuster-opsi'
    elif profile == 'docker':
        ipnr = '3'
        pkgs = 'docker docker-compose linuxmuster-nginx-proxy'
    pkgs = pkgs + ' ' + getIssuePkgs()
    return ipnr, pkgs

# network setup
def do_network(iface, iface_default, ipnr, ipnet, hostip, bitmask, netmask, broadcast, firewallip, hostname, domainname, unattended, setup_mode):
    # interface
    print('## Network')
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
    if setup_mode == 'babo':
        ipnet = ipnet_babo + ipnr + '/' + bitmask_babo
    elif setup_mode == 'default' or ipnet == '':
        ipnet = ipnet_default + ipnr + '/' + bitmask_default
    # correct ip address
    if '.0/' in ipnet and ipnr != '':
        ipnet = ipnet.replace('.0/', '.' + ipnr + '/')
    # if ip is still a network address
    if '.0/' in ipnet:
        ipnet = ''
        defaultip = ipnet_default + '1/' + bitmask_default
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
    # firewall ip
    if firewallip == '':
        firewallip = o1 + '.' + o2 + '.' + o3 + '.254'
    if unattended:
        if not isValidHostIpv4(firewallip):
            print('Invalid firewall ip: ' + firewallip)
            sys.exit(1)
    else:
        while True:
            defaultip = firewallip
            firewallip = input('Enter gateway/firewall ip address [' + firewallip + ']: ')
            firewallip = firewallip or defaultip
            if isValidHostIpv4(firewallip):
                break
            else:
                print("Invalid entry!")
    # hostname
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
    return iface, hostname, domainname, hostip, bitmask, netmask, network, broadcast, firewallip

# lvm
def do_lvm(pvdevice, vgname, lvmvols, quotamntopts):
    print('## LVM')
    # if volume group exists do nothing
    vgdisplay = os.popen('vgdisplay').read()
    if ' ' + vgname + '\n' in vgdisplay:
        pvdevice = os.popen("pvdisplay | grep 'PV Name' | awk '{ print $3 }'").read().replace('\n', '')
        print('# Volume group ' + vgname + ' with device ' + pvdevice + ' exists already!')
        return pvdevice
    # ask for pvdevice
    if not unattended:
        while True:
            pvdevice = input('Enter physical device to use for LVM [' + pvdevice + ']: ')
            if pvdevice == '':
                break
            elif pathlib.Path(pvdevice).is_block_device():
                break
            else:
                pvdevice = ''
                print("Invalid entry!")
    if pvdevice == '':
        # return if no pvdevice is entered
        return pvdevice
    rc, fstab = readTextfile('/etc/fstab')
    fstab = fstab + '\n'
    print('# Creating physical volume ' + pvdevice + '.')
    if os.system('pvcreate ' + pvdevice) != 0:
        sys.exit(1)
    print('# Creating volume group ' + vgname + '.')
    if os.system('vgcreate ' + vgname + ' ' + pvdevice) != 0:
        sys.exit(1)
    for item in lvmvols:
        volname = item[0]
        volsize = item[1]
        if '%' in volsize:
            volsize = ' -l ' + volsize
        else:
            volsize = ' -L ' + volsize
        volmnt = item[2]
        os.system('mkdir -p ' + volmnt)
        volpath = '/dev/' + vgname + '/' + volname
        print('# Creating logical volume ' + volname + '.')
        lvcreate = 'lvcreate' + volsize + ' -n ' + volname + ' ' + vgname
        #print('# ' + lvcreate)
        if os.system(lvcreate) != 0:
            sys.exit(1)
        if os.system('mkfs.ext4 -L ' + volname + ' ' + volpath) != 0:
            sys.exit(1)
        # set quota mount options
        if volname == 'global' or volname == 'default-school':
            mntopts = quotamntopts
        else:
            mntopts = 'defaults'
        fstab = fstab + volpath + ' ' + volmnt + ' ext4 ' + mntopts + ' 0 1\n'
    print('# Writing /etc/fstab.')
    if not writeTextfile('/etc/fstab', fstab, 'w'):
        sys.exit(1)
    print('# Moving /var.')
    if os.system('mount /dev/' + vgname + '/var /mnt') != 0:
        sys.exit(1)
    if os.system('rsync -a /var/ /mnt/') != 0:
        sys.exit(1)
    if os.system('umount /mnt && rm -rf /var/* && mount -a') != 0:
        sys.exit(1)
    return pvdevice

# set quota mount options to fstab if no lvm is defined
def do_fstab_root(quotamntopts):
    mntopts = quotamntopts + ',errors=remount-ro'
    config = FSTabConfig(path='/etc/fstab')
    config.load()
    count = 0
    count_max = len(config.tree.filesystems)
    while count < count_max:
        mp = config.tree.filesystems[count].mountpoint
        #print('## Mountpoint ' + str(count) + ' ' + mp)
        if mp == '/':
            print('# Modifying mount options for "' + mp + '".')
            config.tree.filesystems[count].options = mntopts
            config.save()
            os.system('mount -o remount /')
            break
        count += 1

# activate quota on server partitions
def do_quota():
    print('# Activating quota.')
    os.system('quotaoff -a')
    os.system('quotacheck -cvuga')
    os.system('quotaon -a')

# swap file
def do_swap(swapsize):
    print('## Swapfile')
    gbsize = swapsize + 'G'
    if not os.path.isfile(swapfile):
        print('No swapfile found, skipping this step!')
        return
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

# root password
def do_password(rootpw):
    print('## Passwords')
    printr('# root ... ')
    rc = os.system('echo "root:' + rootpw + '" | chpasswd')
    if rc == 0:
        print('OK!')
    else:
        print('Failed!')
    for item in user_list:
        if os.path.isdir('/home/' + item):
            printr('# ' + item + ' ... ')
            rc = os.system('echo "' + item + ':' + rootpw + '" | chpasswd')
        if rc == 0:
            print('OK!')
        else:
            print('Failed!')

# create ssh hostkeys
def do_keys():
    print('## SSH host keys')
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

# create ssl certs (docker only)
def do_sslcert(profile, domainname):
    print('## SSL certificate')
    ssldir = '/etc/linuxmuster/ssl'
    csrfile = ssldir + '/' + profile + '.csr'
    keyfile = ssldir + '/' + profile + '.key.pem'
    certfile = ssldir + '/' + profile + '.cert.pem'
    days = '3653'
    os.system('mkdir -p ' + ssldir)
    os.system('openssl genrsa -out ' + keyfile + ' 2048')
    os.system('chmod 640 ' + keyfile)
    os.system('echo -e "\n\n\n' + domainname + '\n' + profile + '\n' + profile + '\n\n\n\n" | openssl req -new -key ' + keyfile + ' -out ' + csrfile)
    os.system('openssl x509 -req -days ' + days + ' -in ' + csrfile + ' -signkey ' + keyfile + ' -out ' + certfile)

# host specific software if internet connection is available
def do_updates(pkgs):
    if not internet():
        print('# No internet connection!')
        sys.exit(1)
    print('## Installing updates and host specific software')
    os.system('apt-key add ' + repokey)
    os.system('apt update')
    os.system('DEBIAN_FRONTEND=noninteractive apt -y dist-upgrade')
    os.system('DEBIAN_FRONTEND=noninteractive apt -y --allow-unauthenticated install ' + pkgs)
    os.system('apt clean && apt -y autoremove')
    updates = True
    return updates

# merge inifiles
def mergeInis():
    print('## Merging inifiles:')
    setup = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    for item in [setupini, prepini]:
        # skip non existant file
        if not os.path.isfile(item):
            print('# ' + item + ' not found!')
            return False
        # reading setup values
        print('# Reading ' + item)
        setup.read(item)
    # writing setup.ini
    print('# Writing ' + setupini)
    try:
        with open(setupini, 'w') as outfile:
            setup.write(outfile)
    except:
        print('# Writing failed!')
        return False
    # remove prepare.ini
    os.unlink(prepini)

# print setup values
def print_values(profile, hostname, domainname, hostip, netmask, firewallip, iface, swapsize, pvdevice):
    print('\n## The system has been prepared with the following values:')
    print('# Profile   : ' + profile)
    print('# Hostname  : ' + hostname)
    print('# Domain    : ' + domainname)
    print('# IP        : ' + hostip)
    print('# Netmask   : ' + netmask)
    print('# Firewall  : ' + firewallip)
    print('# Interface : ' + iface)
    print('# Swapsize  : ' + swapsize + 'G')
    if pvdevice != '':
        print('# LVM device: ' + pvdevice)

## functions end


os.system('clear')
print('### linuxmuster-prepare')

# get cli args
try:
    opts, args = getopt.getopt(sys.argv[1:], "a:bcd:ef:hil:n:op:r:st:uw:x", ["rootpw=", "reboot", "createcert", "domain=", "default", "firewall=", "help", "initial", "pvdevice=", "ipnet=", "profile=", "do-it-like-babo", "serverip=", "setup", "hostname=", "unattended", "swapsize=", "force"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    usage(2)

# read saved profile from previous run
inifile = ''
if os.path.isfile(prepini):
    inifile = prepini
elif os.path.isfile(setupini):
    inifile = setupini
if inifile != '':
    print('## Reading profile from ' + inifile + ':')
    prep = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    prep.read(inifile)
    # try:
    #     domainname_ini = prep.get('setup', 'domainname')
    #     if domainname_ini != '':
    #         domainname = domainname_ini
    #         print('# domainname: ' + domainname)
    # except:
    #     pass
    # try:
    #     hostip_ini = prep.get('setup', 'hostip')
    #     if hostip_ini != '':
    #         hostip = hostip_ini
    #         print('# hostip: ' + hostip)
    # except:
    #     pass
    # try:
    #     hostname_ini = prep.get('setup', 'hostname')
    #     if hostname_ini != '':
    #         hostname = hostname_ini
    #         print('# hostname: ' + hostname)
    # except:
    #     pass
    try:
        profile_ini = prep.get('setup', 'profile')
        if profile_ini != '':
            # profile = profile_ini
            print('# saved profile: ' + profile_ini)
    except:
        pass
    # try:
    #     serverip_ini = prep.get('setup', 'serverip')
    #     if serverip_ini != '':
    #         serverip = serverip_ini
    #         print('# serverip: ' + serverip)
    # except:
    #     pass
    # try:
    #     firewallip_ini = prep.get('setup', 'firewallip')
    #     if firewallip_ini != '':
    #         firewallip = firewallip_ini
    #         print('# firewallip: ' + firewallip)
    # except:
    #     pass
    # try:
    #     bitmask_ini = prep.get('setup', 'bitmask')
    #     if bitmask_ini != '':
    #         bitmask = bitmask_ini
    #         print('# bitmask: ' + bitmask)
    # except:
    #     pass
    # try:
    #     swapsize_ini = prep.get('setup', 'swapsize')
    #     if swapsize_ini != '':
    #         swapsize = swapsize_ini
    #         print('# swapsize: ' + swapsize)
    # except:
    #     pass
    # if hostip != '' and bitmask !='':
    #     ipnet = hostip + '/' + bitmask

# evaluate options
for o, a in opts:
    if o in ("-u", "--unattended"):
        unattended = True
    elif o in ("-e", "--default"):
        setup_mode = 'default'
        unattended = True
        setup = True
    elif o in ("-o", "--do-it-like-babo"):
        setup_mode = 'babo'
        unattended = True
        setup = True
    elif o in ("-x", "--force"):
        force = True
    elif o in ("-c", "--createcert"):
        createcert = True
    elif o in ("-w", "--swapsize"):
        swapsize = str(a)
    elif o in ("-p", "--profile"):
        if a in profile_list:
            profile = a
        else:
            usage(1)
    elif o in ("-t", "--hostname"):
        hostname = a
    elif o in ("-l", "--pvdevice"):
        pvdevice = a
    elif o in ("-r", "--serverip"):
        serverip = a
    elif o in ("-b", "--reboot"):
        reboot = True
    elif o in ("-i", "--initial"):
        initial = True
    elif o in ("-s", "--setup"):
        setup = True
    elif o in ("-d", "--domain"):
        domainname = a
    elif o in ("-a", "--rootpw"):
        rootpw = a
    elif o in ("-n", "--ipnet"):
        ipnet = a
        # ipset = True
    elif o in ("-f", "--firewall"):
        firewallip = a
        fwset = True
    elif o in ("-h", "--help"):
        usage(0)
    else:
        assert False, "unhandled option"
        usage(1)

# exit if system is already set up
if force:
    print("## Force is given, skipping test for configured system.")
else:
    if os.path.isfile(setupini):
        print("## Don't do this on an already configured system!")
        sys.exit(1)

# test values
if setup_mode != '':
    if profile == '' and profile_ini != '':
        profile = profile_ini
if not profile in profile_list or profile == '':
    print('Invalid profile!')
    usage(1)
if profile != 'server':
    pvdevice = ''
    hostname = profile
else:
    if hostname == '':
        hostname = 'server'
if ipnet == '' and profile == '':
    usage(1)
if pvdevice != '' and initial == False:
    print('LVM setup works only with -i!')
    usage(1)
if setup == False and initial == False:
    print('You have to provide either -i or -s!')
    usage(1)
if setup == True and initial == True:
    print("-i and -s don't work together!")
    usage(1)
if setup == False and profile != 'docker' and createcert == True:
    print("-c can only be used together with -s and docker profile!")
    usage(1)
# pvdevice
if pvdevice != '':
    if not pathlib.Path(pvdevice).is_block_device():
        print('# ' + pvdevice + 'is not a block device!')
        sys.exit(1)
# swapsize
if not str.isdigit(swapsize):
    usage(1)
# override ini values if ipnet was set on cli
# if ipset:
#     if not fwset:
#         firewallip = ''
# do not set in interactive mode
if unattended == False:
    reboot = False

# get network interfaces
iface_list, iface_default = getDefaultIface()
if len(iface_list) == 0:
    print('# No network interfaces found!')
    sys.exit(1)

# main
if initial:
    serverip = ''
    rootpw = rootpw_default
    ipnr, pkgs = do_profile(profile)
    iface, hostname, domainname, hostip, bitmask, netmask, network, broadcast, firewallip = do_network(iface, iface_default, ipnr, ipnet, hostip, bitmask, netmask, broadcast, firewallip, hostname, domainname, unattended, setup_mode)
    if profile == 'server':
        pvdevice = do_lvm(pvdevice, vgname, lvmvols, quotamntopts)
        if pvdevice == '':
            do_fstab_root(quotamntopts)
        do_quota()
    do_password(rootpw)
    updates = do_updates(pkgs)
    if profile == 'opsi':
        os.system('linuxmuster-opsi --prepare')
    writeTextfile('/etc/hostname', hostname + '.' + domainname, 'w')
    dnssearch = ''
elif setup:
    ipnr, pkgs = do_profile(profile)
    iface, hostname, domainname, hostip, bitmask, netmask, network, broadcast, firewallip = do_network(iface, iface_default, ipnr, ipnet, hostip, bitmask, netmask, broadcast, firewallip, hostname, domainname, unattended, setup_mode)
    do_swap(swapsize)
    # write hostname before keys and certificates were created
    writeTextfile('/etc/hostname', hostname + '.' + domainname, 'w')
    do_keys()
    if profile == 'docker' and createcert:
        do_sslcert(profile, domainname)
    do_password(rootpw)
    dnssearch = 'search: [' + domainname + ']'

# write configs, common and issue specific
print('## Writing configuration')
os.system('mkdir -p ' + libdir)
# delete cloud-init netcfg if present (we provide our own)
if os.path.isdir('/etc/netplan') and getIssue() == 'bionic':
    os.system('rm -f /etc/netplan/*.yaml')
for tdir in [templates + '/common', templates + '/' + getIssue()]:
    for item in os.listdir(tdir):
        rc, content = readTextfile(tdir + '/' + item)
        # extract oufile path from first line
        firstline = re.findall(r'# .*\n', content)[0]
        outfile = firstline.partition(' ')[2].replace('\n', '')
        # replace placeholders
        content = content.replace('@@iface@@', iface)
        content = content.replace('@@hostip@@', hostip)
        content = content.replace('@@hostname@@', hostname)
        content = content.replace('@@bitmask@@', bitmask)
        content = content.replace('@@netmask@@', netmask)
        content = content.replace('@@network@@', network)
        content = content.replace('@@broadcast@@', broadcast)
        content = content.replace('@@profile@@', profile)
        content = content.replace('@@firewallip@@', firewallip)
        content = content.replace('@@domainname@@', domainname)
        content = content.replace('@@dnssearch@@', dnssearch)
        content = content.replace('@@swapsize@@', swapsize)
        #content = content.replace('@@resolvconf@@', resolvconf)
        if outfile == prepini and profile == 'server':
            content = content.replace('@@serverip@@', hostip)
        else:
            content = content.replace('@@serverip@@', serverip)
        # repair missing serverip in netcfg.yaml
        content = content.replace('[,', '[')
        # add date string
        content = '# modified by linuxmuster-prepare at ' + dtStr() + '\n' + content
        # write outfile
        writeTextfile(outfile, content, 'w')

# merge inifiles if setup.ini is present
if os.path.isfile(setupini):
    mergeInis()

# apply netplan configuration
if getIssue() == 'bionic':
    print('## Configuring netplan')
    os.system('netplan generate')
    os.system('netplan apply')
os.system('hostnamectl set-hostname ' + hostname + '.' + domainname)

# finally reconfigure docker containers
if profile == 'docker' and setup == True:
    print('## Reconfiguring docker containers')
    os.system('cd ' + dockerdir + '; for i in linuxmuster-*; do dpkg-reconfigure "$i"; systemctl enable "$i"; done')

# print values
print_values(profile, hostname, domainname, hostip, netmask, firewallip, iface, swapsize, pvdevice)

print('\n### Finished - a reboot is necessary!')

if not updates:
    print("\n### Don't forget to dist-upgrade the system before setup!")

if unattended and reboot:
    print('\n### Reboot requested ...')
    os.system('/sbin/reboot')
