# Garo measure car charging

This repos is for measuring electric car charging while using Garo
charge stations. It can be one, or full network of chargers.

The script fetches data from all Garo stations in the network.
There needs to be network connection to Garo. Easiest is to
connect to wlan of Garo box. And yes, you need to have it with
the wlan module.

The script fetches each boxes serial number and reference name
and uses them as influxdb tags. The data field is the energy
consumption. So it keeps increasing immediately when you start
charing. Unit is 1 kW.

Program exits after sending data once. You need to keep calling
it from systemd timer or cron to get values periodicly.


There needs to be garo2influxdb.ini with connection details.
See the garo2influxdb-example.ini.


