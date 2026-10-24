import copy
import unittest
from printwatch.config import DEFAULT, validate
from printwatch.decision import DecisionEngine, pause_allowed

class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.c=copy.deepcopy(DEFAULT); self.e=DecisionEngine()
        self.d={'category':'spaghetti','score':0.9,'box':[0.1,0.1,0.2,0.2]}
    def test_separated_cameras_cannot_accumulate(self):
        self.e.update('a',[self.d],0,self.c)
        self.e.update('b',[self.d],3,self.c)
        confirmed,_=self.e.update('a',[self.d],6,self.c)
        self.assertFalse(confirmed)
    def test_clean_frame_breaks_streak(self):
        for t,ds in [(0,[self.d]),(3,[self.d]),(4,[]),(6,[self.d]),(9,[self.d])]:
            confirmed,_=self.e.update('a',ds,t,self.c)
            self.assertFalse(confirmed)
        confirmed,_=self.e.update('a',[self.d],12,self.c)
        self.assertEqual(confirmed,[self.d])
    def test_missing_frame_gap_breaks_streak(self):
        self.e.update('a',[self.d],0,self.c); self.e.update('a',[self.d],3,self.c)
        confirmed,_=self.e.update('a',[self.d],20,self.c)
        self.assertFalse(confirmed)
    def test_different_categories_cannot_accumulate(self):
        self.e.update('a',[self.d],0,self.c)
        other=dict(self.d,category='blob')
        self.e.update('a',[other],3,self.c)
        self.assertFalse(self.e.update('a',[self.d],6,self.c)[0])
    def test_observation_cannot_pause(self):
        self.c['monitoring']=True
        self.assertFalse(pause_allowed(self.c,{'state':'printing','fresh':True},100,1,True,999))
    def test_pause_requires_all_gates(self):
        self.c.update(action='pause',monitoring=True)
        good=({'state':'printing','fresh':True},40,1,True,999)
        self.assertTrue(pause_allowed(self.c,*good))
        for args in [({'state':'paused','fresh':True},40,1,True,999),
                     ({'state':'printing','fresh':False},40,1,True,999),
                     (good[0],1,1,True,999),(good[0],40,11,True,999),
                     (good[0],40,1,False,999),(good[0],40,1,True,1)]:
            self.assertFalse(pause_allowed(self.c,*args))
    def test_bad_roi_rejected(self):
        self.c['cameras'][0]['roi']=[0.9,0,0.2,1]
        with self.assertRaises(ValueError): validate(self.c)
    def test_nan_threshold_rejected(self):
        self.c['categories']['blob']['threshold']=float('nan')
        with self.assertRaises(ValueError): validate(self.c)

if __name__=='__main__': unittest.main()
