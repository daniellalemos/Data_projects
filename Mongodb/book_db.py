from dotenv import load_dotenv, find_dotenv
import os
import pprint
import certifi
from pymongo import MongoClient
from datetime import datetime as dt
# load the environment variable file
load_dotenv(find_dotenv())


# get the password
password = os.environ.get('MONGODB_PWD')
connection_string = f'mongodb+srv://danielalemoss20:{password}@project.9gvdldj.mongodb.net/?retryWrites=true&w=majority&appName=Project'

# connect
ca = certifi.where()
client = MongoClient(connection_string, tlsCAFile = ca)

# databases
dbs = client.list_database_names()

production = client.production

# schema validation
def create_book_collection():
    book_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title", "authors", "publish_date", "type", "copies"],
            "properties": {
                "title": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "authors": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "objectId",
                        "description": "must be an objectid and is required"
                    }
                },
                "publish_date": {
                    "bsonType": "date",
                    "description": "must be a date and is required"
                },
                "type": {
                    "enum": ["Fiction", "Non-Fiction"],
                    "description": "can only be one of the enum values and is required"
                },
                "copies": {
                    "bsonType": "int",
                    "minimum":0,
                    "description": "must be an integer greater than O and is required"
                },
            }
        }
    }

    # create the collection book 
    try:
        production.create_collection('book')
    except Exception as e:
        print(e)

    # modify the collection
    production.command('collMod', 'book', validator = book_validator)

# create the author collection
def create_author_collection():
    author_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["first_name", "last_name", "date_of_birth"],
            "properties": {
                "first_name": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "last_name": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "date_of_birth": {
                    "bsonType" : "date",
                    "description": "must be a date and is required"
                },
            }
        }
    }

    try:
        production.create_collection('author')
    except Exception as e:
        print(e)

    production.command('collMod', 'author', validator = author_validator)

#create_book_collection()
#create_author_collection()

# Add some sample data with bulk inserting 

def create_data():
    authors = [
        {
            "first_name": "Tim",
            "last_name": "Ruscica",
            "date_of_birth": dt(2000, 7, 20)
        },
        {
            "first_name": "George",
            "last_name": "Orwell",
            "date_of_birth": dt(1903, 6, 25)
        },
        {
            "first_name": "Herman",
            "last_name": "Melville",
            "date_of_birth": dt(1819, 8, 1)
        },
        {
            "first_name": "F. Scott",
            "last_name": "Fitzgerald",
            "date_of_birth": dt(1896, 9, 24)
        }
    ]
    author_collection = production.author
    # IDs of authors
    authors = author_collection.insert_many(authors).inserted_ids

    books = [
        {
            "title": "MondoDB Advanced Tutorial",
            "authors": [authors[0]], #index of the author (ID)
            "publish_date": dt.today(),
            "type": "Non-Fiction",
            "copies": 5
        },
        {
            "title": "Python For Dummies",
            "authors": [authors[0]],
            "publish_date": dt(2022, 1, 17),
            "type": "Non-Fiction",
            "copies": 5
        },
        {
            "title": "Nineteen Eighty-Four",
            "authors": [authors[1]],
            "publish_date": dt(1949, 6, 8),
            "type": "Fiction",
            "copies": 5
        },
        {
            "title": "The Great Gatsby",
            "authors": [authors[3]],
            "publish_date": dt(2014, 5, 23),
            "type": "Fiction",
            "copies": 5
        },
        {
            "title": "Moby Dick",
            "authors": [authors[2]],
            "publish_date": dt(1851, 9, 24),
            "type": "Fiction",
            "copies": 5
        }
    ]
    book_collection = production.book
    book_collection.insert_many(books)

#create_data()

printer = pprint.PrettyPrinter()

# Queries
    
#retrieve all of the books that conatin the letter A in the title

books_containing_a = production.book.find({'title': {'$regex': 'a{1}'}})
#printer.pprint(list(books_containing_a))

# JOIN operation. 
# Grab every single one of the authors, but i want a field in the authors that contains all of the books they wrote

authors_and_books = production.author.aggregate([{
    '$lookup': {
        'from': 'book',
        'localField': '_id', 
        'foreignField': 'authors',
        'as': 'books'
    }
}])

#printer.pprint(list(authors_and_books))

# Get authors and a count of how many books they wrote

authors_book_count = production.author.aggregate([{
    '$lookup': {
        'from': 'book',
        'localField': '_id', 
        'foreignField': 'authors',
        'as': 'books'
    }
},
{
    '$addFields': {
        'total_books': {'$size': '$books'} 
    }
},
{
    '$project': {'first_name': 1, 'last_name': 1, 'total_books': 1, '_id': 0},
}
])

#printer.pprint(list(authors_book_count))

# Grab all the authors and their books but only for a certain authors age (50-150)

books_with_old_authors = production.book.aggregate([
    {
        '$lookup': {
            'from': 'author', 
            'localField': 'authors',
            'foreignField': '_id',
            'as': 'authors'
        }
    },
    {
        '$set': {
            'authors': {
                '$map': {
                    'input': '$authors',
                    'in': {
                        'age': {
                            '$dateDiff': {
                                'startDate': '$$this.date_of_birth',
                                'endDate': '$$NOW',
                                'unit': 'year'
                            }
                        },
                        'firstname': '$$this.first_name',
                        'last_name': '$$this.last_name',
                    }
                }
            }
        }
    },
    {
        '$match': {
            '$and': [
                {'authors.age': {'$gte': 50}},
                {'authors.age': {'$lte': 130}},
            ]
        }
    },
    {
        '$sort': {
            'age': 1
        }
    }
])

#printer.pprint(list(books_with_old_authors))


# Convert data from MongoDB to a pandas dataframe, arrow table and numpy array

import pyarrow
from pymongoarrow.api import Schema
from pymongoarrow.monkey import patch_all 
import pymongoarrow as pma
from bson import ObjectId

patch_all()

author = Schema({'_id': ObjectId, 'first_name': pyarrow.string(), 'last_name': pyarrow.string(), 'date_of_birth': dt})

df = production.author.find_pandas_all({}, schema = author)
#print(df.head())

arrow_table = production.author.find_arrow_all({}, schema = author)
#print(arrow_table)

nparrays = production.author.find_numpy_all({}, schema = author)
print(nparrays)