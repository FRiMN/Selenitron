import io
from typing import Optional

from arsenic import services, browsers, get_session
from fastapi import FastAPI
from starlette.responses import StreamingResponse

from consumers import StreamConsumer
from generators.html import HTMLGenerator
from generators.pdf import PdfGenerator
from utils import add_partner_id_and_locale_in_url, timing

app = FastAPI()


@app.get("/render/{url:path}")
@timing
def render(url: str, partner_id: Optional[str] = None, locale: Optional[str] = None):
    if partner_id or locale:
        url = add_partner_id_and_locale_in_url(url, partner_id, locale)

    consumer = StreamConsumer()
    generator = HTMLGenerator(url, consumer)
    generator.add_task(0, 0)
    task = generator.execute_tasks()[0]
    return StreamingResponse(io.StringIO(task.data), media_type="text/html")


@app.get("/pdf/{url:path}")
@timing
def pdf(url: str, width: int = 1280, height: int = 800, partner_id: Optional[str] = None, locale: Optional[str] = None):
    if partner_id or locale:
        url = add_partner_id_and_locale_in_url(url, partner_id, locale)

    consumer = StreamConsumer()
    generator = PdfGenerator(url, consumer)
    generator.add_task(width, height)
    task = generator.execute_tasks()[0]
    return StreamingResponse(io.BytesIO(task.data), media_type="application/pdf")


@app.get("/screenshot/{url:path}")
# @timing
async def screenshot(url: str, width: int = 1280, height: int = 800, partner_id: Optional[str] = None,
               locale: Optional[str] = None):
    if partner_id or locale:
        url = add_partner_id_and_locale_in_url(url, partner_id, locale)

    # consumer = StreamConsumer()
    # generator = AsyncScreenshotGenerator(url, consumer)
    # generator.add_task(width, height)
    # generator.add_task(100, 100)
    # generator.add_task(200, 200)
    # generator.add_task(300, 300)
    # tasks = await generator.execute_tasks()
    # task = tasks[0]
    # print('data', task.data)
    # return StreamingResponse(io.BytesIO(task.data), media_type="image/jpeg")

    service = services.Chromedriver()
    browser = browsers.Chrome()

    async with get_session(service, browser) as session:
        await session.set_window_size(width, height)

        await session.get(url)
        # hide_scrollbars(session)

        s = await session.get_page_source()
    return s
