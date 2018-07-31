import boto3
import json
import traceback
import os
import logging, sys
import tarfile

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Get the service resource
sqs = boto3.resource('sqs', region_name='eu-central-1')
s3_client = boto3.client('s3', region_name='eu-central-1')

# Get the queue
queue = sqs.get_queue_by_name(QueueName='Your SQS Queue Name')

for message in queue.receive_messages(MaxNumberOfMessages=10):
  try:
    if message is not None:
      # Parsing event message from s3 bucket
      s3 = json.loads(message.body)['Records'][0]['s3']
      bucket = s3['bucket']['name']
      key = s3['object']['key']
      
      logging.debug('bucket :'+bucket)
      logging.debug('key :'+key)
      
      # Get filename and directory from key
      filename = os.path.basename(key)
      directory = '/your_prefix_dir/' + os.path.dirname(key)
      
      logging.debug('filename :'+filename)
      logging.debug('directory :'+directory)
      
      # Create Directory if it is not exist
      if not os.path.exists(directory):
          os.makedirs(directory)  
                          
      # Download Log File
      s3_client.download_file(bucket, key, directory + filename)
      logging.debug('Download completed')
      
      # Extract tar.gz File
      tar = tarfile.open(directory + filename, "r:gz")
      tar.extractall(directory)
      tar.close()  
      logging.debug('extract file completed')
         
      # Remove tar.gz File
      os.remove(directory + filename)
      
      # Remove SQS message    
      message.delete()
      
  except ValueError:
    # SQS is dedicated for S3 event message. If there is wrong message from other service, leave message body and remove the message
    logging.error('Message format is not valid. Delete message :' + message.body)
    message.delete()
  except Exception:
    logging.error(traceback.format_exc()) 
  else:
    logging.info('finish')