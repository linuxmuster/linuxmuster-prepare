# linuxmuster-prepare 7.4.2

## Zuverlässigeres Systemupdate

`linuxmuster-distupgrade` aktualisiert die linuxmuster-Pakete jetzt zuverlässig
auch dann, wenn ein Paket neue Abhängigkeiten mitbringt, die mit bereits
installierten Paketen kollidieren. Bislang blieben solche Pakete beim Update
einfach zurück.

Neu sind außerdem die Optionen `-c, --clean` (räumt am Ende den Paketcache auf)
und `-h, --help` (zeigt eine Kurzhilfe).

## Fehlerfreier Systemstart bei aktivierten Quotas

Auf von 7.3 aktualisierten Systemen blieben veraltete Quota-Einstellungen
zurück, die bei jedem Start zu Fehlermeldungen und einem fehlgeschlagenen
Systemdienst führten. `lmn-prepare` räumt diese Altlasten nun auf – der
Systemstart läuft wieder fehlerfrei, die Quota-Erfassung arbeitet unverändert.

Signed-off by: thomas@linuxmuster.net
Assisted by  : Claude

