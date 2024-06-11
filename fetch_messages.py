import boto3
import json
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import psycopg2
import base64

# Secret key and IV for AES (should be securely managed)
SECRET_KEY = b'sixteenbytekey!!!'  # Ensure this key is 16 bytes for AES-128
IV = b'sixteenbyteiv0000'  # 16 bytes IV for CBC mode

# Inorder to mask the PII data - I am going to use an encryption technique called AES 
# we can do hashing but we can't recover the values transformed using hashing

# so, AES does encryption to IP, device_id - we will encrypt all the values using the 
# same secret key, IV pairs - as we are using the same key pairs - we will get
# same masking values after transformation - hepls to identify duplicates

def encrypt(value):
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(value.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(IV), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(encrypted).decode()

# decrytpion is to get back the original values later on - we can decrypt using 
# the same secret key, IV pairs used above for encryption.

def decrypt(encrypted_value):
    encrypted_data = base64.b64decode(encrypted_value.encode())
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(IV), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    return decrypted.decode()

# Inorder to connect to the SQS service to read the messages, we will use boto3 
# boto3 is the SDK for python in order to interact and manage AWS services. 

def connect_to_sqs():
    sqs = boto3.client('sqs', endpoint_url='http://localhost:4566', region_name='us-east-1')
    return sqs
 

def receive_messages(sqs_client, queue_url):
    """ 
    function to read messages that are available in SQS Queue service

    Data structures - lists for storing multiple records fetched from the SQS queue  
    before processing them, This allows for batch processing and easy iteration.
    """
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5
    )
    return response.get('Messages', [])
 

def process_message(message):
    """
    function to mask values using AES encryption functions used above.

    Initially the message is a dictionary - suitable data structure to handle JSON format

    so, Here also we are adding two more fields and returning back a dictionary.
    """
    message['masked_device_id'] = encrypt(message['device_id'])
    message['masked_ip'] = encrypt(message['ip'])
    return message

# Function to insert the data into postgres database.
def insert_into_db(conn, data):
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        data['user_id'], data['device_type'], data['masked_ip'],
        data['masked_device_id'], data['locale'], data['app_version'],
        data['create_date']
    ))
    conn.commit()
    cursor.close()


def connect_to_postgres():
    """
    connecting to the database using credentials - Ideally we don't want to expose passwords

    we are using the psycopg2 library in order to interact with the postgres database.

    Just for this sample example - we can use SQLAlchemy as well which is an ORM way 
    of querying a database i.e., you just write python code to interact with databases

    but as data gets evolved over time - It's always better to have stronger command
    over the things happening in database which we will get by using raw SQL queries.
    """
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'  # Ensure this matches your port
    )
    return conn

# Messages will be sent to SQS from producers and will be processed by consumers 
# Once processed they will be deleted from the Queue, If not - they will be written 
# back to Queue again  

# just Imagine the situation on an E-commerce ordering platform - whenever customers 
# order a new item - It will be added to the queue and will be processed by 
# people who will recieve and ship the orders. 

def wait_for_localstack():
    retries = 20
    for _ in range(retries):
        try:
            sqs_client = connect_to_sqs()
            sqs_client.list_queues()
            print("Localstack is ready.")
            return
        except Exception as e:
            print(f"Waiting for Localstack... ({e})")
            time.sleep(10)
    raise Exception("Localstack did not become ready in time.")


def fetch_messages():
    """
    Function to perform everything discussed till now - fetch the data from SQS, 
    do the necessary transformations and write the records into the database. 
    """

    wait_for_localstack()  # Ensure Localstack is ready
    sqs_client = connect_to_sqs()
    queue_url = 'http://localhost:4566/000000000000/login-queue'
    messages = receive_messages(sqs_client, queue_url)
    
    conn = connect_to_postgres()
    
    for message in messages:
        msg_body = json.loads(message['Body'])
        masked_msg = process_message(msg_body)
        insert_into_db(conn, masked_msg)
        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
    
    conn.close()

if __name__ == '__main__':
    fetch_messages()


# This whole application code will run using docker containerization techniques 
# You can run these same set of files any system without configurations issues 
# by just installing docker and using a single command. 