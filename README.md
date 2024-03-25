# Zabbix Event Sensors for Homeassistant ###
Custom Integration to import Zabbix events as HA Sensors

There already is a Zabbix integration in homeassistant but its focus is on publishing homeassistant states to Zabbix. It also can import zabbix states to homeassistant sensors, but you need to configure Zabbix host ids in HA for this and it is limited to importing Zabbix triggers.

As I needed to import the states of Zabbix services as homeassistant sensors I made up this custom component.

## Features
* Available via HACS using this repo as a custom repository
* Import Zabbix services as Home Assistant Sensors
* Import Zabbix problems as Home Assistant sensors by defining tag / value pairs that match those of interesting Zabbix problems. The state is set to the most severe problem if the tag/value of the sensor matches multiple problems.
* Stete of the sensor will be -1 if there is no problem. Values 0 to 5 reflect Zabbix problem states (0=Not classified up to 5=Disaster)

## What can I do with it?
[Zabbix](https://www.zabbix.com/) is a monitoring solution for your IT infrastructure. It can detect problem states and report it on its web interface. With this Home Assistant integration these problems can be imported as sensors into Home Assistant. You can import two types of Zabbix problem indicators:

* Zabbix services: Services are an aggregation function. A service monitors the state of several problems and reports an aggregated state based on configurable rules. Each configured service is imported as a sensor in Home Assistant.
* Zabbix problems: Problems can be automatically tagged in Zabbix with tag/value pairs. A tag/value pair can be mapped to a Home Assistant sensor. The sensor reports the state of all prblems matching the tag/value pair in its attributes and sets its state to the most severe of them.

## Prerequisite
If you would like to use Home Assistant sensors based on Zabbix services, you have to create these in Zabbix in advance:
* WebUI > Services > Services > Edit > Create Service)

## Installation
* Use HACS to import this repository:
   * Home Assistant > HACS > Integrations > ... Menu > Custom Repositories > https://github.com/rexdek/zabbix_evt_sensors
* After importing the repo set it up in Homeassistant:
   * Settings -> Devices -> Add Integration choose "Zabbix Event Sensors".
* Configure the integration with the config wizard:
   * Configure the Zabbix hostname or IP, an API Token (must have been configured in Zabbix before) and optionally a port and whether SSL is used for the connection. Please note that the Zabbix certificate currently is not verified.
   * Choose the sensor prefix and which types of sensors should be created.
   * For Zabbix services all configured services in Zabbix are imported as sensors.
   * For Zabbix problems please specify all interesting tag/value sets.
* After submitting you will have new "Zabbix Event Sensors" devices under integrations and additionally the Zabbix services as sensor entities. The sensor entities' names are made up by concatenating these elements:

    - sensor.
    - prefix_from_config_flow_
    - either: "service_" or "problem_"
    - zabbix service name or problem tag_value set (e.g. sensor.zabbix_service_network, sensor.zabbix_problem_class_os)

    
