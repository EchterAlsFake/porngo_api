import pytest
from porngo_api import Client

@pytest.fixture
def client():
    return Client()

@pytest.mark.asyncio
async def test_video(client):
    video = await client.get_video("https://www.porngo.com/videos/1930359/pervmom-horny-stepmom-kagney-linn-karter-sucks-stepsons-big-dick/")
    assert isinstance(video.title, str) and len(video.title) > 0
    assert isinstance(video.author, str) and len(video.author) > 0
    assert isinstance(video.categories, list) and len(video.categories) > 0
    assert isinstance(video.direct_download_urls, list) and len(video.direct_download_urls) > 0
    assert isinstance(video.dislikes, str) and len(video.dislikes) > 0
    assert isinstance(video.likes, str) and len(video.likes) > 0
    assert isinstance(video.pornstars, list) and len(video.pornstars) > 0
    assert isinstance(video.thumbnail, str) and len(video.thumbnail) > 0
    assert isinstance(video.views, str) and len(video.views) > 0
    assert await video.download(quality="480p") is True


