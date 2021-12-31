import dawdreamer
import configparser
import json

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
    pass

if __name__ == '__main__':
    main()