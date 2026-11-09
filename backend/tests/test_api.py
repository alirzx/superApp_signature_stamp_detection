def test_health_and_auth(client):
    assert client.get('/health/live').status_code == 200
    assert client.get('/health/ready').json()['device'] == 'cpu'
    assert client.get('/v1/models').status_code == 401
    models = client.get('/v1/models',headers={'X-API-Key':'abc-123-testing-secret'})
    assert models.status_code == 200
    assert models.json()['models'][0]['classes'] == ['stamp','signature']


def test_detect_schema(client,png_bytes):
    response = client.post('/v1/detect',headers={'X-API-Key':'abc-123-testing-secret'},
        files={'file':('example.png',png_bytes,'image/png')}, data={'document_id':'doc-7','page_id':'page-1','page_number':2})
    assert response.status_code == 200,response.text
    r=response.json()
    assert r['schema_version'] == 'superapp.stamp-signature.v1'
    assert r['counts'] == {'stamp':1,'signature':1}
    assert r['image']['source_coordinate_space'] == 'exif_corrected_source_pixels'
    assert len(r['objects']) == 2
    assert {o['type'] for o in r['objects']} == {'stamp','signature'}
    assert all(o['provenance']['model_version'] for o in r['objects'])
    assert r['objects'][0]['page_number'] == 2


def test_filter_routes(client,png_bytes):
    headers={'X-API-Key':'abc-123-testing-secret'}
    def call(path): return client.post(path,headers=headers,files={'file':('f.png',png_bytes,'image/png')})
    assert call('/v1/detect/stamps').json()['counts'] == {'stamp':1,'signature':0}
    assert call('/v1/detect/signatures').json()['counts'] == {'stamp':0,'signature':1}
    assert call('/v1/detect').json()['counts'] == {'stamp':1,'signature':1}


def test_reject_bad_image_and_limits(client,settings,png_bytes):
    h={'X-API-Key':'abc-123-testing-secret'}
    assert client.post('/v1/detect',headers=h,files={'file':('a.pdf',b'not-image','application/pdf')}).status_code == 422
    assert client.post('/v1/detect',headers=h,files={'file':('f.png',png_bytes,'image/png')},data={'threshold':'1.5'}).status_code == 422
    assert client.post('/v1/detect',headers=h,files={'file':('f.png',png_bytes,'image/png')},data={'page_number':'0'}).status_code == 422
    assert client.post('/v1/detect',headers=h,files={'file':('f.png',png_bytes,'image/png')},data={'document_id':'   '}).status_code == 422
    assert client.post('/v1/detect',headers={'X-API-Key':'invalid'},files={'file':('f.png',png_bytes,'image/png')}).status_code == 401
