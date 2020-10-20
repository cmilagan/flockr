from json import dumps
import pytest
import re
from subprocess import Popen, PIPE
import signal
from time import sleep
import requests
import json

from error import InputError, AccessError

def register_default_user(url, name_first, name_last):
    email = f'{name_first.lower()}{name_last.lower()}@gmail.com'
    data = {
        'email': email,
        'password': 'password',
        'name_first': name_first,
        'name_last': name_last
    }
    payload = requests.post(f'{url}auth/register', json=data)
    return payload.json()

@pytest.fixture
def user_1(url):
    requests.delete(f'{url}clear')
    return register_default_user(url, 'John', 'Smith')


@pytest.fixture
def user_2(url):
    return register_default_user(url, 'Jane', 'Smith')
    
@pytest.fixture
def user_3(url):
    return register_default_user(url, 'Jace', 'Smith')
    
@pytest.fixture
def user_4(url):
    return register_default_user(url, 'Janice', 'Smith')


@pytest.fixture
def default_channel(url, user_1):
    return requests.post(f'{url}/channels/create', json={
        'token': user_1['token'],
        'name': 'Group 1',
        'is_public': True,
    }).json()


# Use this fixture to get the URL of the server. It starts the server for you,
# so you don't need to.
@pytest.fixture
def url():
    url_re = re.compile(r' \* Running on ([^ ]*)')
    server = Popen(["python3", "src/server.py"], stderr=PIPE, stdout=PIPE)
    line = server.stderr.readline()
    local_url = url_re.match(line.decode())
    if local_url:
        yield local_url.group(1)
        # Terminate the server
        server.send_signal(signal.SIGINT)
        waited = 0
        while server.poll() is None and waited < 5:
            sleep(0.1)
            waited += 0.1
        if server.poll() is None:
            server.kill()
    else:
        server.kill()
        raise Exception("Couldn't get URL from local server")

# Example testing from echo_http_test.py
# def test_echo(url):
#     '''
#     A simple test to check echo
#     '''
#     resp = requests.get(url + 'echo', params={'data': 'hello'})
#     assert json.loads(resp.text) == {'data': 'hello'}

#------------------------------------------------------------------------------#
#                               channel/invite                                 #
#------------------------------------------------------------------------------#

#?-------------------------- Input/Access Error Testing ----------------------?#

def test_channel_invite_login_user_HTTP(url, user_1, user_2, user_3, user_4, default_channel):
    """Testing invalid token for users which have logged out
    """
    log_out = requests.post(f'{url}/auth/logout', json={'token': user_1['token']}).json()
    assert log_out['is_success'] == True
    log_out = requests.post(f'{url}/auth/logout', json={'token': user_2['token']}).json()
    assert log_out['is_success'] == True
    log_out = requests.post(f'{url}/auth/logout', json={'token': user_3['token']}).json()
    assert log_out['is_success'] == True
    log_out = requests.post(f'{url}/auth/logout', json={'token': user_4['token']}).json()
    assert log_out['is_success'] == True

    # with pytest.raises(AccessError):
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : user_3['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : user_4['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code
    requests.delete(f'{url}/clear')

def test_channel_invite_wrong_data_type_HTTP(url, user_1, default_channel):
    """Testing when wrong data types are used as input
    """
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : -1,
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : '@#$!',
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : 67.666,
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code
    requests.delete(f'{url}/clear')

def test_channel_invite_invalid_user_HTTP(url, user_1, default_channel):
    """Testing when invalid user is invited to channel
    """
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_1['u_id'] + 1,
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_1['u_id'] - 1,
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code
    requests.delete(f'{url}/clear')

def test_channel_invite_invalid_channel_HTTP(url, user_1, user_2):
    """Testing when valid user is invited to invalid channel
    """
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': -122,
        'u_id'      : user_2['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': -642,
        'u_id'      : user_2['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': '@#@!',
        'u_id'      : user_2['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': 212.11,
        'u_id'      : user_2['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code
    requests.delete(f'{url}/clear')

def test_channel_invite_not_authorized_HTTP(url, user_1, user_2, user_3):
    """Testing when user is not authorized to invite other users to channel
    (Assumption) This includes an invalid user inviting users to channel
    """
    channel_profile = {
        'token'    : user_3['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    default_channel = requests.post(f'{url}/channels/create', json=channel_profile).json()
    log_out = requests.post(f'{url}/auth/logout', json={'token': user_1['token']}).json()
    assert log_out['is_success'] == True

    invite_details = {
        'token'     : 12,
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : -12,
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : 121.11,
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_1['token'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['token'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['token'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == AccessError.code
    requests.delete(f'{url}/clear')

def test_channel_invite_invalid_self_invite_HTTP(url, user_1, default_channel):
    """Testing when user is not allowed to invite him/herself to channel
    (Assumption testing) this error will be treated as InputError
    """
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code
    requests.delete(f'{url}/clear')

def test_channel_multiple_invite_HTTP(url, user_1, user_2, default_channel):
    """Testing when user invites a user multiple times
    (Assumption testing) this error will be treated as AccessError
    """
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    error = requests.post(f'{url}/channel/invite', json=invite_details)
    error.status_code == InputError.code
    requests.delete(f'{url}/clear')

#?------------------------------ Output Testing ------------------------------?#

def test_channel_invite_successful_HTTP(url, user_1, user_2, user_3, user_4, default_channel):
    """Testing if user has successfully been invited to the channel
    """
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
        ],
    }

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
            {
                'u_id': user_3['u_id'],
                'name_first': 'Jace',
                'name_last': 'Smith',
            },
        ],
    }

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_4['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()    
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
            {
                'u_id': user_3['u_id'],
                'name_first': 'Jace',
                'name_last': 'Smith',
            },
            {
                'u_id': user_4['u_id'],
                'name_first': 'Janice',
                'name_last': 'Smith',
            },
        ],
    }
    requests.delete(f'{url}/clear')

def test_channel_invite_flockr_user_HTTP(url, user_1, user_2, user_3):
    """(Assumption testing) first person to register is flockr owner
    Testing if flockr owner has been successfully invited to channel and given ownership
    """
    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    default_channel = requests.post(f'{url}/channels/create', json=channel_profile).json()

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
            {
                'u_id': user_3['u_id'],
                'name_first': 'Jace',
                'name_last': 'Smith',
            },
        ],
    }

    invite_details = {
        'token'     : user_3['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
            {
                'u_id': user_3['u_id'],
                'name_first': 'Jace',
                'name_last': 'Smith',
            },
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
    }
    requests.delete(f'{url}/clear')

#------------------------------------------------------------------------------#
#                               channel/details                                #
#------------------------------------------------------------------------------#

#?-------------------------- Input/Access Error Testing ----------------------?#

def test_channel_details_invalid_channel_HTTP(url, user_1):
    """Testing if channel is invalid or does not exist
    """
    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': -1,
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == InputError.code

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': -19,
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == InputError.code

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': '#@&!',
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == InputError.code

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': 121.12,
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == InputError.code
    requests.delete(f'{url}/clear')

def test_channel_details_invalid_user_HTTP(url, user_1, user_2, default_channel):
    """Testing if unauthorized/invalid user is unable to access channel details
    """    
    channel_profile = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == AccessError.code
    requests.delete(f'{url}/clear')

def test_channel_details_invalid_token_HTTP(url, user_1, default_channel):
    """Testing if given invalid token returns an AccessError
    """
    channel_profile = {
        'token'     : 6.333,
        'channel_id': 0,
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == AccessError.code

    channel_profile = {
        'token'     : '@^!&',
        'channel_id': -3,
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == AccessError.code

    channel_profile = {
        'token'     : -1,
        'channel_id': default_channel['channel_id'],
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == AccessError.code

    channel_profile = {
        'token'     : 'abcd',
        'channel_id': default_channel['channel_id'],
    }
    error = requests.get(f'{url}/channel/details', params=channel_profile)
    error.status_code == AccessError.code
    requests.delete(f'{url}/clear')

#?------------------------------ Output Testing ------------------------------?#

def test_channel_details_authorized_user_HTTP(url, user_1, user_2, user_3, user_4, default_channel):
    """Testing the required correct details of a channel
    """
    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
        ],
    }

    invite_details = {
        'token'     : user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_3['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}
    
    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
            {
                'u_id': user_3['u_id'],
                'name_first': 'Jace',
                'name_last': 'Smith',
            },
        ],
    }

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_4['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()    
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
            {
                'u_id': user_3['u_id'],
                'name_first': 'Jace',
                'name_last': 'Smith',
            },
            {
                'u_id': user_4['u_id'],
                'name_first': 'Janice',
                'name_last': 'Smith',
            },
        ],
    }
    requests.delete(f'{url}/clear')

def test_output_details_twice_HTTP(url, user_1, user_2, default_channel):
    """Test if details will be shown when a second channel is created.
    """
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 2',
        'is_public': True,
    }
    default_channel_2 = requests.post(f'{url}/channels/create', json=channel_profile).json()

    invite_details = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    channel_return = requests.post(f'{url}/channel/invite', json=invite_details).json()
    assert channel_return == {}

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel_2['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 2',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
    }

    channel_profile = {
        'token'     : user_1['token'],
        'channel_id': default_channel['channel_id'],
    }
    channel_information = requests.get(f'{url}/channel/details', params=channel_profile).json()
    assert channel_information == {
        'name': 'Group 1',
        'owner_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
        ],
        'all_members': [
            {
                'u_id': user_1['u_id'],
                'name_first': 'John',
                'name_last': 'Smith',
            },
            {
                'u_id': user_2['u_id'],
                'name_first': 'Jane',
                'name_last': 'Smith',
            },
        ],
    }
    requests.delete(f'{url}/clear')

# ------------------------------------------------------------------------------#
#                               channel/messages                               #
# ------------------------------------------------------------------------------#

# ?-------------------------- Input/Access Error Testing ----------------------?#


# ?------------------------------ Output Testing ------------------------------?#



# ------------------------------------------------------------------------------#
#                               channel/leave                                  #
# ------------------------------------------------------------------------------#

#?-------------------------- Input/Access Error Testing ----------------------?#

def test_input_leave_channel_id(url, user_1):
    """Testing when an invalid channel_id is used as a parameter
    """
    payload = requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'], 
        'channel_id': -1
    })
    assert payload.status_code == InputError.code

    payload = requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'], 
        'channel_id': 0
    })
    assert payload.status_code == InputError.code

    payload = requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'], 
        'channel_id': 1
    })
    assert payload.status_code == InputError.code

    requests.delete(f'{url}/clear')

def test_access_leave_user_is_member(url, user_1, user_2):
    """Testing if a user was not in the channel initially
    """
    channel_data_1 = requests.post(f'{url}/channels/create', json={
        'token': user_1['token'],
        'name': 'Group 1',
        'is_public': True,
    }).json()

    channel_data_2 = requests.post(f'{url}/channels/create', json={
        'token': user_2['token'],
        'name': 'Group 1',
        'is_public': True,
    }).json()

    payload = requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': channel_data_2['channel_id']
    })
    assert payload.status_code == AccessError.code

    payload = requests.post(f'{url}/channel/leave', json={
        'token': user_2['token'], 
        'channel_id': channel_data_1['channel_id']
    })
    assert payload.status_code == AccessError.code

    requests.delete(f'{url}/clear')


def test_access_leave_valid_token(url, user_1, default_channel):
    """Testing if token is valid
    """
    requests.post(f'{url}/auth/logout', json={'token': user_1['token']})

    payload = requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    })
    assert payload.status_code == AccessError.code

    requests.delete(f'{url}/clear')


#?------------------------------ Output Testing ------------------------------?#

def test_output_user_leave_public(url, user_1, default_channel):
    """Testing if the user has successfully left a public channel
    """
    requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    })

    payload = requests.get(f'{url}/channels/list', params={'token': user_1['token']}).json()
    assert payload['channels'] == []
    requests.delete(f'{url}/clear')

def test_output_user_leave_private(url, user_1, default_channel):
    """Testing if the user has successfully left a private channel
    """
    requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    })

    payload = requests.get(f'{url}/channels/list', params={'token': user_1['token']}).json()
    assert payload['channels'] == []
    requests.delete(f'{url}/clear')


def test_output_user_leave_channels(url, user_1, default_channel):
    """Testing if user has left the correct channel and that channel is no longer
    on the user's own channel list
    """
    requests.post(f'{url}/channels/create', json={
        'token': user_1['token'],
        'name': 'Group 2',
        'is_public': False,
    })
    channel_3 = requests.post(f'{url}/channels/create', json={
        'token': user_1['token'],
        'name': 'Group 3',
        'is_public': False,
    }).json()
    requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': channel_3['channel_id']
    })

    payload = requests.get(f'{url}/channels/list', params={'token': user_1['token']}).json()
    leave_channel = {
        'channel_id': channel_3['channel_id'],
        'name': 'Group 3',
    }
    assert leave_channel not in payload['channels']
    requests.delete(f'{url}/clear')

def test_output_leave_channels(url, user_1, user_2):
    """Testing when user leaves multiple channels
    """
    channel_leave_1 = requests.post(f'{url}/channels/create', json={
        'token': user_1['token'],
        'name': 'Group 1',
        'is_public': False,
    }).json()
    requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': channel_leave_1['channel_id']
    })

    channel_leave_2 = requests.post(f'{url}/channels/create', json={
        'token': user_2['token'],
        'name': 'Group 1',
        'is_public': False,
    }).json()
    requests.post(f'{url}/channel/addowner', json={
        'token': user_2['token'], 
        'channel_id': channel_leave_2['channel_id'],
        'u_id': user_1['u_id']
    })

    requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': channel_leave_1['channel_id']
    })

    payload = requests.get(f'{url}/channels/list', params={'token': user_1['token']}).json()
    assert payload['channels'] == []
    requests.delete(f'{url}/clear')

def test_output_member_leave(url, user_1, user_2, user_3, default_channel):
    """Testing when a member leaves that it does not delete the channel. Covers 
    also if user infomation has been erased on channel's end.
    """
    requests.post(f'{url}/channel/invite', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id': user_2['u_id'],
    })
    requests.post(f'{url}/channel/invite', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id': user_3['u_id'],
    })
    requests.post(f'{url}/channel/leave', json={
        'token': user_3['token'],
        'channel_id': default_channel['channel_id']
    })

    payload = requests.get(f'{url}channel/details', params={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    }).json()
    for member in payload['all_members']:
        assert member['u_id'] != user_3['u_id']
    requests.delete(f'{url}/clear')

def test_output_all_members_leave(url, user_1, user_2, default_channel):
    """Test if the channel is deleted when all members leave
    """
    requests.post(f'{url}/channel/invite', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id': user_2['u_id'],
    })
    
    requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    })

    requests.post(f'{url}/channel/leave', json={
        'token': user_2['token'],
        'channel_id': default_channel['channel_id']
    })

    payload = requests.get(f'{url}/channels/listall', params={
        'token': user_1['token'],
    }).json()

    for curr_channel in payload['channels']:
        assert curr_channel['channel_id'] != default_channel['channel_id']

    requests.delete(f'{url}/clear')

def test_output_flockr_rejoin_channel(url, user_1, user_2, default_channel):
    """Test when the flockr owner leaves and comes back that the user status is an
    owner.
    """

    requests.post(f'{url}/channel/invite', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id'],
        'u_id': user_2['u_id'],
    })
    
    requests.post(f'{url}/channel/leave', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    })

    requests.post(f'{url}/channel/join', json={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    })

    payload = requests.get(f'{url}/channel/details', params={
        'token': user_1['token'],
        'channel_id': default_channel['channel_id']
    }).json()

    user_1_details = {'u_id': user_1['u_id'], 'name_first': 'John', 'name_last': 'Smith'}
    assert user_1_details in payload['owner_members']
    assert user_1_details in payload['all_members']

    requests.delete(f'{url}/clear')

def test_output_creator_rejoin_channel(url, user_1, user_2, user_3, default_channel):
    """Test when the the creator leaves and comes back that the user status is a member.
    """

    requests.post(f'{url}/channel/invite', json={
        'token': user_2['token'],
        'channel_id': default_channel['channel_id'],
        'u_id': user_3['u_id'],
    })
    
    requests.post(f'{url}/channel/leave', json={
        'token': user_2['token'],
        'channel_id': default_channel['channel_id']
    })

    requests.post(f'{url}/channel/join', json={
        'token': user_2['token'],
        'channel_id': default_channel['channel_id']
    })

    payload = requests.get(f'{url}/channel/details', params={
        'token': user_2['token'],
        'channel_id': default_channel['channel_id']
    }).json()
    user_2_details = {'u_id': user_2['u_id'], 'name_first': 'Jane', 'name_last': 'Smith'}
    assert user_2_details not in payload['owner_members']
    assert user_2_details in payload['all_members']

    requests.delete(f'{url}/clear')
    
#------------------------------------------------------------------------------#
#                                   channel_join                               #
#------------------------------------------------------------------------------#

#?------------------------- Input/Access Error Testing -----------------------?#

def test_input_join_channel_id(url):
    """Testing when Channel ID is not a valid channel
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    arg_join = {
        'token'     : user_1['token'],
        'channel_id': -1,
    }
    res_err = requests.post(url + 'channel/join', json=arg_join)
    res_err.status_code == InputError.code

    arg_join = {
        'token'     : user_1['token'],
        'channel_id': 0,
    }
    res_err = requests.post(url + 'channel/join', json=arg_join)
    res_err.status_code == InputError.code

    arg_join = {
        'token'     : user_1['token'],
        'channel_id': 5,
    }
    res_err = requests.post(url + 'channel/join', json=arg_join)
    res_err.status_code == InputError.code

    arg_join = {
        'token'     : user_1['token'],
        'channel_id': 1,
    }
    res_err = requests.post(url + 'channel/join', json=arg_join)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_access_join_valid_token(url):
    """Testing if token is valid
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    new_channel = requests.post(url + 'channels/create', json=channel_profile).json()

    log_out = requests.post(url + 'auth/logout', json={'token': user_1['token']}).json()
    assert log_out['is_success']

    arg_join = {
        'token'     : user_1['token'],
        'channel_id': new_channel['channel_id'],
    }
    res_err = requests.post(url + 'channel/join', json=arg_join)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_access_join_user_is_member(url):
    """Testing if channel_id refers to a channel that is private (when the
    authorised user is not a global owner)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'jonesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jone',
        'name_last' : 'Smith',
    }
    user_3 = requests.post(url + 'auth/register', json=user_profile).json()

    # Channel is private
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Group 2',
        'is_public': False,
    }
    new_channel_2 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_join = {
        'token'     : user_3['token'],
        'channel_id': new_channel_2['channel_id'],
    }
    res_err = requests.post(url + 'channel/join', json=arg_join)
    res_err.status_code == AccessError.code

    arg_join = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    res_err = requests.post(url + 'channel/join', json=arg_join)
    res_err.status_code == AccessError.code
    requests.delete(url + '/clear')
    

#?------------------------------ Output Testing ------------------------------?#

def test_output_user_join_public(url):
    """Testing if the user has successfully joined a public channel
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a public channel and join user_2
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_join = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    requests.post(url + 'channel/join', json=arg_join).json()

    # Check channel details if the user is a member
    arg_details = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    in_channel = False
    for member in channel_data['all_members']:
        if member['u_id'] is user_2['u_id']:
            in_channel = True
            break
    assert in_channel

    # Check if channel appears in the user's channels list
    arg_list = {
        'token'     : user_2['token'],
    }
    channel_user_list = requests.get(url + 'channels/list', params=arg_list).json()
    assert len(channel_user_list) == 1
    requests.delete(url + '/clear')
    

def test_output_user_join_flockr_private(url):
    """Test for flockr owner (flockr owner can join private channels)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a private channel and check if flockr owner
    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Private Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    # Assume that the first user is the flockr owner
    arg_join = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    requests.post(url + 'channel/join', json=arg_join).json()

    arg_list = {
        'token'     : user_2['token'],
    }
    channel_list = requests.get(url + 'channels/list', params=arg_list).json()

    # Check if flockr owner is in channel list
    in_channel = False
    for curr_channel in channel_list['channels']:
        if curr_channel['channel_id'] == new_channel_1['channel_id']:
            in_channel = True
            break
    assert in_channel
    requests.delete(url + '/clear')
    

def test_output_user_join_flockr_member_list(url):
    """Test for flockr owner (flockr owner can join private channels)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a private channel and check if flockr owner
    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Private Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    # Assume that the first user is the flockr owner
    arg_join = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    requests.post(url + 'channel/join', json=arg_join).json()

    # Check if flockr owner is a channel member
    arg_details = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    is_member = False
    for member in channel_data['all_members']:
        if member['u_id'] == user_1['u_id']:
            is_member = True
            break
    assert is_member
    requests.delete(url + '/clear')
    

def test_output_user_join_flockr_owner_list(url):
    """Test for flockr owner (flockr owner can join private channels)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a private channel and check if flockr owner
    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Private Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    # Assume that the first user is the flockr owner
    arg_join = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    requests.post(url + 'channel/join', json=arg_join).json()

    # Flockr owner becomes owner after channel join
    owner = True
    arg_details = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    for member in channel_data['owner_members']:
        if member['u_id'] == user_1['u_id']:
            owner = False
    assert not owner
    requests.delete(url + '/clear')
    

def test_output_user_join_again(url):
    """Test for a person joining again
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_details = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()

    user_details = {'name_first': 'John', 'name_last': 'Smith', 'u_id': user_1['u_id']}
    assert user_details in channel_data['all_members']

    arg_join = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    requests.post(url + 'channel/join', json=arg_join).json()

    # Check channel details if the user is a member
    arg_details = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    assert user_details in channel_data['all_members']

    # Check if channel appears in the user's channels list
    arg_list = {
        'token'     : user_1['token'],
    }
    channel_user_list = requests.get(url + 'channels/list', params=arg_list).json()
    assert len(channel_user_list) == 1
    requests.delete(url + '/clear')
    

#------------------------------------------------------------------------------#
#                                channel_addowner                              #
#------------------------------------------------------------------------------#

#?------------------------- Input/Access Error Testing -----------------------?#

def test_input_channel_id_addowner(url):
    """Testing when Channel ID is not a valid channel
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': -1,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': 0,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': 1,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': 5,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_access_add_valid_token(url):
    """Testing if token is valid
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    log_out = requests.post(url + 'auth/logout', json={'token': user_1['token']}).json()
    assert log_out['is_success']

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == AccessError.code
    requests.delete(url + '/clear')
    

def test_input_u_id_addowner(url):
    """Testing when u_id is not a valid u_id
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : -1,
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : 0,
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : 5,
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : 7,
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_add_user_is_already_owner(url):
    """Testing when user with user id u_id is already an owner of the channel
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()

    # Channel is private (creators are already owners)
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Group 2',
        'is_public': False,
    }
    new_channel_2 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code

    arg_addowner = {
        'token'     : user_2['token'],
        'channel_id': new_channel_2['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_auth_user_is_not_owner(url):
    """Testing when the authorised user is not an owner of the flockr, or an owner of this channel
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()

    # User_1 is owner of new_channel_1 and User_2 is the owner of new_channel_2
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Group 2',
        'is_public': False,
    }
    new_channel_2 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_2['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == AccessError.code

    arg_addowner = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    res_err = requests.post(url + 'channel/addowner', json=arg_addowner)
    res_err.status_code == AccessError.code
    requests.delete(url + '/clear')
    

#?------------------------------ Output Testing ------------------------------?#

def test_output_user_addowner_private(url):
    """Testing if the user has successfully been added as owner of the channel (private)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a private channel
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    requests.post(url + 'channel/addowner', json=arg_addowner).json()

    arg_details = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    user_2_details = {'name_first': 'Jane', 'name_last': 'Smith', 'u_id': user_2['u_id']}
    assert user_2_details in channel_data['all_members']
    assert user_2_details in channel_data['owner_members']
    requests.delete(url + '/clear')
    

def test_output_user_addowner_public(url):
    """Testing if the user has successfully been added as owner of the channel (public)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a public channel
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    requests.post(url + 'channel/addowner', json=arg_addowner).json()

    arg_details = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    user_2_details = {'name_first': 'Jane', 'name_last': 'Smith', 'u_id': user_2['u_id']}
    assert user_2_details in channel_data['all_members']
    assert user_2_details in channel_data['owner_members']
    requests.delete(url + '/clear')
    

def test_output_member_becomes_channel_owner(url):
    """Testing if the user has become a channel owner from a channel member
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a public channel
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    user_2_details = {'name_first': 'Jane', 'name_last': 'Smith', 'u_id': user_2['u_id']}

    arg_join = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    requests.post(url + 'channel/join', json=arg_join).json()

    arg_details = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    print(channel_data)
    assert user_2_details in channel_data['all_members']
    assert user_2_details not in channel_data['owner_members']

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    requests.post(url + 'channel/addowner', json=arg_addowner).json()

    arg_details = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    assert user_2_details in channel_data['all_members']
    assert user_2_details in channel_data['owner_members']
    requests.delete(url + '/clear')
    

#------------------------------------------------------------------------------#
#                                channel_removeowner                           #
#------------------------------------------------------------------------------#

#?------------------------- Input/Access Error Testing -----------------------?#

def test_input_removeowner(url):
    """Testing when Channel ID is not a valid channel
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': -1,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': 0,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': 1,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': 5,
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_access_remove_valid_token(url):
    """Testing if token is valid
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    log_out = requests.post(url + 'auth/logout', json={'token': user_1['token']}).json()
    assert log_out['is_success']

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_1['u_id'],
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == AccessError.code
    requests.delete(url + '/clear')
    

def test_input_u_id_removeowner(url):
    """Testing when u_id is not a valid u_id
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : -1,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_1['u_id'] + 1,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_1['u_id'] - 1,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_1['u_id'] + 7,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_remove_user_is_not_owner(url):
    """Testing when user with user id u_id is not an owner of the channel
    """
    requests.delete(url + '/clear')
    
    # First user is always the flockr owner
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'jonesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jone',
        'name_last' : 'Smith',
    }
    user_3 = requests.post(url + 'auth/register', json=user_profile).json()

    # Channel is private (users are already owners)
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Group 2',
        'is_public': False,
    }
    new_channel_2 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'] + 7,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code

    arg_removeowner = {
        'token'     : user_2['token'],
        'channel_id': new_channel_2['channel_id'],
        'u_id'      : user_3['u_id'] + 7,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == InputError.code
    requests.delete(url + '/clear')
    

def test_remove_user_is_owner(url):
    """Testing when the authorised user is not an owner of the flockr, or an owner of this channel
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Channel is private (users are not owners)
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    channel_profile = {
        'token'    : user_2['token'],
        'name'     : 'Group 2',
        'is_public': False,
    }
    new_channel_2 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_removeowner = {
        'token'     : user_2['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_1['u_id'] + 7,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == AccessError.code

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_2['channel_id'],
        'u_id'      : user_2['u_id'] + 7,
    }
    res_err = requests.post(url + 'channel/removeowner', json=arg_removeowner)
    res_err.status_code == AccessError.code
    requests.delete(url + '/clear')
    

#?------------------------------ Output Testing ------------------------------?#

def test_output_user_removeowner_private(url):
    """Testing if the user has successfully been removed as owner of the channel (private)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()
    # Make a private channel
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': False,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    requests.post(url + 'channel/addowner', json=arg_addowner).json()

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    requests.post(url + 'channel/removeowner', json=arg_removeowner).json()

    arg_details = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()

    for curr_owner in channel_data['owner_members']:
        assert curr_owner['u_id'] is not user_2['u_id']
    requests.delete(url + '/clear')
    

def test_output_user_removeowner_public(url):
    """Testing if the user has successfully been removed as owner of the channel (public)
    """
    requests.delete(url + '/clear')
    
    user_profile = {
        'email'     : 'johnsmith@gmail.com',
        'password'  : 'password',
        'name_first': 'John',
        'name_last' : 'Smith',
    }
    user_1 = requests.post(url + 'auth/register', json=user_profile).json()

    user_profile = {
        'email'     : 'janesmith@gmail.com',
        'password'  : 'password',
        'name_first': 'Jane',
        'name_last' : 'Smith',
    }
    user_2 = requests.post(url + 'auth/register', json=user_profile).json()

    # Make a public channel
    channel_profile = {
        'token'    : user_1['token'],
        'name'     : 'Group 1',
        'is_public': True,
    }
    new_channel_1 = requests.post(url + 'channels/create', json=channel_profile).json()

    arg_addowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    requests.post(url + 'channel/addowner', json=arg_addowner).json()

    arg_removeowner = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
        'u_id'      : user_2['u_id'],
    }
    requests.post(url + 'channel/removeowner', json=arg_removeowner).json()

    arg_details = {
        'token'     : user_1['token'],
        'channel_id': new_channel_1['channel_id'],
    }
    channel_data = requests.get(url + 'channel/details', params=arg_details).json()
    for curr_owner in channel_data['owner_members']:
        assert curr_owner['u_id'] is not user_2['u_id']
    requests.delete(url + '/clear')
    
