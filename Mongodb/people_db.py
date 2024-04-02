from dotenv import load_dotenv, find_dotenv
import os
import pprint
import certifi
from pymongo import MongoClient
# load the environment variable file
load_dotenv(find_dotenv())


# get the passwords
password = os.environ.get('MONGODB_PWD')
connection_string = f'mongodb+srv://danielalemoss20:{password}@project.9gvdldj.mongodb.net/?retryWrites=true&w=majority&appName=Project'

# connect
ca = certifi.where()
client = MongoClient(connection_string, tlsCAFile = ca)

# databases
dbs = client.list_database_names()
#print(dbs)

# acess a db
test_db = client.test
# list all the collections inside of the db
collections = test_db.list_collection_names()
#print(collections)

# inserting documents
def insert_test_doc():
    collection = test_db.test
    test_document = {
        'name': 'Tim',
        'type': 'Test'
    }
    inserted_id = collection.insert_one(test_document).inserted_id
    print(inserted_id)

#insert_test_doc()

# create database
production = client.production
# create collection
person_collection = production.person_collection
# create document

def create_documents():
    first_names = ['Tim', 'Sarah', 'Jennifer', 'Jose', 'Brad', 'Allen']
    last_names = ['Ruscica', 'Smith', 'Bart', 'Cater', 'Pit', 'Geral' ]
    ages = [21, 40, 23, 19, 34, 67]

    docs = []
    #insert various documents
    for first_name, last_name, age in zip(first_names, last_names, ages):
        doc = {'first_name': first_name, 'last_name': last_name, 'age': age}
        docs.append(doc)
    #insert various documents    
    person_collection.insert_many(docs)    

#create_documents()

printer = pprint.PrettyPrinter()

# reading documents
def find_all_people():
    # find all the people in the collection
    people = person_collection.find()

    for person in people:
        printer.pprint(person)

#find_all_people()
        
# look for a specific document based on a field value
def find_person():
    person = person_collection.find_one({'first_name': 'Tim'})
    printer.pprint(person)

#find_person()

# count all the people
def count_all_people():
    #count = person_collection.find().count()
    count = person_collection.count_documents(filter = {})
    print('Number of people', count)

#count_all_people()

# find person by their ID
def get_person_by_id(person_id):
    from bson.objectid import ObjectId
    #converts the string to an id object
    _id = ObjectId(person_id)
    person = person_collection.find_one({'_id': _id})
    printer.pprint(person)

#get_person_by_id('6604ac198c8a80f43abfc32b')
    
# get a specific age range
def get_age_range(min_age, max_age):
    query = {'$and': [
            {'age': {'$gte': min_age}},
            {'age': {'$lte': max_age}},
        ]}
    people = person_collection.find(query).sort('age')
    for person in people:
        printer.pprint(person)

#get_age_range(20,35)

# project specific columns

def project_columns():
    #columns that I want in result
    columns = {'_id': 0, 'first_name': 1, 'last_name': 1}
    people = person_collection.find({}, columns)
    for person in people:
        printer.pprint(person)

#project_columns()

# Updating documents
        
def update_person_by_id(person_id):
    from bson.objectid import ObjectId
    #converts the string to an id object
    _id = ObjectId(person_id)
    all_updates = {
        '$set': {'new_field':  True},
        '$inc': {'age': 1},
        '$rename': {'first_name': 'first', 'last_name': 'last'}
    }
    person_collection.update_one({'_id': _id}, all_updates)

#update_person_by_id('6604ac198c8a80f43abfc32a')
    
def update_person_by_id2(person_id):
    from bson.objectid import ObjectId
    #converts the string to an id object
    _id = ObjectId(person_id)
    person_collection.update_one({'_id': _id}, {'$unset': {'new_field': ''}})

#update_person_by_id2('6604ac198c8a80f43abfc32a')
    
# replacing documents
def replace_one(person_id):
    from bson.objectid import ObjectId
    #converts the string to an id object
    _id = ObjectId(person_id)
    #keep the same ID but change the other fields
    new_doc = {
        'first_name': 'new first name',
        'last_name': 'new last name',
        'age': 100
    }

    person_collection.replace_one({'id': _id}, new_doc)

#replace_one('6604ac198c8a80f43abfc32a')
    
# delete documents
def delete_doc_by_id(person_id):
    from bson.objectid import ObjectId
    #converts the string to an id object
    _id = ObjectId(person_id)
    person_collection.delete_one({'_id': _id})

delete_doc_by_id('6604ac198c8a80f43abfc32a')

# Relationships

address = {
    '_id': '6604ac198c8a80f43abfc32k',
    'street': 'Bay Street',
    'number': 2706,
    'city': 'San Francisco',
    'country': 'United States',
    'zip': '94107'
}

person = {
    'id': '6604ac198c8a80f43abfc32a',
    'first_name': 'John',
}

def add_address_embed(person_id, address):
    from bson.objectid import ObjectId
    #converts the string to an id object
    _id = ObjectId(person_id)

    person_collection.update_one({'_id': _id}, {'$addToSet': {'addresses': address}})

#add_address_embed('6604ac198c8a80f43abfc32b', address)
    
def add_address_relationship(person_id, address):
    from bson.objectid import ObjectId
    #converts the string to an id object
    _id = ObjectId(person_id)
    address = address.copy()
    address['owner_id'] = person_id
    #new collection for address
    address_collection = production.address
    address_collection.insert_one(address)

add_address_relationship('6604ac198c8a80f43abfc32c', address)
