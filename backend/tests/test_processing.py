from io import BytesIO
from PIL import Image
import pytest
from app.preprocessing.images import InvalidImage,prepare_image,restore_box


def test_resize_and_roundtrip():
    image = Image.new('RGB',(4000,2000),'white'); b=BytesIO(); image.save(b,format='PNG')
    p=prepare_image(b.getvalue(),max_pixels=9_000_000,max_long_edge=2500)
    assert p.image.size == (2500,1250)
    assert restore_box((250,125,500,250),p) == (400.0,200.0,800.0,400.0)
    assert restore_box((-10,-10,2600,1300),p) == (0.0,0.0,4000.0,2000.0)
    assert restore_box((10,10,10,15),p) is None


def test_exif_orientation():
    image=Image.new('RGB',(40,20),'white');exif=Image.Exif();exif[274]=6
    b=BytesIO();image.save(b,format='JPEG',exif=exif)
    p=prepare_image(b.getvalue(),max_pixels=10000,max_long_edge=2500)
    assert (p.source_width,p.source_height)==(20,40)
    assert p.exif_orientation_applied


def test_bad_input():
    with pytest.raises(InvalidImage): prepare_image(b'',max_pixels=10000,max_long_edge=2500)
    with pytest.raises(InvalidImage): prepare_image(b'fake',max_pixels=10000,max_long_edge=2500)
