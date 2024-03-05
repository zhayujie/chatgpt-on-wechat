from common.expired_dict import ExpiredDict

USER_IMAGE_CACHE = ExpiredDict(100 * 3)
USER_WEBPAGE_CACHE = ExpiredDict(60 * 3)
USER_FILE_CACHE = ExpiredDict(60 * 3)