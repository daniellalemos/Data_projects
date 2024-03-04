from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.http.sensors.http import HttpSensor
import json
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
import pandas as pd
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


def kelvin_to_fahrenheit(temp_in_kelvin):
    '''
    Convert kelvins to fahrenheit
    '''
    temp_in_fahrenheit = (temp_in_kelvin - 273.15) * (9/5) + 32
    return round(temp_in_fahrenheit, 3)


def transform_load_data(task_instance):
    '''
    Transform and load the data.
    The task_instance is the previous task - extraction
    '''
    #pull data that the previous task returned
    data = task_instance.xcom_pull(task_ids="group_a.tsk_extract_houston_weather_data")
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

    transformed_data = {"city": city,
                        "description": weather_description,
                        "temperature_farenheit": temp_farenheit,
                        "feels_like_farenheit": feels_like_farenheit,
                        "minimun_temp_farenheit":min_temp_farenheit,
                        "maximum_temp_farenheit": max_temp_farenheit,
                        "pressure": pressure,
                        "humidity": humidity,
                        "wind_speed": wind_speed,
                        "time_of_record": time_of_record,
                        "sunrise_local_time)":sunrise_time,
                        "sunset_local_time)": sunset_time                        
                        }
    transformed_data_list = [transformed_data]
    df_data = pd.DataFrame(transformed_data_list)
    
    df_data.to_csv("current_weather_data.csv", index = False, header = False)


def load_weather():
    '''
    Load the csv data to the postgres
    '''
    hook = PostgresHook(postgres_conn_id= 'postgres_conn')
    hook.copy_expert(
        sql = "COPY weather_data FROM stdin WITH DELIMITER as ','",
        filename = 'current_weather_data.csv'
    )


def save_joined_data_s3(task_instance):
    '''
    Load the joined data in S3 bucket
    '''
    #pull from the previous data that was generated when joined the data
    data = task_instance.xcom_pull(task_ids = "task_join_data")
    df = pd.DataFrame(data, columns = ['city', 'description', 'temperature_farenheit', 'feels_like_farenheit', 'minimun_temp_farenheit', 'maximum_temp_farenheit', 'pressure','humidity', 'wind_speed', 'time_of_record', 'sunrise_local_time', 'sunset_local_time', 'state', 'census_2020', 'land_area_sq_mile_2020'])
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    dt_string = 'joined_weather_data_' + dt_string
    df.to_csv(f"s3://testiing-bucket/{dt_string}.csv", index = False)


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


with DAG('weather_dag_2',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:

        #1st (dummy) task - start the pipeline 
        start_pipeline = DummyOperator(
            task_id = 'tsk_start_pipeline'
        )

        #2nd task - join the data from the group (weather data + city look up data)
        join_data = PostgresOperator(
                task_id = 'task_join_data',
                postgres_conn_id = "postgres_conn",
                sql = '''SELECT 
                    w.city,                    
                    description,
                    temperature_farenheit,
                    feels_like_farenheit,
                    minimun_temp_farenheit,
                    maximum_temp_farenheit,
                    pressure,
                    humidity,
                    wind_speed,
                    time_of_record,
                    sunrise_local_time,
                    sunset_local_time,
                    state,
                    census_2020,
                    land_area_sq_mile_2020                    
                    FROM weather_data w
                    INNER JOIN city_look_up c
                        ON w.city = c.city                                      
                ;
                '''
            )

        #3rd task - load the joined data in s3
        load_joined_data = PythonOperator(
            task_id = 'task_load_joined_data',
            python_callable = save_joined_data_s3
            )
        
        #4th (dummy) task - end the pipeline 
        end_pipeline = DummyOperator(
                task_id = 'task_end_pipeline'
        )

        #create a group to do the parallel processing
        with TaskGroup(group_id = 'group_a', tooltip= "Extract_from_S3_and_weatherapi") as group_A:

            create_table_1 = PostgresOperator(
                task_id = 'tsk_create_table_1',
                postgres_conn_id = "postgres_conn",
                #1st task: SQL statement - what I want to do (create a table)
                sql = '''  
                    CREATE TABLE IF NOT EXISTS city_look_up (
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    census_2020 numeric NOT NULL,
                    land_Area_sq_mile_2020 numeric NOT NULL                    
                );
                '''
            )
            #2nd task - If the table created have data already, truncate the data 
            truncate_table = PostgresOperator(
                task_id ='tsk_truncate_table',
                postgres_conn_id = "postgres_conn",
                sql = ''' TRUNCATE TABLE city_look_up;
                    '''
            )
            #3rd task - grab the csv file from the S3 bucket and upload it in the table
            uploadS3_to_postgres  = PostgresOperator(
                task_id = "tsk_uploadS3_to_postgres",
                postgres_conn_id = "postgres_conn",
                sql = "SELECT aws_s3.table_import_from_s3('city_look_up', '', '(format csv, DELIMITER '','', HEADER true)', 'testiing-bucket', 'us_city.csv', 'eu-west-3');"
            )

            #Do the other workflow ETL but inside the same group

            #4th task - create a table with the weather data from the API
            create_table_2 = PostgresOperator(
                task_id = 'tsk_create_table_2',
                postgres_conn_id = "postgres_conn",
                sql = ''' 
                    CREATE TABLE IF NOT EXISTS weather_data (
                    city TEXT,
                    description TEXT,
                    temperature_farenheit NUMERIC,
                    feels_like_farenheit NUMERIC,
                    minimun_temp_farenheit NUMERIC,
                    maximum_temp_farenheit NUMERIC,
                    pressure NUMERIC,
                    humidity NUMERIC,
                    wind_speed NUMERIC,
                    time_of_record TIMESTAMP,
                    sunrise_local_time TIMESTAMP,
                    sunset_local_time TIMESTAMP                    
                );
                '''
            )

            #5th task - connect to the API and verify if is ready before the next task
            is_houston_weather_api_ready = HttpSensor(
                task_id ='tsk_is_houston_weather_api_ready',
                http_conn_id ='weathermap_api',
                endpoint ='/data/2.5/weather?q=houston&APPID=8fd27dae808563b5261861dd01c897ac'
            )

            #6th task - extract data
            extract_houston_weather_data = SimpleHttpOperator(
                task_id = 'tsk_extract_houston_weather_data',
                http_conn_id = 'weathermap_api',
                endpoint='/data/2.5/weather?q=houston&APPID=8fd27dae808563b5261861dd01c897ac',
                method = 'GET',
                response_filter = lambda r: json.loads(r.text),
                log_response = True
            )

            #7th task - transform the data
            transform_load_houston_weather_data = PythonOperator(
                task_id = 'transform_load_houston_weather_data',
                python_callable = transform_load_data
            )

            #8th task - load the data(csv) in the postgres
            load_weather_data = PythonOperator(
            task_id = 'tsk_load_weather_data',
            python_callable = load_weather
            )


            #order of pipeline in the group that run in parallel
            create_table_1 >> truncate_table >> uploadS3_to_postgres
            create_table_2 >> is_houston_weather_api_ready >> extract_houston_weather_data >> transform_load_houston_weather_data >> load_weather_data
        #order of the full pipeline
        start_pipeline >> group_A >> join_data >> load_joined_data >> end_pipeline