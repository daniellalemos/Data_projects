from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.http.sensors.http import HttpSensor
import json
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
import pandas as pd



def kelvin_to_fahrenheit(temp_in_kelvin):
    '''
    Convert kelvins to fahrenheit
    '''
    temp_in_fahrenheit = (temp_in_kelvin - 273.15) * (9/5) + 32
    return temp_in_fahrenheit


def transform_load_data(task_instance):
    '''
    Transform and load the data.
    The task_instance is the previous task - extraction
    '''
    data = task_instance.xcom_pull(task_ids="extract_weather_data")
    city = data["name"]
    weather_description = data["weather"][0]['description']
    temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp"])
    feels_like_farenheit= kelvin_to_fahrenheit(data["main"]["feels_like"])
    min_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_min"])
    max_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_max"])
    pressure = data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
    sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
    sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

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
    transformed_data_list = [transformed_data]
    df_data = pd.DataFrame(transformed_data_list)
    aws_credentials = {"key": "", "secret": "", "token": ""} #add credentials!

    now = datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    dt_string = 'current_weather_data_portland_' + dt_string
    #save the csv file inside the S3 bucket
    df_data.to_csv(f"s3://openweatherapiibucket/{dt_string}.csv", index = False, storage_options = aws_credentials)



default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 4), #when airflow will start running
    'email': ['lemosdaniela3@gmail.com'],
    'email_on_failure': True, #if the pipeline fails email me
    'email_on_retry': False, #when it wants to retry it should email me
    'retries': 2,
    'retry_delay': timedelta(minutes = 2) #when it fails how many minutes it should wait before retrying again
}


with DAG('weather_dag',
        default_args = default_args,
        schedule_interval = '@daily', #it's going to run daily 
        catchup = False) as dag:

        #fist task - connect to the API and verify if is ready before the next task
        is_weather_api_ready = HttpSensor(
        task_id = 'is_weather_api_ready',
        http_conn_id = 'weathermap_api',
        endpoint = '/data/2.5/weather?q=Portland&APPID=8fd27dae808563b5261861dd01c897ac'
        )

        #second task - extract data
        extract_weather_data = SimpleHttpOperator(
        task_id = 'extract_weather_data',
        http_conn_id = 'weathermap_api',
        endpoint = '/data/2.5/weather?q=Portland&APPID=8fd27dae808563b5261861dd01c897ac',
        method = 'GET',
        response_filter =  lambda r: json.loads(r.text),
        log_response = True
        )

        #third task - transform the data and load
        transform_load_weather_data = PythonOperator(
        task_id = 'transform_load_weather_data',
        python_callable = transform_load_data
        )


        #define the workflow
        is_weather_api_ready >> extract_weather_data >> transform_load_weather_data