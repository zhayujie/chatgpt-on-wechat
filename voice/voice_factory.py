"""
voice factory
"""

def create_voice(voice_type):
    """
    create a voice instance
    :param voice_type: voice type code
    :return: voice instance
    """
    if voice_type == 'xfyun':
        from voice.xfyun.xfyun_voice import XfyunVoice
        return XfyunVoice()
    elif voice_type == 'google':
        from voice.google.google_voice import GoogleVoice
        return GoogleVoice()
    raise RuntimeError
