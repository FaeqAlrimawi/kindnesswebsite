
import urllib
import mimetypes
from ..models import MediaType
from ..control import getBaseURL

def getMediaType(mediaURL):
    # get media type (video or image or gif, etc)
    mediaType = mimetypes.MimeTypes().guess_type(mediaURL)[0]
    
    if mediaType is not None:
        if "image" in mediaType:
            mediaType = MediaType.IMAGE
        elif "video" in mediaType:
            mediaType = MediaType.VIDEO    
    
    else:
        # check if it is a youtube video
        baseURL = getBaseURL(mediaURL)
        youtubeURLs = ["youtube", "youtu."]
        vimeoURLs = ["vimeo"]
        if any(src in baseURL for src in youtubeURLs):
            mediaType = MediaType.YOUTUBE
        elif  any(src in baseURL for src in vimeoURLs):
             mediaType = MediaType.VIMEO
              
    if mediaType is None:
        mediaType = MediaType.UNKNOWN
        
    return mediaType    