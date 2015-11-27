import psycopg2
import psycopg2.extras
import credentials


def do_queries(queries, conn_string=credentials.conn_strings['db02.dev.cal-net.nl']):
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    for query in queries:
        cursor.execute(query['text'], query['vals'])
    #print(cursor.statusmessage)
    #print(cursor.rowcount)
    if 'SELECT' in str(cursor.statusmessage):
        memory = cursor.fetchall()
    else:
        memory = None
    conn.commit()
    cursor.close()
    conn.close()
    if memory is not None:
        return memory
