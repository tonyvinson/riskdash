import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.aws_control import (
    create_aws_control,
    create_aws_proj_control,
    get_aws_control,
    get_aws_control_by_id,
    update_aws_control_by_id,
    delete_aws_control_by_id,
)
from fedrisk_api.db.models import AWSControl, AWSControlProjectControl

from fedrisk_api.schema.aws_control import (
    UpdateAWSControl,
)


# Test create_aws_control
def test_create_aws_control():
    db = MagicMock(spec=Session)  # Mock the Session
    aws_control_data = {
        "aws_id": "123",
        "aws_title": "Test Control",
        "aws_control_status": "Active",
        "aws_severity": "High",
    }

    create_aws_control_instance = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    result = create_aws_control(create_aws_control_instance, db)

    db.add.assert_called_once()
    db.commit.assert_called_once()
    # assert result == create_aws_control_instance


# Test get_aws_control
def test_get_aws_control():
    db = MagicMock(spec=Session)
    tenant_id = 1
    mock_query_result = [MagicMock(spec=AWSControl)]
    db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_query_result

    result = get_aws_control(db, tenant_id)

    # assert result == mock_query_result
    db.query.assert_called_once()


# Test update_aws_control_by_id
# def test_update_aws_control_by_id():
#     db = MagicMock(spec=Session)
#     # aws_control_update = MagicMock()
#     aws_control_update = UpdateAWSControl(
#         aws_id=1,
#         aws_title="test",
#     )
#     aws_control_id = 1
#     tenant_id = 1

#     queryset_mock = db.query().filter().filter().first.return_value = MagicMock()

#     result = update_aws_control_by_id(aws_control_update, db, aws_control_id, tenant_id)

#     # assert result is True
#     db.commit.assert_called_once()

#     # If no record is found
#     db.query().filter().filter().first.return_value = None
#     result = update_aws_control_by_id(aws_control_update, db, aws_control_id, tenant_id)

#     # assert result is False


# Test delete_aws_control_by_id
def test_delete_aws_control_by_id():
    db = MagicMock(spec=Session)
    aws_control_id = 1
    mock_aws_control = MagicMock(spec=AWSControl)
    db.query().filter().first.return_value = mock_aws_control

    result = delete_aws_control_by_id(db, aws_control_id)

    assert result is True
    db.commit.assert_called_once()

    # If no record is found
    db.query().filter().first.return_value = None
    result = delete_aws_control_by_id(db, aws_control_id)

    assert result is False
