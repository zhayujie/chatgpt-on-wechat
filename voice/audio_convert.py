import wave
import pysilk
from pydub import AudioSegment


def get_pcm_from_wav(wav_path):
    """
    从 wav 文件中读取 pcm

    :param wav_path: wav 文件路径
    :returns: pcm 数据
    """
    wav = wave.open(wav_path, "rb")
    return wav.readframes(wav.getnframes())


def mp3_to_wav(mp3_path, wav_path):
    """
    把mp3格式转成pcm文件
    """
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")


def pcm_to_silk(pcm_path, silk_path):
    """
    wav 文件转成 silk
    return 声音长度，毫秒
    """
    audio = AudioSegment.from_wav(pcm_path)
    wav_data = audio.raw_data
    silk_data = pysilk.encode(
        wav_data, data_rate=audio.frame_rate, sample_rate=audio.frame_rate)
    with open(silk_path, "wb") as f:
        f.write(silk_data)
    return audio.duration_seconds * 1000


def mp3_to_sil(mp3_path, silk_path):
    """
    mp3 文件转成 silk
    return 声音长度，毫秒
    """
    audio = AudioSegment.from_mp3(mp3_path)
    wav_data = audio.raw_data
    silk_data = pysilk.encode(
        wav_data, data_rate=audio.frame_rate, sample_rate=audio.frame_rate)
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
