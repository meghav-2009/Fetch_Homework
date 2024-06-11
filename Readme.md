
# Fetch Rewards Data Engineer Take Home Exam

Folder Setup

- Main Folder : Fetch_Project

- Sub Folders : Dockerfile, docker-compose.yml, requirements.txt, fetch_messages.py 

Steps to Run the Application

1. Open command prompt and navigate till you get to the Fetch_Project folder. Now, You are inside the folder where you have access to code files.

2. The description of each of the code files is as follows 

- requirements.txt : Listing down required libraries for successful execution of code

- Dockerfile : More or less the initial setup : Installing dependencies, setting up the environment using python to run a python file at start and copying the application files to a directory in the container. 

- docker-compose.yml : To set up multiple containers for database, other services and manage all the required interdependencies, volumes. 

whenever someone runs docker compose up - Dockerfile gets executed, It starts the execution of fetch_messages.py which takes cares of all the necessary steps. 

- fetch_messages.py : python code to fetch data from SQS Queue in JSON format and then do the necessary transformations befor loading the data into the postgres database.

3. Run the command 'docker compose up --built' : This command sets up the containers, installs the requirements and then run the python file as well. You can see the status in the command prompt that It was executed successfully. 

## For In-detailed understanding of how things are happeing in the pipeline, please refer to the fetch_messages.py file

4. Now, In a new command prompt, run the command 'psql -d postgres -U postgres -p 5434 -h localhost -W' - It will ask for password, type in postgres

Now, you can access the postgres database, Just to verify the whole process, Run the Query SELECT * FROM user_logins; and verify the data being populated in the database.



# Questions

-- Few questions were answered in fetch_messages.py about the process of designing this ETL pipeline. 

## 1. How would you deploy this application in production?

- we use kubernetes for managinging the docker containers. In kubernetes we have deployments, which have a control of our docker containers and you also have nodes - master node is responsible for making sure all the deployments are running as excpected, handling any failures using etcd, snapshots and also to manage all the interdependecies, as in case of microservices architectures you have lots of nodes. 

- we setup kubernetes clusters by creating services and deployment files where you write YAML code for setting up the cluster configurations, replicas, specifications etc ... kubernetes automatically handles scaling up and down of application resources as required and we will use kubectl commands to monitor / handle the cluster and finally for deployment which end users can access using services, ingress.  



## 2. What other components would you want to add to make this production ready?

- first thing would to implement auto scaling policies in kubernetes so that It can handle various workloads using Horizontal Pod Autoscaler which does continuous monitoring to make it handles all the requests at a certain point of time. 

- Using ELK stack for logs analysis - which will help to monitor how it's working, to easily debug if in case we come across any issues and also using Prometheus and Grafana for metrics collection and visualization of how well our application is performing in real time which I will help us to get to know about how can we make it more convenient / efficient for end users. 

- One more thing is to consider the use of airflow, since the pipeline just consists of fe simple steps - It is fine to write all of it in one python file but as we get more columns / transformations that needs to be done, It's better to use different python files for each of them (maybe use PySpark) and then manage the exceution os all those tasks dependencies using Airflow, which has a very Good GUI for monitoring, viewing logs and graph visualizations just to get a proper visual representation of how things are taking place. It's also easier to cretae DAG's with in-built operators, which also go along well with connecting to AWS services.

- Few more things are probably to use Cloud database like RDS or Aurora in place of postgres for easy database scaling purposes and also implement more security measures like using AWS Secrets Manager, IAM roles / RBAC. 



## 3. How can this  application scale with a growing dataset 

- As just mentioned above, using RDS or Auurora might be an easier option as you don't have to do most of the things manually. 

- but, It we talk about using postgres itself - then it might be performace efficient to implement the concept of sharding, which is to distribute the data accross mutliple databases which eases out the load. Few important things that needs to be considered while perofmring sharding are defining strategies of efficient ways of distributing the data based on frequent queries etc to balance loads, seeting up the shard databases, modifying the application logic to route queries to corresponding shards based on the sharding key, periodically monitoring them and re-balancng shards as needed.

- Similarly, we can implement the auto-scaling feature in SQS to handle increasing no.of read / write messages to the Queue, and also we can implement the concept of batch processing instead of handling messages one by one which might be slightly inefficient as there's lot of over head - using kafka to handle batch processing might be a better way. 

- using Performance optimization techniques like indexing so that the amount of time take for queries will be significantly reduced which is an important factor when the data gets large and also using caching mechanisms like Redis so that you store frequently requested data in a temporary place to access it more frequently without querying on the entire database again. 



## 4. How can PII be recovered later on 

- Inorder to mask the PII data - It's better to use an encryption technique called AES. we can do hashing but we can't recover the original values back which were transformed using hashing. so, AES does encryption to IP, device_id using a set of mathematical operations along with secret key, IV pairs (store them securely using AWS KMS)

- we will use the same set of secret key, IV pairs for all the input values so that same inputs will be transformed in the exact similar manner to produce the same outputs (which is not possible in case of SHA 256 hashing) - so, using AES encryption technique will help us to find out duplicates as well

- Decryption is the process to get back the original values later on - we will make use of secret key, IV pairs and perfrom all the mathematical operations we did while encryption in AES in reverse order to get the original values

- so, use AES encrptions along with proper access controls / MFA of who could access these data / functions.



## 5. Assumptions I made 

- assumed that there are no duplicates as we have implemented strict constarints on the database (means thinking that SQS  will not recieve duplicate messages), aws services and security measures are replicated / handled by localstack and also - schema will not eveolve - It's a fixed schema.




