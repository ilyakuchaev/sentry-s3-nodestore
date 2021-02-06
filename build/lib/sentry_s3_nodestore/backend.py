"""
sentry_s3_nodestore.backend
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2015 by Ernest W. Durbin III.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import simplejson
from base64 import urlsafe_b64encode
from time import sleep
from uuid import uuid4
import zlib

import boto3

from sentry.nodestore.base import NodeStorage


def retry(attempts, func, *args, **kwargs):
    for _ in range(attempts):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            sleep(0.1)
            raise
    raise

SENTRY_NODESTORE_OPTIONS = {
    'bucket_name': 'sentry-nodestore-13e15550-9a2e-4910-98c5-b0cc76c60f04',
    'region': 'us-west-1',
    'endpoint':'https://s3.royalroad.com',
    'aws_access_key_id': '***REMOVED***',
    'aws_secret_access_key': '***REMOVED***'
}

class S3NodeStorage(NodeStorage):

    def __init__(self, bucket_name=None, endpoint=None, region='eu-west-1', aws_access_key_id=None, aws_secret_access_key=None, max_retries=3):
        self.max_retries = max_retries
        self.bucket_name = bucket_name
        self.client = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key)

    def delete(self, id):
        """
        >>> nodestore.delete('key1')
        """
        self.client.delete_object(Bucket=self.bucket_name, Key=id)

    def delete_multi(self, id_list):
        """
        Delete multiple nodes.

        Note: This is not guaranteed to be atomic and may result in a partial
        delete.

        >>> delete_multi(['key1', 'key2'])
        """
        self.client.delete_objects(Bucket=self.bucket_name, Delete={
            'Objects': [{'Key': id} for id in id_list]
        })

    def _get_bytes(self, id):
        """
        >>> nodestore._get_bytes('key1')
        b'{"message": "hello world"}'
        """
        result = retry(self.max_retries, self.client.get_object, Bucket=self.bucket_name, Key=id)
        return zlib.decompress(result['Body'].read())

    def _set_bytes(self, id, data, ttl=None):
        """
        >>> nodestore.set('key1', b"{'foo': 'bar'}")
        """
        retry(self.max_retries, self.client.put_object, Body=zlib.compress(data), Bucket=self.bucket_name, Key=id)

    def generate_id(self):
        return urlsafe_b64encode(uuid4().bytes)