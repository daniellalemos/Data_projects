import json
from datetime import datetime
import pandas as pd
import requests

city_name = 'Portland'
base_url = 'https://api.openweathermap.org/data/2.5/weather?q='

with open('credentials.txt', 'r') as f:
    api_key = f.read() #key for the api

full_url = base_url + city_name + '&appid=' + api_key


'''
{'coord': {'lon': -122.6762, 'lat': 45.5234}, 'weather': [{'id': 500, 'main': 'Rain', 'description': 'light rain', 'icon': '10d'}], 
'base': 'stations', 'main': {'temp': 277.46, 'feels_like': 273.81, 'temp_min': 275.66, 'temp_max': 279.38, 'pressure': 1008, 'humidity': 91}, 
'visibility': 10000, 'wind': {'speed': 4.63, 'deg': 210}, 'rain': {'1h': 0.81}, 'clouds': {'all': 100}, 'dt': 1709498365, 
'sys': {'type': 2, 'id': 2008548, 'country': 'US', 'sunrise': 1709477077, 'sunset': 1709517642}, 'timezone': -28800, 'id': 5746545, 'name': 'Portland', 'cod': 200}
'''


def kelvin_to_fahrenheit(temp_in_kelvin):
    '''
    Convert kelvins to fahrenheit
    '''
    temp_in_fahrenheit = (temp_in_kelvin - 273.15) * (9/5) + 32
    return temp_in_fahrenheit



def etl_weather_data(url):
    #connect to the api
    r = requests.get(url)
    #convert it to json to get the dictionary with the data
    data = r.json()
    #retrieve informations from json(dictionary)
    city = data["name"]
    weather_description = data["weather"][0]['description']
    temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp"])
    feels_like_farenheit= kelvin_to_fahrenheit(data["main"]["feels_like"])
    min_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_min"])
    max_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_max"])
    pressure = data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    #Convert date in Unix to local time
    time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
    sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
    sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

    #put informations in a dictionary
    transformed_data = {"City": city,
                        "Description": weather_description,
                        "Temperature (F)": temp_farenheit,
                        "Feels Like (F)": feels_like_farenheit,
                        "Minimun Temp (F)":min_temp_farenheit,
                        "Maximum Temp (F)": max_temp_farenheit,
                        "Pressure": pressure,
                        "Humidty": humidity,
                        "Wind Speed": wind_speed,
                        "Time of Record": time_of_record,
                        "Sunrise (Local Time)":sunrise_time,
                        "Sunset (Local Time)": sunset_time                        
                        }

    #Put in a df
    transformed_data_list = [transformed_data]
    df_data = pd.DataFrame(transformed_data_list)
    #save data as csv
    df_data.to_csv("current_weather_portland.csv", index = False)


if __name__ == '__main__':
    etl_weather_data(full_url)