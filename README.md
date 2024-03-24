# Zabbix Event Sensors for Homeassistant ###
Custom Integration to import Zabbix events as HA Sensors

There already is a Zabbix integration in homeassistant but its focus is on publishing homeassistant states to Zabbix. It also can import zabbix states to homeassistant sensors, but you need to configure Zabbix host ids in HA for this and it is limited to importing Zabbix triggers.

As I needed to import the states of Zabbix services as homeassistant sensors I made up this custom component.

## Features
* Available via HACS using this repo as a custom repository
* Zabbix services can be imported as Home Assistant Sensors: The state is set to the Zabbix state number of the service.
* Additionally Zabbix problems can also be imported as Home Assistant sensors by defining tag / value pairs that match those of interesting Zabbix problems. The state is set to the most severe problem if the tag/value of the sensor matches multiple problems.
* Stete of the sensor will be -1 if there is no problem. Values 0 to 5 reflect Zabbix problem states (0=Not classified up to 5=Disaster)

## Prerequisite
Create Zabbix services in Zabbix (WebUI > Services > Services > Edit > Create Service)

## Installation
* Use HACS to import this repository.
* In Homeassistant -> Settings -> Devices -> Add Integration choose "Zabbix Event Sensors".
* Config Wizard
    * Configure the Zabbix hostname or IP, an API Token (must have been configured in Zabbix before) and optionally a port and whether SSL is used for the connection. Please note that the Zabbix certificate currently is not verified.
    * Choose the sensor prefix and which types of sensors should be created.
    * For Zabbix services all configured services in Zabbix are imported as sensors.
    * FOr Zabbix problems please specify all interesting tag/value sets.
* After submitting you will have new "Zabbix Event Sensors" devices under integrations and additionally the Zabbix services as sensor entities. The sensor entities' names are made up by concatenating these elements:

    - sensor.
    - prefix_from_config_flow_
    - either: "service_" or "problem_"
    - zabbix service name or problem tag_value set (e.g. sensor.zabbix_service_network, sensor.zabbix_problem_class_os)

    
