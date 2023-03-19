import pytest
import types
import upsolver.dbapi as upsolver
from upsolver.client.exceptions import InterfaceError, OperationalError,DatabaseError

SELECT_COMMAND = "SELECT * FROM orders_transformed_data LIMIT 6;"
SELECT_RESPONSE = {
    'columns': [
        {'name': 'order_id', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': 'customer_id', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': 'customer_name', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': 'total', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': 'partition_date', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': '$shard_number', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': '$source_id', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': '$commit_time', 'columnType': {'clazz': 'StringColumnType'}},
        {'name': '$event_time', 'columnType': {'clazz': 'StringColumnType'}}
    ],
    'data': [
        ['ZCqes8quqd', 'd4f2de89a2c83b8f20bfc32938da8064', 'Catherine Rivera', '291.86', '2023-01-30', '0',
         '58e40edf-e663-4f37-9f8a-d9097424f61e', '2023-01-30 21:23:00.000', '2023-01-30 20:50:00.000'],
        ['wiOqu4jqf3', 'e121e550fb10d350c5d4f13a5c503b10', 'Kayla Jimenez', '1255.04', '2023-01-30', '0',
         '58e40edf-e663-4f37-9f8a-d9097424f61e', '2023-01-30 21:23:00.000', '2023-01-30 20:50:00.000'],
        ['ItSyMIOaVG', 'cc267b0fbc93616d919d2981082e83c7', 'Logan Bennet', '1361.77', '2023-01-30', '0',
         '58e40edf-e663-4f37-9f8a-d9097424f61e', '2023-01-30 21:23:00.000', '2023-01-30 20:50:00.000'],
        ['443MXyQR6B', '5a3b45ab0bf89290b57ee03a2c7b5b54', 'Kelly Edwards', '343.6', '2023-01-30', '0',
         '58e40edf-e663-4f37-9f8a-d9097424f61e', '2023-01-30 21:23:00.000', '2023-01-30 20:50:00.000'],
        ['hGd89jCQQG', 'a5436c62216c404040f72d300a4a2f89', 'Charles Martinez', '2546.66', '2023-01-30', '0',
         '58e40edf-e663-4f37-9f8a-d9097424f61e', '2023-01-30 21:23:00.000', '2023-01-30 20:50:00.000'],
        ['eXWJu43yKd', '7e73134ffe802b9477f8bd5ed07d28e4', 'Bobby Ross', '1791.24', '2023-01-30', '0',
         '58e40edf-e663-4f37-9f8a-d9097424f61e', '2023-01-30 21:23:00.000', '2023-01-30 20:50:00.000']
    ],
    'has_next_page': False
}


def test_execute_manipulation(mocker):
    def mock_execute(self, query, timeout_sec):
        yield {'message': 'Connection created successfully'}

    mocker.patch('upsolver.client.query.RestQueryApi.execute', mock_execute)

    conn = upsolver.connection.connect(None, None)
    cursor = conn.cursor()

    create_result = list(cursor.execute(''))
    assert len(create_result) == 1
    assert create_result[0] == 'Connection created successfully'


def test_execute_select(mocker):
    def mock_execute(self, query, timeout_sec):
        yield SELECT_RESPONSE

    mocker.patch('upsolver.client.query.RestQueryApi.execute', mock_execute)

    conn = upsolver.connect(None, None)
    cursor = conn.cursor()
    select_result = cursor.execute(SELECT_COMMAND)

    assert isinstance(select_result, types.GeneratorType)
    assert sum(1 for _ in select_result) == len(SELECT_RESPONSE['data'])
    assert cursor.rowcount == len(SELECT_RESPONSE['data'])
    for res_column, check_column in zip(cursor.description, SELECT_RESPONSE['columns']):
        assert res_column[0] == check_column['name']
        assert res_column[1] == upsolver.STRING


def test_fetching_after_select(mocker):
    def mock_execute(self, query, timeout_sec):
        yield SELECT_RESPONSE

    mocker.patch('upsolver.client.query.RestQueryApi.execute', mock_execute)

    conn = upsolver.connect(None, None)
    cursor = conn.cursor()
    cursor.execute(SELECT_COMMAND)

    one_result = cursor.fetchone()
    assert one_result == SELECT_RESPONSE['data'][0]

    cursor.arraysize = 3
    many_result = cursor.fetchmany()
    assert isinstance(many_result, list)
    assert len(many_result) == cursor.arraysize
    for res_data, check_data in zip(many_result, SELECT_RESPONSE['data'][1: 1 + cursor.arraysize]):
        assert res_data == check_data

    all_result = cursor.fetchall()
    assert isinstance(all_result, list)
    assert len(all_result) == len(SELECT_RESPONSE['data']) - cursor.arraysize - 1
    for res_data, check_data in zip(all_result, SELECT_RESPONSE['data'][1 + cursor.arraysize:]):
        assert res_data == check_data

    one_empty_result = cursor.fetchone()
    assert one_empty_result is None

    many_empty_result = cursor.fetchmany()
    assert isinstance(many_empty_result, list)
    assert len(many_empty_result) == 0

    all_empty_result = cursor.fetchall()
    assert isinstance(all_empty_result, list)
    assert len(all_empty_result) == 0


def test_closed_cursor():
    conn = upsolver.connect(None, None)
    cursor = conn.cursor()
    cursor.close()

    with pytest.raises(InterfaceError):
        cursor.execute(SELECT_COMMAND)


def test_closed_connection():
    conn = upsolver.connect(None, None)
    conn.close()

    with pytest.raises(InterfaceError):
        conn.cursor()


def test_wrong_command(mocker):
    mocker.patch('upsolver.client.query.RestQueryApi.execute', side_effect=OperationalError)

    conn = upsolver.connect(None, None)
    cursor = conn.cursor()

    with pytest.raises(OperationalError):
        cursor.execute(SELECT_COMMAND)


def test_missing_credentials():
    conn = upsolver.connect(None, None)
    cursor = conn.cursor()

    with pytest.raises(DatabaseError):
        cursor.execute(SELECT_COMMAND)
