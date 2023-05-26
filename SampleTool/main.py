import dawdreamer
import json
import sys
import traceback
import soundfile
import numpy
import pathlib
import scipy.io.wavfile
import os
import time

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
        self.seperate_release=False
        self.release_filename_pattern='{name}_{velocity}_{note}_release.wav'
        self.normalize_release_seperate=True
        self.start_time=1

class SampleToolFile:

    def __init__(self, path, filename, audio):
        self.path = path
        self.filename = filename
        self.audio = audio

def normalize(files):
    # Find max volume
    m = 0
    for f in files:
        for s in f:
            for c in s:
                if abs(c) > m:
                    m = abs(c)
    # Normalize
    print("max :", m)
    if m > 0:
        for f in files:
            for i in range(len(f)):
                for j in range(len(f[i])):
                    f[i][j] = f[i][j]/m
    
def cut_silence(audio, threshold, release_time): # Threshold as scalar, release in samples
    index = 0
    # Find first index
    for i in reversed(range(len(audio))):
        found = False
        for c in audio[i]:
            if abs(c) >= threshold:
                index = i
                found = True
        if found:
            break
    # Release
    end_index = min(len(audio), index + release_time)
    if end_index > index:
        for i in range(index, end_index):
            percent = (i - index)/(end_index - index)
            audio[i] *= percent
    print("Cutting " + str(index) + "/" + str(end_index) + "/" + str(len(audio)))
    # Cut end
    return audio[0:end_index]

def trim_start(audio):
    index = 0
    # Find first index
    for i in range(len(audio)):
        found = False
        for c in audio[i]:
            if abs(c) >= 0:
                index = i
                found = True
        if found:
            break
    # Cut end
    return audio[index:]
    

def save_files(files, sample_rate):
    for f in files:
        os.makedirs(f.path, exist_ok=True)
        soundfile.write(f.path + '\\' + f.filename, f.audio, sample_rate, subtype='PCM_24')

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
            # Convert velocities
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
        dump["velocities"] = []
        for vel in config.velocities:
            dump['velocities'].append(vel.__dict__)
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
    t = time.time()/1000.0
    if config.open_editor:
        plugin.open_editor()
    #Save preset
    if config.save_preset_path != '':
        plugin.save_state(config.save_preset_path)
    #Open
    if config.normalize == 'total':
        print('Normalizing all files together')
    elif config.normalize == 'velocity':
        print('Normalizing each velocity individually')
    elif config.normalize == 'note':
        print('Normalizing each note individually')
    else:
        print('Applying no normalization')
    #Clear buffers
    graph= [
        (plugin, [])
    ]
    engine.load_graph(graph)
    engine.render(time.time()/1000.0 - t + 2)
    plugin.clear_midi()
    #Velocities
    files = []
    to_normalize = []
    to_normalize_release = []
    for velocity in config.velocities:
        print("Processing velocity ", velocity.name, " (", velocity.velocity, ")")
        #Notes
        note = config.start_note
        while note <= config.end_note:
            print("Rendering note ", note)
            graph= [
                (plugin, [])
            ]
            plugin.add_midi_note(note, velocity.velocity, config.start_time, config.press_duration)
            engine.load_graph(graph)
            engine.render(config.duration + config.start_time)
            plugin.clear_midi()

            audio = trim_start(engine.get_audio().transpose())
            path = folder + '\\' + config.dist_path + '\\' + velocity.name
            file = SampleToolFile(path, config.filename_pattern.format(name=config.name, note=note, velocity=velocity.name, step=config.note_step), audio)
            #Cut end
            if config.seperate_release:
                dur = round(config.press_duration * config.sample_rate)
                release = audio[dur:]
                audio = audio[0:dur]
                file.audio = audio # Re set the audio
                rel = SampleToolFile(path, config.release_filename_pattern.format(name=config.name, note=note, velocity=velocity.name, step=config.note_step), release)
                if config.normalize_release_seperate:
                    to_normalize_release.append(release)
                else:
                    to_normalize.append(release)
                files.append(rel)
            to_normalize.append(audio)
            files.append(file)
            if config.normalize == 'note': #Normalize every note
                normalize(to_normalize)
                normalize(to_normalize_release)
                to_normalize = []
                to_normalize_release = []
            note += config.note_step
        if config.normalize == 'velocity': #Normalize every velocity
            print(to_normalize)
            normalize(to_normalize)
            normalize(to_normalize_release)
            to_normalize = []
            to_normalize_release = []
    if config.normalize == 'total': #Normalize all files
        normalize(to_normalize)
        normalize(to_normalize_release)
        to_normalize = []
        to_normalize_release = []

    #Post process
    if config.cut_silence:
        print("Cutting end silence with a " + str(config.silence_threshold) + " dB threshold and a release time of " + str(config.release_time) + " s")
        for f in files:
            f.audio = cut_silence(f.audio, pow(10, config.silence_threshold/10), round(config.release_time * config.sample_rate))
    # TODO
    # Save files
    print("Saving files ...")
    save_files(files, config.sample_rate)
    files = []
    print("Done")
       
if __name__ == '__main__':
    main()

