# linuxmuster-prepare

Scripts and configuration templates to initially setup a virtual appliance for linuxmuster.net 7.4.

Skripte und Konfigurationsvorlagen für die Vorbereitung einer virtuellen Appliance für linuxmuster.net 7.4 auf Basis von Ubuntu Server 26.04.

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
  - ubuntu: Es werden keine zusätzliche Pakete installiert, Hostname mit Parameter `-t, --hostname=<hostname>` und IP/Netzmaske mit `-n, --ipnet=<ip/bitmask>` müssen zwingend angegeben werden.

### Beispiele
- `lmn-appliance -u -p server`
  - Richtet Serverprofil mit Standardwerten ein:
  - Hostname _server_,
  - IP/Bitmask _10.0.0.1/16_,
  - Domänenname _linuxmuster.lan_
  - Gateway/DNS _10.0.0.254_
- `lmn-appliance -u -p server -n 10.0.0.1/24`
  - Richtet Serverprofil mit angepasstem IP-Netz ein:
  - Hostname _server_,
  - IP/Bitmask _10.0.0.1/24_,
  - Domänenname _linuxmuster.lan_
  - Gateway/DNS _10.0.0.254_
- `lmn-appliance -p ubuntu -t testhost -n 192.168.0.1/16`
  - Richtet die Appliance wie folgt ein:
  - Hostname _testhost_,
  - IP/Bitmask _192.168.0.1/16_,
  - Domänenname _linuxmuster.lan_,
  - Gateway/DNS _192.16.0.254_

## Server-Appliance vorbereiten
- Appliance mit 2 Festplatten einrichten, zum Beispiel:
  - HD 1: 25G (Root-Dateisystem)
  - HD 2: 100G (Daten auf /srv eingehängt))
- [Ubuntu Server 18.04 Minimalinstallation](https://www.howtoforge.com/tutorial/ubuntu-minimal-server-install/) durchführen.
  - System in eine Partition auf HD 1 installieren (keine Swappartition),
  - auf HD 2 eine ext4-Partition einrichten und unter /srv einhängen Eintrag in `/etc/fstab`:
    `/dev/vdb1 /srv ext4 defaults 0 1`
- Nach dem ersten Boot als root einloggen und Prepare-Skript herunterladen:  
  `# wget https://raw.githubusercontent.com/linuxmuster/linuxmuster-prepare/master/lmn-appliance`
- Skript ausführbar machen und starten:
  `./lmn-appliance -p server -u`
- Appliance herunterfahren und Snapshot erstellen.
- Danach kann das Setup ausgeführt werden.

## Quota
Die Quota-Option für ext4-Partitionen kann nicht mehr zur Laufzeit aktiviert werden, das Dateisystem darf nicht gemountet sein. Dazu wird jetzt unter `/usr/lib/dracut/modules.d/99linuxmuster` ein Dracut-Modul angelegt, das ein Premount-Skript in die Initrd integriert. Dieses Skript aktiviert per `tune2fs` die Quota-Option während des Bootvorgangs bevor die Dateisysteme gemountet werden.

## Ubuntu-Appliances vorbereiten
Generelle Ubuntu-Appliances berücksichtigen nur eine Festplatte bei der Vorbereitung. Die Vorgehensweise ist ansonsten analog zu derjenigen des Servers. Beispiele für Skriptaufrufe siehe oben.