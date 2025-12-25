#!/usr/bin/env python3
# encoding=utf-8

from pytz import timezone
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
import sys
import socket
import subprocess
import platform
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


speedtestPath="/usr/bin/speedtest"

# debug enviroment variables
debug_str=os.getenv("DEBUG", None)
if debug_str is not None:
	debug = debug_str.lower() == "true"
else:
	debug = False


# influxDBv2 envionment variables
influxdb2_host=os.getenv('INFLUXDB2_HOST', "localhost")
influxdb2_port=int(os.getenv('INFLUXDB2_PORT', "8086"))
influxdb2_org=os.getenv('INFLUXDB2_ORG', "Home")
influxdb2_token=os.getenv('INFLUXDB2_TOKEN', "token")
influxdb2_bucket=os.getenv('INFLUXDB2_BUCKET', "DEV")

influxdb2_ssl_str=os.getenv('INFLUXDB2_SSL', "False")
if influxdb2_ssl_str is not None:
    influxdb2_ssl = influxdb2_ssl_str.lower() == "true"
else:
    influxdb2_ssl = False

influxdb2_ssl_verify_str=os.getenv('INFLUXDB2_SSL_VERIFY', "False")
if influxdb2_ssl_verify_str is not None:
    influxdb2_ssl_verify = influxdb2_ssl_verify_str.lower() == "true"
else:
    influxdb2_ssl_verify = False

# speedtest envionment variables
speedtest_server = os.getenv("SPEEDTEST_SERVER")
expected_down = os.getenv("EXPECTED_DOWN")
expected_up = os.getenv("EXPECTED_UP")
host = os.getenv("HOST", socket.gethostname())


# hard encoded envionment varables

# brew tap teamookla/speedtest
# brew update
# brew install speedtest --force
#speedtestPath="/usr/local/bin/speedtest"


# report debug/domac status
if debug:
	print ( " debug: TRUE" )
else:
	print ( " debug: FALSE" )
	
if influxdb2_ssl_verify:
	print ( "verify: TRUE" )
else:
	print ( "verify: FALSE" )


# influxDBv2
if influxdb2_ssl_str:
    influxdb2_url="https://" + influxdb2_host + ":" + str(influxdb2_port)
else:
    influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)

if debug:
	print ( "influx: "+influxdb2_url )
	print ( "bucket: "+influxdb2_bucket )
	
if influxdb2_ssl_verify:
	print ( "verify: True" )
	client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org, verify_ssl=True)
else:
	print ( "verify: False" )
	client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org, verify_ssl=False)

write_api = client.write_api(write_options=SYNCHRONOUS)


# Run Speedtest
if speedtest_server:
    print("Running Speedtest : ", speedtest_server)
    speedtest_server_arg = "--server-id="+speedtest_server
    rawResults = subprocess.run([speedtestPath, '--accept-license', '--accept-gdpr', '--format=json', speedtest_server_arg], stdout=subprocess.PIPE, text=True, check=True)
else:
    print("Running Speedtest : random server")
    rawResults = subprocess.run([speedtestPath, '--accept-license', '--accept-gdpr', '--format=json'], stdout=subprocess.PIPE, text=True, check=True)

results = json.loads(rawResults.stdout.strip())


# Basic values
speed_down = results["download"]["bandwidth"] / 100000.0
speed_up = results["upload"]["bandwidth"] / 100000.0
ping_latency = results["ping"]["latency"]
ping_jitter = results["ping"]["jitter"]
result_url = results["result"]["url"]

# Advanced values
speedtest_server_id = results["server"]["id"]
speedtest_server_name = results["server"]["name"]
speedtest_server_location = results["server"]["location"]
speedtest_server_country = results["server"]["country"]
speedtest_server_host = results["server"]["host"]

# Print results to Docker logs
if expected_down:
    percent_down = ( 100.0 * speed_down / float(expected_down) ) - 100.0
    print("download %.1f mbps = %+.1f of %.0f mbps" % (speed_down,percent_down,float(expected_down)))
else:
    print("download %.1f mbps" % (speed_down))

if expected_up:
    percent_up = ( 100.0 * speed_up / float(expected_up) ) - 100.0
    print("  upload %.1f mbps = %+.1f of %.0f mbps" % (speed_up,percent_up,float(expected_up)))
else:
    print("  upload %.1f mbps" % (speed_up))

print("    latency %.1f ms" % (ping_latency))
print("    jitter  %.1f ms" % (ping_jitter))

if debug:
    print("server id       ", speedtest_server_id)
    print("server name     ", speedtest_server_name)
    print("server location ", speedtest_server_location)
    print("server country  ", speedtest_server_country)
    print("server host     ", speedtest_server_host)
    print("result URL      ", result_url)

# downloads
senddata={}

senddata["measurement"]="speedtest"
senddata["tags"]={}
senddata["tags"]["source"]="docker speedtest-influxdbv2"
senddata["tags"]["origin"]="speedtest.net"
senddata["tags"]["direction"]="download"
senddata["tags"]["host"]=host
senddata["fields"]={}
senddata["fields"]["data-rate"]=speed_down

if expected_down:
    senddata["fields"]["percent"]=percent_down
    senddata["fields"]["expected"]=float(expected_down)

if debug:
    print ("INFLUX: "+influxdb2_bucket)
    print (json.dumps(senddata,indent=4))
write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])

# uploads
senddata={}

senddata["measurement"]="speedtest"
senddata["tags"]={}
senddata["tags"]["source"]="docker speedtest-influxdbv2"
senddata["tags"]["origin"]="speedtest.net"
senddata["tags"]["direction"]="upload"
senddata["tags"]["host"]=host
senddata["fields"]={}
senddata["fields"]["data-rate"]=speed_up

if expected_up:
    senddata["fields"]["percent"]=percent_up
    senddata["fields"]["expected"]=float(expected_up)

if debug:
    print ("INFLUX: "+influxdb2_bucket)
    print (json.dumps(senddata,indent=4))
write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])

# other
senddata={}

senddata["measurement"]="speedtest"
senddata["tags"]={}
senddata["tags"]["source"]="docker speedtest-influxdbv2"
senddata["tags"]["origin"]="speedtest.net"
senddata["tags"]["host"]=host
senddata["fields"]={}
senddata["fields"]["latency"]=ping_latency
senddata["fields"]["jitter"]=ping_jitter

if debug:
    print ("INFLUX: "+influxdb2_bucket)
    print (json.dumps(senddata,indent=4))
write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])
