# tests/test_map_endpoints.py
import sys
import os
os.environ["TESTING"] = "1"   # prevents background thread from starting
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import pytest
import FlaskServer as _fs
from FlaskServer import app, _sse_clients, _sse_lock


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_map_state():
    _fs._map_point_count = 0
    _fs._map_seq = -1
    _fs._jetson_ws_connected = False
    yield
    _fs._map_point_count = 0
    _fs._map_seq = -1
    _fs._jetson_ws_connected = False


class TestMapStatus:
    def test_returns_200(self, client):
        r = client.get('/map_status')
        assert r.status_code == 200

    def test_has_required_keys(self, client):
        data = json.loads(client.get('/map_status').data)
        assert 'connected' in data
        assert 'point_count' in data
        assert 'seq' in data

    def test_default_not_connected(self, client):
        data = json.loads(client.get('/map_status').data)
        assert data['connected'] is False

    def test_default_point_count_zero(self, client):
        data = json.loads(client.get('/map_status').data)
        assert data['point_count'] == 0


class TestMapControl:
    def test_returns_503_when_not_connected(self, client):
        r = client.post('/map_control',
                        data=json.dumps({'action': 'start'}),
                        content_type='application/json')
        assert r.status_code == 503

    def test_clear_resets_point_count(self, client):
        _fs._map_point_count = 42
        client.post('/map_control',
                    data=json.dumps({'action': 'clear'}),
                    content_type='application/json')
        assert _fs._map_point_count == 0

    def test_clear_resets_seq(self, client):
        _fs._map_seq = 10
        client.post('/map_control',
                    data=json.dumps({'action': 'clear'}),
                    content_type='application/json')
        assert _fs._map_seq == -1


class TestConfig:
    def test_config_returns_jetson_ws_url(self, client):
        data = json.loads(client.get('/config').data)
        assert 'jetson_ws_url' in data

    def test_config_post_updates_jetson_ws_url(self, client):
        r = client.post('/config',
                        data=json.dumps({'jetson_ws_url': 'ws://10.0.0.5:9001'}),
                        content_type='application/json')
        data = json.loads(r.data)
        assert data.get('jetson_ws_url') == 'ws://10.0.0.5:9001'
