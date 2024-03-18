# Zabbix Event Sensors for Homeassistant ###
Custom Integration to import Zabbix events as HA Sensors

There already is a Zabbix integration in homeassistant but its focus is on publishing homeassistant states to Zabbix. It also can import zabbix states to homeassistant sensors, but you need to configure Zabbix host ids in HA for this and it is limited to importing Zabbix triggers.

As I needed to import the states of Zabbix services as homeassistant sensors I made up this custom component.

## Prerequisite
Create Zabbix services in Zabbix (WebUI > Services > Services > Edit > Create Service)

## Installation
Use HACS to import this repository and install the zabbix_evt_sensors custom component to homeassistant.

In Homeassistant -> Settings -> Devices -> Add Integration choose "Zabbix Event Sensors".

In the menu configure the Zabbix hostname or IP, an API Token (must have been configured in Zabbix before) and optionally a port and whether SSL is used for the connection. Please note that the Zabbix certificate currently is not verified.

After submitting you will have a new "Zabbix Event Sensors" device under integrations and additionally the Zabbix services as sensor entities. The sensor entities' names are made up by concatenating these elements:

    - sensor.
    
    - zabbix_
    
    - zabbix_host_name (from config flow)
    
    - zabbix service name (from Zabbix)
    
