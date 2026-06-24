# linuxmuster-prepare

Scripts and configuration templates to prepare a virtual appliance for linuxmuster.net 7.4 based on Ubuntu Server 26.04.

## The lmn-appliance script

[lmn-appliance](https://raw.githubusercontent.com/linuxmuster/linuxmuster-prepare/master/lmn-appliance) prepares the appliance for rollout:

- It brings the operating system up to date,
- sets up the linuxmuster.net package repository,
- installs the **linuxmuster-prepare** package, and
- then starts the preparation script _lmn-prepare_,
  - which installs the packages required for the respective appliance profile,
  - configures the network,
  - sets the root password to _Muster!_, and
  - optionally sets up LVM in the case of the server profile.

Installation:

- Download the script:  
  `wget https://raw.githubusercontent.com/linuxmuster/linuxmuster-prepare/master/lmn-appliance`
- Make it executable:
  `chmod +x lmn-appliance`
- Run the script:
  `./lmn-appliance <options>`

If `lmn-appliance` is called without options, it only sets up the linuxmuster.net package repository and updates the system. In that case, the appliance preparation must be completed afterwards with `lmn-prepare` (see `lmn-prepare -h` for options).

### Options for lmn-appliance

Parameter | Value | Description
--- | --- | ---
`-t, --hostname=` | `<hostname>` | Hostname of the appliance; if omitted, the profile name is used.
`-n, --ipnet=` | `<ip/bitmask>` | IP address and bitmask of the host (default is 10.0.0.[1,2,3]/16, depending on the profile).
`-p, --profile=` | `<server\|ubuntu>` | Appliance profile; if `-n` was not specified, the IP address for _server_ is set automatically (10.0.0.1). For _ubuntu_, an address/bitmask must be provided with `-n`.
`-w, --swapsize=` | `<#>` | Swap file size in GiB (default 2).
`-f, --firewall=` | `<ip>` | Firewall/nameserver address (default x.x.x.254).
`-g, --gateway=` | `<ip>` | Gateway address (default is the firewall IP).
`-d, --domain=` | `<domain>` | Domain name (default: linuxmuster.lan).
`-u, --unattended` | - | No prompts, use default values.
`-b, --reboot` | - | Final reboot (only in combination with _unattended_).
`-h, --help` | - | Show help.

### Profile defaults

- server: The _linuxmuster-base7_ package with all its dependencies is installed.
- ubuntu: No additional packages are installed; hostname must be specified with `-t, --hostname=<hostname>` and IP/netmask with `-n, --ipnet=<ip/bitmask>`.

### Examples

- `lmn-appliance -u -p server`
  - Sets up the server profile with default values:
  - Hostname _server_,
  - IP/Bitmask _10.0.0.1/16_,
  - Domain name _linuxmuster.lan_,
  - Gateway/DNS _10.0.0.254_
- `lmn-appliance -u -p server -n 10.0.0.1/24`
  - Sets up the server profile with a custom IP network:
  - Hostname _server_,
  - IP/Bitmask _10.0.0.1/24_,
  - Domain name _linuxmuster.lan_,
  - Gateway/DNS _10.0.0.254_
- `lmn-appliance -p ubuntu -t testhost -n 192.168.0.1/16`
  - Sets up the appliance as follows:
  - Hostname _testhost_,
  - IP/Bitmask _192.168.0.1/16_,
  - Domain name _linuxmuster.lan_,
  - Gateway/DNS _192.16.0.254_

## Preparing the server appliance

- Set up the appliance with 2 hard disks, for example:
  - HD 1: 25G (root filesystem)
  - HD 2: 100G (data mounted at /srv)
- Perform a [Ubuntu Server 18.04 minimal installation](https://www.howtoforge.com/tutorial/ubuntu-minimal-server-install/).
  - Install the system into a single partition on HD 1 (no swap partition),
  - create an ext4 partition on HD 2 and mount it at /srv with the following entry in `/etc/fstab`:
    `/dev/vdb1 /srv ext4 defaults 0 1`
- After the first boot, log in as root and download the prepare script:  
  `# wget https://raw.githubusercontent.com/linuxmuster/linuxmuster-prepare/master/lmn-appliance`
- Make the script executable and run it:
  `./lmn-appliance -p server -u`
- Shut down the appliance and create a snapshot.
- The setup can then be run.

## Quota

The quota option for ext4 partitions can no longer be enabled at runtime while the filesystem is mounted. A Dracut module is therefore created under `/usr/lib/dracut/modules.d/99linuxmuster` that integrates a pre-mount script into the initrd. This script enables the quota option via `tune2fs` during the boot process before the filesystems are mounted.

## Preparing Ubuntu appliances

General Ubuntu appliances consider only a single hard disk during preparation. The procedure is otherwise analogous to that of the server. See the examples for script invocations above.
