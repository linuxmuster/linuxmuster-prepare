# linuxmuster-prepare

Scripts and configuration templates to initially setup a virtual appliance for linuxmuster.net 7.1 & 7.2.

Skripte und Konfigurationsvorlagen für die Vorbereitung einer virtuellen Appliance für linuxmuster.net 7.1/7.2 auf Basis von Ubuntu Server 18.04/22.04.

## Das Skript lmn-appliance

[lmn-appliance](https://raw.githubusercontent.com/linuxmuster/linuxmuster-prepare/master/lmn-appliance) bereitet die Appliance für das Rollout vor:
- Es bringt das Betriebssystem auf den aktuellen Stand,
- richtet das linuxmuster.net-Paket-Repo ein,
- installiert das Paket **linuxmuster-prepare** und
- startet dann das Vorbereitungsskript _lmn-prepare_,
  - das die für das jeweilige Appliance-Profil benötigten Pakete installiert,
  - das Netzwerk konfiguriert,
  - das root-Passwort auf _Muster!_ setzt und
  - im Falle des Serverprofils optional LVM einrichtet.

Installation:
- Skript herunterladen:  
  `wget https://raw.githubusercontent.com/linuxmuster/linuxmuster-prepare/master/lmn-appliance`
- Ausführbar machen:
  `chmod +x lmn-appliance`
- Skript starten:
  `./lmn-appliance <Optionen>`

Wird `lmn-appliance` ohne Optionen aufgerufen, richtet es nur das linuxmuster.net-Paket-Repo ein und aktualisiert das System. Die Vorbereitung der Appliance muss in dem Fall anschließend mit `lmn-prepare` gemacht werden (Optionen siehe `lmn-prepare -h`).

### Optionen von lmn-appliance

Parameter | Wert | Bedeutung
----------|------|----------
`-t, --hostname=` | `<hostname>` | Hostname der Appliance, falls weggelassen wird der Profilname verwendet.
`-n, --ipnet=` | `<ip/bitmask>` | IP-Adresse und Bitmaske des Hosts (Standardwert ist 10.0.0.[1,2,3]/16, abhängig vom Profil).
`-p, --profile=` | `<server\|ubuntu>` | Appliance-Profil, wurde -n nicht angegeben, wird die IP-Adresse für _server_ automatisch gesetzt (10.0.0.1). Im Falle von _ubuntu_ muss mit -n eine Adresse/Bitmaske angegeben werden.
`-l, --pvdevice=` | `<device>` | Pfad zum LVM-Device (nur bei Serverprofil), kann eine Partition oder eine komplette Disk sein (optional). Wird kein LVM-Device angegeben, gilt die vorhandene Partitionierung.
`-v, --volumes=` | `<name:size,name:size,...>` | Liste von LVM-Volumes mit Namen und Größe. Beispiel: `linbo:50%FREE,global:10,default-school:100%FREE` bedeutet "linbo" bekommt 50% des Volumes, "global" bekommt 10G und "default-school" den gesamten Rest. Es müssen mindestens "linbo", "global" und "default-school" angegeben werden, "var" kann weggelassen werden. "global" und "default-school" werden quotiert. Standardwert ist: "var:10,linbo:40,global:10,default-school:100%FREE".
`-w, --swapsize=` | `<#>` | Größe der Swapdatei in GiB (Standard 2).
`-f, --firewall=` | `<ip>` | Firewall-/Nameserver-Adresse (Standard x.x.x.254).
`-g, --gateway=` | `<ip>` | Gateway-Adresse (Standard ist Firewall-IP).
`-d, --domain=` | `<domain>` | Domänenname (Standard: linuxmuster.lan).
`-u, --unattended` | - | Keine Abfragen, verwende Standardwerte.
`-b, --reboot` | - | Abschließender Neustart (nur zusammen mit _unattended_).
`-h, --help` | - | Hilfe anzeigen.

### Profilvorgaben
- server:
  - Paket _linuxmuster-base7_ mit allen seinen Abhängigkeiten wird installiert.
  - Wird per Parameter `-l, --pvdevice=<device>` ein LVM-Device angegeben (Partition oder Disk), wird diese wie folgt mit LVM eingerichtet (Werte beziehen sich auf eine Festplattengröße von 100G. Für das LV _default-school_ wird immer der verbleibende Rest genommen. Festplattengröße muss daher mindestens 70G betragen.):

    LV Name | LV Pfad | Mountpoint | Größe
    --------|---------|------------|------
    var | /dev/vg_srv/var | /var | 10G
    linbo | /dev/vg_srv/linbo | /srv/linbo | 40G
    global | /dev/vg_srv/global | /srv/samba/global | 10G
    default-school | /dev/vg_srv/default-school | /srv/samba/default-school | 40G

  - Per Parameter `-v, --volumes=<name:size,name:size,...>` kann die Volumegröße angepasst werden. `var` kann weggelassen werden.

- ubuntu: Es werden keine zusätzliche Pakete installiert, Hostname mit Parameter `-t, --hostname=<hostname>` und IP/Netzmaske mit `-n, --ipnet=<ip/bitmask>` müssen zwingend angegeben werden.

### Beispiele
- `lmn-appliance -u -p server -l /dev/sdb`
  - Richtet Serverprofil mit LVM auf 2. Festplatte mit Standardwerten ein:
  - Hostname _server_,
  - IP/Bitmask _10.0.0.1/16_,
  - Domänenname _linuxmuster.lan_
  - Gateway/DNS _10.0.0.254_
- `lmn-appliance -u -p server -n 10.0.0.1/24 -l /dev/sda5 -v linbo:50%FREE,global:10,default-school:100%FREE`
  - Richtet Serverprofil mit selbst festgelegten LVM-Volumes auf Partition sda5 und angepasstem IP-Netz ein:
  - Hostname _server_,
  - IP/Bitmask _10.0.0.1/24_,
  - Domänenname _linuxmuster.lan_
  - Gateway/DNS _10.0.0.254_
- `lmn-appliance -p ubuntu -t testhost -n 10.16.1.10/12`
  - Richtet die Appliance wie folgt ein:
  - Hostname _testhost_,
  - IP/Bitmask _10.16.1.10/12_,
  - Domänenname _linuxmuster.lan_,
  - Gateway/DNS _10.16.1.254_

## Server-Appliance vorbereiten
- Appliance mit 2 Festplatten einrichten, zum Beispiel:
  - HD 1: 25G (Root-Dateisystem)
  - HD 2: 100G (LVM)
- [Ubuntu Server 18.04 Minimalinstallation](https://www.howtoforge.com/tutorial/ubuntu-minimal-server-install/) durchführen.
  - System in eine Partition auf HD 1 installieren (keine Swappartition),
  - HD 2 unkonfiguriert lassen.
- Nach dem ersten Boot als root einloggen und Prepare-Skript herunterladen:  
  `# wget https://raw.githubusercontent.com/linuxmuster/linuxmuster-prepare/master/lmn-appliance`
- Skript ausführbar machen und starten:
  `./lmn-appliance -p server -u -l /dev/sdb`
- Appliance herunterfahren und Snapshot erstellen.

## Ubuntu-Appliances vorbereiten
Generelle Ubuntu-Appliances berücksichtigen nur eine Festplatte bei der Vorbereitung. Die Vorgehensweise ist ansonsten analog zu derjenigen des Servers. Beispiele für Skriptaufrufe siehe oben.
