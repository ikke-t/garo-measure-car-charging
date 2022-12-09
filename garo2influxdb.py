#!python3
"""
This module sends Garo electric car charger network usage values
into influxdb. It is recommended to run this periodicly e.g. from
systemd timer or cronjob.

Program needs config file describing the influxdb and garo device
details.

You need to have network connection to Garo device for this to work.

To get going with influxdb:
    python3 -m venv virtualenv
    source virtualenv/bin/activate
    pip install influxdb-client
https://docs.influxdata.com/influxdb/cloud/api-guide/client-libraries/python/

Author: Ilkka Tengvall <ilkka.tengvall@iki.fi>
License: GPLv3 or later
"""

from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime
import json
import configparser
import logging

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

def send_measurements(garo_vals, cnf):
    """
    We send data to influxdb. Datapoints are in garo_vals dict, and we
    find influxdb based on cnf values
    """
    influxdb_client = InfluxDBClient(url=cnf.get('INFLUX', 'INFLUX_URL'),
                                     token=cnf.get('INFLUX', 'INFLUX_TOKEN'),
                                     org=cnf.get('INFLUX', 'INFLUX_ORG'))
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    time = datetime.utcnow()
    success = 0
    for g in garo_vals:
        point = Point("garos") \
            .tag("reference", g["reference"]) \
            .tag("serialNumber", g["serialNumber"]) \
            .field("accEnergy", g["accEnergy"]) \
            .time(time)
        logging.info(f"Writing: {point.to_line_protocol()}")
        client_response = write_api.write(
                              bucket=cnf.get('INFLUX', 'INFLUX_BUCKET'),
                              record=point)
        # write() returns None on success
        if client_response is None:
            success += 1
    return success


if __name__ == "__main__":

	# pylint: disable=C0103
    error = False
    config = configparser.ConfigParser()
    config.read('garo2influxdb.ini')

    verbosity = config.get('DEBUG', 'VERBOSITY', fallback='NOTSET')
    logging.basicConfig(level=verbosity, format='%(levelname)s:%(message)s')
    logging.debug('loglevel %s', verbosity)

    garo_address = config.get('GARO', 'GARO_ADDRESS')
    url = 'http://' + garo_address + ':8080/servlet/rest/chargebox/slaves/false'
    # for debug: url = "https://xxx.yyy/slaves-false.json"

    # get the Garo charging station network data
    logging.info("Connecting to : %s", url)
    try:
        response = urlopen(url)
    except HTTPError as err:
        if err.code == 404:
            error = True
            print("Page not found!")
        elif err.code == 403:
            error = True
            print("Access denied!")
        else:
            error = True
            print("Something prevented Garo connection! Error code", err.code)
    except URLError as err:
        error = True
        print("Some Garo connection error happened: ", err.reason)
    #  response = open('slaves-false.json',)

    if error is True:
        response.close()
        raise SystemExit('Could not connect to Garo, check your network and address.')

    now = datetime.now()

    garos = json.loads(response.read())
    response.close()
    logging.debug("Response: %s", json.dumps(garos, indent=2))

    save_keys = ("reference", "serialNumber", "accEnergy")
    dictfilt = lambda x, y: dict([ (i,x[i]) for i in x if i in set(y) ])

    data = []

    for i in garos:
        filtered_fields = dictfilt(i, save_keys)
        data.append(filtered_fields)

    logging.debug("Filtered list: %s", json.dumps(data, indent=2))
    succeeded = send_measurements(data, config)
    logging.info("sent %i of %i.", succeeded, len(data))

    if verbosity == 'DEBUG':
        flat_dict = {d['reference']: d['accEnergy'] for d in data}
        logging.debug(flat_dict)

        sorted_dict = {int(x):flat_dict[x] for x in flat_dict.keys()}
        json_out = json.dumps(sorted_dict, indent=2, sort_keys=True)
        logging.debug(json_out)

    exit()
