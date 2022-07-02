import dawdreamer
import json
import sys
import traceback
import soundfile
import numpy
import pathlib

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
        self.save_preset_path=''
        self.dist_path='./'
        self.filename_pattern='{name}_{velocity}_{note}_{step}.wav'
        self.press_duration=20.0
        self.duration=22.0
        self.open_editor=False

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
    
    folder = str(pathlib.Path(config_path).parent.absolute())
    #Load plugin
    print("Loading plugin: ", config.vst_path)
    engine = dawdreamer.RenderEngine(config.sample_rate, config.buffer_size)
    plugin = engine.make_plugin_processor("plugin", config.vst_path)
    #Load state
    if config.preset_path != '':
        print("Loading preset: ", folder + '/' + config.preset_path)
        if not plugin.load_state(folder + '/' + config.preset_path):
            print("Couldn't load preset!")
            return
    #Open gui
    if config.open_editor:
        plugin.open_editor()
    #Save preset
    if config.save_preset_path != '':
        plugin.save_state(config.save_preset_path)
    #Open
    #Process
    for velocity in config.velocities:
        #Notes
        note = config.start_note
        time = 1.0
        while note <= config.end_note:
            print("Adding note ", note)
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
        soundfile.write(folder + '/' + config.dist_path + '/' + config.filename_pattern.format(name=config.name, note=config.start_note, velocity=velocity, step=config.note_step), engine.get_audio().transpose(), config.sample_rate, subtype='PCM_24')
       
if __name__ == '__main__':
    main()