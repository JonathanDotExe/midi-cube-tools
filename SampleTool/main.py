import dawdreamer
import json
import sys
import traceback
import soundfile
import numpy
import pathlib
import scipy.io.wavfile

class SampleToolVelocity:

    def __init__(self, name = "", velocity = 0) -> None:
        self.name = name
        self.velocity = velocity

class SampleToolParams:

    def __init__(self):
        self.sample_rate=48000
        self.buffer_size=265
        self.name='sample'
        self.start_note=22
        self.end_note=108
        self.note_step=3
        self.velocities=[SampleToolVelocity("FFF", 127)]
        self.vst_path=''
        self.preset_path=''
        self.save_preset_path=''
        self.dist_path='./'
        self.filename_pattern='{name}_{velocity}_{note}.wav'
        self.press_duration=20.0
        self.duration=22.0
        self.open_editor=False
        self.normalize='total' #possible values: none, total, velocity, note
        self.cut_silence=True
        self.silence_threshold=-70 #in dB
        self.release_time=0.05

def normalize(files):
    # Find max volume
    max = 0
    for f in files:
        for s in f:
            if abs(s) > max:
                max = abs(s)
    # Normalize
    if max > 0:
        for f in files:
            for i in range(f.len):
                f[i] = f[i]/max
    
def cut_silence(audio, threshold, release_time): # Threshold as scalar, release in samples
    index = audio.len
    # Find first index
    for i in reversed(range(audio.len)):
        if abs(audio[i]) >= threshold:
            index = i
    # Release
    end_index = min(audio.len, index + release_time)
    if end_index > index:
        for i in range(index, end_index):
            percent = (i - index)/(end_index - index)
            audio[i] *= percent
    # Cut end
    
    

def save_files(files, sample_rate):
    for f in files:
        soundfile.write(f[0], f[1], sample_rate, subtype='PCM_24')

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
            for i in range(len(config.velocities)):
                vel = SampleToolVelocity()
                vel.__dict__.update(config.velocities[i])
                config.velocities[i] = vel
    except:
        print("Config not found!")
        traceback.print_exc()
        found=False
    # Save settings to add new options
    with open(config_path, 'w') as cfg:
        # Convert to dict
        dump = config.__dict__.copy()
        for i in range(len(dump['velocities'])):
            dump['velocities'][i] = dump['velocities'][i].__dict__
        json.dump(dump, cfg, indent=4)
    
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
        plugin.load_state(folder + '/' + config.preset_path)
    #Open gui
    if config.open_editor:
        plugin.open_editor()
    #Save preset
    if config.save_preset_path != '':
        plugin.save_state(config.save_preset_path)
    #Open
    #Velocities
    files = []
    to_normalize = []
    for velocity in config.velocities:
        print("Processing velocity ", velocity.name, " (", velocity.velocity, ")")
        #Notes
        note = config.start_note
        while note <= config.end_note:
            print("Rendering note ", note)
            graph= [
                (plugin, [])
            ]
            plugin.add_midi_note(note, velocity.velocity, 0, config.press_duration)
            engine.load_graph(graph)
            engine.render(config.duration)

            print(engine.get_audio())
            audio = engine.get_audio().transpose()
            path = folder + '/' + config.dist_path + '/' + velocity.name + '/' + config.filename_pattern.format(name=config.name, note=config.start_note, velocity=velocity.name, step=config.note_step)
            print(audio)
            file = (path, audio)
            if config.normalize == 'note': #Normalize every note
                normalize(audio)
            else:
                to_normalize.append(file)
            files.append(file)
            note += config.note_step
        if config.normalize == 'velocity': #Normalize every velocity
            normalize(to_normalize)
            to_normalize = []
    if config.normalize == 'total': #Normalize all files
        normalize(to_normalize)

    #Post process
    # TODO
    # Save files
    save_files(files, config.sample_rate)
    files = []
       
if __name__ == '__main__':
    main()

