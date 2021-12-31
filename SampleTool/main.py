import dawdreamer
import json
import sys
import traceback

class SampleToolParams:

    def __init__(self):
        self.sample_rate=48000
        self.buffer_size=265
        self.name='sample'
        self.start_note=22
        self.end_note=108
        self.note_step=3
        self.velocities=[]
        self.vst_path=''
        self.preset_path=''
        self.dist_path='./'
        self.filename_pattern='{name}_{note}_{velocity}.wav'

def main():
    #Load config
    config_path='./config.json'
    if len(sys.argv) > 1:
        config_path=sys.argv[1]

    print("Loading ", config_path)
    config = SampleToolParams()
    try:
        with open(config_path, 'r') as cfg:
            c = json.load(cfg)
            config.__dict__.update(c)
    except:
        print("Config not found!")
        traceback.print_exc()
    with open(config_path, 'w') as cfg:
        json.dump(config.__dict__, cfg, indent=4)
    
    #Process



if __name__ == '__main__':
    main()