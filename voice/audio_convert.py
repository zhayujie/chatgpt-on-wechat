import shutil
import wave
import pysilk
from pydub import AudioSegment

sil_supports=[8000, 12000, 16000, 24000, 32000, 44100, 48000] # slk转wav时，支持的采样率
def find_closest_sil_supports(sample_rate):
    """
    找到最接近的支持的采样率
    """
    if sample_rate in sil_supports:
        return sample_rate
    closest = 0
    mindiff = 9999999
    for rate in sil_supports:
        diff = abs(rate - sample_rate)
        if diff < mindiff:
            closest = rate
            mindiff = diff
    return closest

def get_pcm_from_wav(wav_path):
    """
    从 wav 文件中读取 pcm

    :param wav_path: wav 文件路径
    :returns: pcm 数据
    """
    wav = wave.open(wav_path, "rb")
    return wav.readframes(wav.getnframes())

def any_to_wav(any_path, wav_path):
    """
    把任意格式转成wav文件
    """
    if any_path.endswith('.wav'):
        shutil.copy2(any_path, wav_path)
        return
    if any_path.endswith('.sil') or any_path.endswith('.silk') or any_path.endswith('.slk'):
        return sil_to_wav(any_path, wav_path)
    audio = AudioSegment.from_file(any_path)
    audio.export(wav_path, format="wav")

def any_to_sil(any_path, sil_path):
    """
    把任意格式转成sil文件
    """
    if any_path.endswith('.sil') or any_path.endswith('.silk') or any_path.endswith('.slk'):
        shutil.copy2(any_path, sil_path)
        return 10000
    if any_path.endswith('.wav'):
        return pcm_to_sil(any_path, sil_path)
    if any_path.endswith('.mp3'):
        return mp3_to_sil(any_path, sil_path)
    raise NotImplementedError("Not support file type: {}".format(any_path))

def mp3_to_wav(mp3_path, wav_path):
    """
    把mp3格式转成pcm文件
    """
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")

def pcm_to_sil(pcm_path, silk_path):
    """
    wav 文件转成 silk
    return 声音长度，毫秒
    """
    audio = AudioSegment.from_wav(pcm_path)
    rate = find_closest_sil_supports(audio.frame_rate)
    # Convert to PCM_s16
    pcm_s16 = audio.set_sample_width(2)
    pcm_s16 = pcm_s16.set_frame_rate(rate)
    wav_data = pcm_s16.raw_data
    silk_data = pysilk.encode(
        wav_data, data_rate=rate, sample_rate=rate)
    with open(silk_path, "wb") as f:
        f.write(silk_data)
    return audio.duration_seconds * 1000

def mp3_to_sil(mp3_path, silk_path):
    """
    mp3 文件转成 silk
    return 声音长度，毫秒
    """
    audio = AudioSegment.from_mp3(mp3_path)
    rate = find_closest_sil_supports(audio.frame_rate)
    # Convert to PCM_s16
    pcm_s16 = audio.set_sample_width(2)
    pcm_s16 = pcm_s16.set_frame_rate(rate)
    wav_data = pcm_s16.raw_data
    silk_data = pysilk.encode(wav_data, data_rate=rate, sample_rate=rate)
    # Save the silk file
    with open(silk_path, "wb") as f:
        f.write(silk_data)
    return audio.duration_seconds * 1000

def sil_to_wav(silk_path, wav_path, rate: int = 24000):
    """
    silk 文件转 wav
    """
    wav_data = pysilk.decode_file(silk_path, to_wav=True, sample_rate=rate)
    with open(wav_path, "wb") as f:
        f.write(wav_data)
