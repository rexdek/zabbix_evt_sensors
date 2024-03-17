# hass_zabbix_api ###
Custom Integration to import Zabbix Services as HA Sensors

There already is a Zabbix integration in homeassistant but its focus is on publishing homeassistant states to Zabbix. It also can import zabbix states to homeassistant sensors, but you need to configure Zabbix host ids in HA for this and it is limited to importing Zabbix triggers.

As I needed to import the states of Zabbix services as homeassistant sensors I made up this custom component.

## Installation
Use HACS to import this repository and install the zabbix_api custom component to homeassistant.

In Homeassistant -> Settings -> Devices -> Add Integration choose zabbix_problems.

In the menu configure the Zabbix hostname or IP, an API Token (must have been configured in Zabbix before) and optionally a port and whether SSL is used for the connection. Please note that the Zabbix vertificate currently is not verified.

After submitting you will have a new "Zabbix API" device under integrations and additionally the Zabbix services as sensor entities. The sensor entities' names are made up by concatenating these elements:

    - sensor.
    
    - zabbix_
    
    - zabbix_host_name (from config flow)
    
    - zabbix service name (from Zabbix)

    
