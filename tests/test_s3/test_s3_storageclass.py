from __future__ import unicode_literals

import boto3

import sure  # noqa
from botocore.exceptions import ClientError
from nose.tools import assert_raises

from moto import mock_s3


@mock_s3
def test_s3_storage_class_standard():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")

    # add an object to the bucket with standard storage

    s3.put_object(Bucket="Bucket", Key="my_key", Body="my_value")

    list_of_objects = s3.list_objects(Bucket="Bucket")

    list_of_objects["Contents"][0]["StorageClass"].should.equal("STANDARD")


@mock_s3
def test_s3_storage_class_infrequent_access():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")

    # add an object to the bucket with standard storage

    s3.put_object(
        Bucket="Bucket",
        Key="my_key_infrequent",
        Body="my_value_infrequent",
        StorageClass="STANDARD_IA",
    )

    D = s3.list_objects(Bucket="Bucket")

    D["Contents"][0]["StorageClass"].should.equal("STANDARD_IA")


@mock_s3
def test_s3_storage_class_intelligent_tiering():
    s3 = boto3.client("s3")

    s3.create_bucket(Bucket="Bucket")
    s3.put_object(
        Bucket="Bucket",
        Key="my_key_infrequent",
        Body="my_value_infrequent",
        StorageClass="INTELLIGENT_TIERING",
    )

    objects = s3.list_objects(Bucket="Bucket")

    objects["Contents"][0]["StorageClass"].should.equal("INTELLIGENT_TIERING")


@mock_s3
def test_s3_storage_class_copy():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")
    s3.put_object(
        Bucket="Bucket", Key="First_Object", Body="Body", StorageClass="STANDARD"
    )

    s3.create_bucket(Bucket="Bucket2")
    # second object is originally of storage class REDUCED_REDUNDANCY
    s3.put_object(Bucket="Bucket2", Key="Second_Object", Body="Body2")

    s3.copy_object(
        CopySource={"Bucket": "Bucket", "Key": "First_Object"},
        Bucket="Bucket2",
        Key="Second_Object",
        StorageClass="ONEZONE_IA",
    )

    list_of_copied_objects = s3.list_objects(Bucket="Bucket2")

    # checks that a copied object can be properly copied
    list_of_copied_objects["Contents"][0]["StorageClass"].should.equal("ONEZONE_IA")


@mock_s3
def test_s3_invalid_copied_storage_class():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")
    s3.put_object(
        Bucket="Bucket", Key="First_Object", Body="Body", StorageClass="STANDARD"
    )

    s3.create_bucket(Bucket="Bucket2")
    s3.put_object(
        Bucket="Bucket2",
        Key="Second_Object",
        Body="Body2",
        StorageClass="REDUCED_REDUNDANCY",
    )

    # Try to copy an object with an invalid storage class
    with assert_raises(ClientError) as err:
        s3.copy_object(
            CopySource={"Bucket": "Bucket", "Key": "First_Object"},
            Bucket="Bucket2",
            Key="Second_Object",
            StorageClass="STANDARD2",
        )

    e = err.exception
    e.response["Error"]["Code"].should.equal("InvalidStorageClass")
    e.response["Error"]["Message"].should.equal(
        "The storage class you specified is not valid"
    )


@mock_s3
def test_s3_invalid_storage_class():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")

    # Try to add an object with an invalid storage class
    with assert_raises(ClientError) as err:
        s3.put_object(
            Bucket="Bucket", Key="First_Object", Body="Body", StorageClass="STANDARDD"
        )

    e = err.exception
    e.response["Error"]["Code"].should.equal("InvalidStorageClass")
    e.response["Error"]["Message"].should.equal(
        "The storage class you specified is not valid"
    )


@mock_s3
def test_s3_default_storage_class():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")

    s3.put_object(Bucket="Bucket", Key="First_Object", Body="Body")

    list_of_objects = s3.list_objects(Bucket="Bucket")

    # tests that the default storage class is still STANDARD
    list_of_objects["Contents"][0]["StorageClass"].should.equal("STANDARD")


@mock_s3
def test_s3_copy_object_error_for_glacier_storage_class():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")

    s3.put_object(
        Bucket="Bucket", Key="First_Object", Body="Body", StorageClass="GLACIER"
    )

    with assert_raises(ClientError) as exc:
        s3.copy_object(
            CopySource={"Bucket": "Bucket", "Key": "First_Object"},
            Bucket="Bucket",
            Key="Second_Object",
        )

    exc.exception.response["Error"]["Code"].should.equal("ObjectNotInActiveTierError")


@mock_s3
def test_s3_copy_object_error_for_deep_archive_storage_class():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="Bucket")

    s3.put_object(
        Bucket="Bucket", Key="First_Object", Body="Body", StorageClass="DEEP_ARCHIVE"
    )

    with assert_raises(ClientError) as exc:
        s3.copy_object(
            CopySource={"Bucket": "Bucket", "Key": "First_Object"},
            Bucket="Bucket",
            Key="Second_Object",
        )

    exc.exception.response["Error"]["Code"].should.equal("ObjectNotInActiveTierError")
