import dawdreamer
import json
import sys
import traceback
from scipy.io import wavfile

class SampleToolParams:

    def __init__(self):
        self.sample_rate=48000
        self.buffer_size=265
        self.name='sample'
        self.start_note=22
        self.end_note=108
        self.note_step=3
        self.velocities=[127]
        self.vst_path=''
        self.preset_path=''
        self.dist_path='./'
        self.filename_pattern='{name}_{velocity}_{note}_{step}.wav'
        self.press_duration=20.0
        self.duration=22.0

def main():
    #Load config
    config_path='./config.json'
    found=True
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
        found=False
    with open(config_path, 'w') as cfg:
        json.dump(config.__dict__, cfg, indent=4)
    
    if not found:
        return
    
    #Process
    for velocity in config.velocities:
        #Load plugin
        print("Loading plugin: ", config.vst_path)
        engine = dawdreamer.RenderEngine(config.sample_rate, config.buffer_size)
        plugin = engine.make_plugin_processor("plugin", config.vst_path)
        if config.preset_path != '':
            print("Loading preset: ", config.preset_path)
            plugin.load_preset(config.preset_path)
        #Notes
        note = config.start_note
        time = 0.0
        while note <= config.end_note:
            print("Addning note ", note)
            plugin.add_midi_note(note, velocity, time, config.press_duration)
            note += config.note_step
            time += config.duration
        #Render
        print("Rendering velocity ", velocity, " Duration: ", time/60.0 , " min")
        graph= [
            (plugin, [])
        ]
        engine.load_graph(graph)
        engine.render(time)
        print("Finished rendering velocity ", velocity)
        wavfile.write(config.dist_path + '/' + config.filename_pattern.format(name=config.name, note=config.start_note, velocity=velocity, step=config.note_step), config.sample_rate, engine.get_audio().transpose())
       
if __name__ == '__main__':
    main()