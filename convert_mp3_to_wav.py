import librosa
import soundfile as sf

def convert_mp3_to_wav(mp3_path, wav_path="temp.wav"):
    y, sr = librosa.load(mp3_path, sr=16000, mono=True)
    sf.write(wav_path, y, 16000)
    # print("MP# path", mp3_path, wav_path)
    print("Success Fully converted to wav")
    return wav_path