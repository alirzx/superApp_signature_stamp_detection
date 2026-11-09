import numpy as np
from app.inference.rfdetr import parse_detections

class Detections:
    xyxy=np.array([[1,2,100,120],[3,4,20,40],[8,9,15,16]])
    class_id=np.array([0,1,2]);confidence=np.array([.91,.82,.99])
    data={'class_name':['wrong','wrong','checkbox_checked']}

def test_supervision_keeps_only_stamp_signature():
    d=parse_detections(Detections(),.5)
    assert [x.label for x in d] == ['stamp','signature']
    assert [x.class_id for x in d] == [0,1]

def test_legacy_dict_compatible():
    d=parse_detections([{'class':0,'confidence':.8,'bbox':[1,2,5,6]},
                        {'class':3,'confidence':.99,'bbox':[1,2,5,6]},
                        {'class':1,'confidence':.1,'bbox':[1,2,5,6]}],.5)
    assert len(d)==1 and d[0].label=='stamp'
