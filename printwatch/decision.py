from collections import defaultdict, deque

class DecisionEngine:
    """Evidence is independent for each camera/class; missing frames break continuity."""
    def __init__(self):
        self.history=defaultdict(deque)
        self.last_frame={}

    def reset(self, camera=None):
        if camera is None:
            self.history.clear(); self.last_frame.clear()
        else:
            for key in list(self.history):
                if key[0] == camera: del self.history[key]
            self.last_frame.pop(camera,None)

    def update(self, camera, detections, now, config):
        previous=self.last_frame.get(camera)
        if previous is not None and now-previous > config['max_frame_age_seconds']:
            self.reset(camera)
        self.last_frame[camera]=now
        best={}
        for d in detections:
            category=d['category']; rule=config['categories'][category]
            area=d['box'][2]*d['box'][3]
            if rule['enabled'] and d['score'] >= rule['threshold'] and rule['minimum_area'] <= area <= rule['maximum_area']:
                if category not in best or best[category]['score'] < d['score']: best[category]=d
        confirmed=[]
        progress={}
        for category in config['categories']:
            key=(camera,category); h=self.history[key]
            # A clean analysed frame resets the streak, unlike the original decrementing counter.
            if category not in best:
                h.clear(); continue
            h.append(now)
            while h and now-h[0] > config['window_seconds']: h.popleft()
            elapsed=now-h[0]
            progress[category]={'hits':len(h),'seconds':round(elapsed,1)}
            if len(h) >= config['minimum_hits'] and elapsed >= config['minimum_duration_seconds']:
                confirmed.append(best[category])
        return confirmed, progress

def pause_allowed(config, printer, armed_seconds, frame_age, camera_ok, cooldown_elapsed):
    return (config['monitoring'] and config['action'] == 'pause'
            and printer.get('state') == 'printing'
            and printer.get('fresh',False)
            and armed_seconds >= config['warmup_seconds']
            and 0 <= frame_age <= config['max_frame_age_seconds']
            and camera_ok and cooldown_elapsed >= config['cooldown_seconds'])
