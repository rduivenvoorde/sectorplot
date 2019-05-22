
# http://stackoverflow.com/questions/10529351/using-a-psycopg2-converter-to-retrieve-bytea-data-from-postgresql

import numpy as np
import psycopg2, psycopg2.extras

def my_adapter(spectrum):
    return psycopg2.Binary(spectrum)

def my_converter(my_buffer, cursor):
    return np.frombuffer(my_buffer)

class MyBinaryTest():

    # Connection info
    user = 'tmpuser'
    password = 'tmpuser!'
    host = 'jrodos.dev.cal-net.nl'
    database = 'RodosHome'

    def __init__(self):
        pass


    def set_up(self):

        # Direct connectly to the database and set up our table
        self.connection = psycopg2.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)


    def perform_test_one(self):

        # Retrieve the data
        query = self.cursor.execute('select zoneradii from npp limit 1')
        result = self.cursor.fetchall()

        print(result)
        print(result[0])
        print(result[0][0])
        print(unicode(result[0][0]))

        # ???
        #shape = (2, 100)
        # Convert it back to a numpy array of the same shape
        #retrieved_data = np.frombuffer(result[0]['data']).reshape(*shape)
        #print(retrieved_data)

        return True


    def setup_adapters_and_converters(self):

        # Set up test adapters
        psycopg2.extensions.register_adapter(np.ndarray, my_adapter)

        # Register our converter
        self.cursor.execute("select null::bytea;")
        my_oid = self.cursor.description[0][1]

        obj = psycopg2.extensions.new_type((my_oid, ), "numpy_array", my_converter)
        psycopg2.extensions.register_type(obj, self.connection)

        self.connection.commit()

        self.use_adapters = True


    def tear_down(self):

        # Close connections
        self.cursor.close()
        self.connection.close()

test = MyBinaryTest()
test.set_up()
test.perform_test_one()
test.tear_down()
