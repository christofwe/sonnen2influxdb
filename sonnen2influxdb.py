import os
import json
import requests
from requests.auth import HTTPBasicAuth

import time
from datetime import datetime, timedelta
import pytz

from influxdb import InfluxDBClient

INFLUXDB_HOST = os.environ['INFLUXDB_HOST']
INFLUXDB_PORT = os.environ['INFLUXDB_PORT']
INFLUXDB_USER = os.environ['INFLUXDB_USER']
INFLUXDB_PASS = os.environ['INFLUXDB_PASS']
INFLUXDB_DB_NAME = os.environ['INFLUXDB_DB_NAME']

SONNEN_API_IP = os.environ['SONNEN_API_IP']
SONNEN_API_TOKEN = os.environ['SONNEN_API_TOKEN']


tz = pytz.timezone(os.environ['TZ'])
local = tz.localize(datetime.now())
timestamp = local.strftime("%Y-%m-%dT%H:%M:%S%Z%z")

influx_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USER, password=INFLUXDB_PASS)
influx_client.switch_database(INFLUXDB_DB_NAME)
influx_body = []

sonnen_api_base_url = f"http://{SONNEN_API_IP}/api/v2"
sonnen_headers = {'Auth-Token': SONNEN_API_TOKEN}

try:
  sonnen_response_status = requests.get(f"{sonnen_api_base_url}/status", headers=sonnen_headers)
  time.sleep(2)
  sonnen_response_latestdata = requests.get(f"{sonnen_api_base_url}/latestdata", headers=sonnen_headers)

  sonnen_response_status.raise_for_status()
  sonnen_response_latestdata.raise_for_status()

  sonnen_metrics_status = json.loads(sonnen_response_status.text)
  sonnen_metrics_latestdata = json.loads(sonnen_response_latestdata.text)

  values_status_watts = ["Consumption_W", "Consumption_Avg", "GridFeedIn_W", "Pac_total_W", "Production_W"]
  values_status_volts = ["Fac", "Uac", "Ubat"]
  values_status_percent = ["RSOC", "USOC"]

  values_latest_watts = ["FullChargeCapacity", "SetPoint_W"]
  values_latest_volts = []
  values_latest_ic_status = ["statebms", "statecorecontrolmodule", "stateinverter"]

  timestamp_status = tz.localize(datetime.fromisoformat(sonnen_metrics_status['Timestamp']))
  timestamp_latestdata = tz.localize(datetime.fromisoformat(sonnen_metrics_latestdata['Timestamp']))

  for value_status_watt in values_status_watts:
    item = {
      "measurement": value_status_watt,
      "tags": {
      },
      "time": timestamp_status.isoformat(),
      "fields": {
        "watts": sonnen_metrics_status[value_status_watt]
      }
    }
    influx_body.append(item)

  for value_status_volt in values_status_volts:
    item = {
      "measurement": value_status_volt,
      "tags": {
      },
      "time": timestamp_status.isoformat(),
      "fields": {
        "volts": sonnen_metrics_status[value_status_volt]
      }
    }
    influx_body.append(item)

  for value_status_percent in values_status_percent:
    item = {
      "measurement": value_status_percent,
      "tags": {
      },
      "time": timestamp_status.isoformat(),
      "fields": {
        "percent": sonnen_metrics_status[value_status_percent]
      }
    }
    influx_body.append(item)

  for value_latest_watt in values_latest_watts:
    item = {
      "measurement": value_latest_watt,
      "tags": {
      },
      "time": timestamp_latestdata.isoformat(),
      "fields": {
        "watts": sonnen_metrics_latestdata[value_latest_watt]
      }
    }
    influx_body.append(item)

  for value_latest_volt in values_latest_volts:
    item = {
      "measurement": value_latest_volt,
      "tags": {
      },
      "time": timestamp_latestdata.isoformat(),
      "fields": {
        "volts": sonnen_metrics_latestdata[value_latest_volt]
      }
    }
    influx_body.append(item)

  for value_latest_ic_status in values_latest_ic_status:
    item = {
      "measurement": value_latest_ic_status,
      "tags": {
      },
      "time": timestamp_latestdata.isoformat(),
      "fields": {
        "value": sonnen_metrics_latestdata['ic_status'][value_latest_ic_status]
      }
    }
    influx_body.append(item)


  if sonnen_metrics_latestdata['ic_status']['Eclipse Led']['Pulsing White']:
    current_status_eclipse = "Pulsing White"
  elif sonnen_metrics_latestdata['ic_status']['Eclipse Led']['Pulsing Green']:
    current_status_eclipse = "Pulsing Green"
  elif sonnen_metrics_latestdata['ic_status']['Eclipse Led']['Pulsing Orange']:
    current_status_eclipse = "Pulsing Orange"
  elif sonnen_metrics_latestdata['ic_status']['Eclipse Led']['Solid Red']:
    current_status_eclipse = "Solid Red"
  else:
    current_status_eclipse = "NA"

  status_eclipse = {
    "measurement": "status_eclipse",
      "tags": {
      },
      "time": timestamp_latestdata.isoformat(),
      "fields": {
        "value": current_status_eclipse
      }
  }
  influx_body.append(status_eclipse)

  influxdb_write = influx_client.write_points(influx_body)
  print(f"{timestamp} influx_write: {influxdb_write}")

except requests.exceptions.HTTPError as error:
  print(f"sonnen_metrics error: {error}")
  print(f"sonnen_metrics_latestdata status_code: {sonnen_metrics_latestdata.status_code}")
  print(f"sonnen_metrics_status status_code: {sonnen_metrics_status.status_code}")
