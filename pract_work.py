import asyncio
import aiohttp
import aiofiles
from tqdm.asyncio import tqdm
from bs4 import BeautifulSoup
from aiohttp_retry import RetryClient, ExponentialRetry
from work_file import get_folder_size


class Parser:
    def __init__(self, start_page, schema):
        self.start_page = start_page
        self.schema = schema
        self.one_hundred_urls = []
        self.all_ten_page_imgs_urls = []
        self.all_images_urls = []
        self.semaphore = asyncio.Semaphore(100)
        self.visited_imgs = set()
        self.pbar_hundred_urls = tqdm(
            total=100, desc="Parsing one hundred urls", colour="WHITE"
        )
        self.pbar_ten_links = tqdm(
            total=999, desc="Parsing ten links on page", colour="WHITE"
        )
        self.pbar_download_images = tqdm(
            total=2615, desc="Complete download images", colour="GREEN"
        )

    async def get_hundred_urls(self, session):
        soup: BeautifulSoup = await self.get_soup(self.start_page, session)
        self.one_hundred_urls = [
            f"{self.schema}{tag_a['href']}" for tag_a in soup.select("div.item_card a")
        ]
        self.pbar_hundred_urls.update(100)

    async def get_ten_links(self, url, session):
        soup: BeautifulSoup = await self.get_soup(url, session)
        ten_links_one_page = [
            f"{self.schema + 'depth2/'}{tag_a['href']}"
            for tag_a in soup.select("div.item_card a")
        ]
        self.all_ten_page_imgs_urls.extend(ten_links_one_page)
        self.pbar_ten_links.update(len(ten_links_one_page))

    async def get_image_urls(self, url, session):
        soup: BeautifulSoup = await self.get_soup(url, session)
        ten_image_links = [img["src"] for img in soup.select("div.img_box img")]
        self.all_images_urls.extend(ten_image_links)

    async def download_image(self, url, session):
        filename = url.split("/")[-1]
        if filename not in self.visited_imgs:
            self.visited_imgs.add(filename)
            async with self.semaphore:
                async with aiofiles.open(f"work/download_imgs/{filename}", "wb") as file:
                    async with session.get(url) as response:
                        async for piece in response.content.iter_chunked(512*1024):
                            await file.write(piece)
                        self.pbar_download_images.update(1)

    async def get_soup(self, url, session):
        async with session.get(url) as resp:
            return BeautifulSoup(await resp.text(), "html.parser")

    async def main(self):
        timeout = aiohttp.ClientTimeout(total=300)  # Если слабое интернет соединение
        connector = aiohttp.TCPConnector(limit=100)
        async with aiohttp.ClientSession(timeout=timeout, read_bufsize=512*1024, connector=connector) as client_session:
            retry_options = ExponentialRetry(attempts=6, statuses={404, 443, 400}, exceptions=[asyncio.TimeoutError])
            async with RetryClient(client_session=client_session, retry_options=retry_options) as session:
                await self.get_hundred_urls(session)

                all_ten_urls_task = [self.get_ten_links(url, session) for url in self.one_hundred_urls]
                await asyncio.gather(*all_ten_urls_task)

                all_ten_image_task = [
                    self.get_image_urls(url, session)
                    for url in self.all_ten_page_imgs_urls]
                await asyncio.gather(*all_ten_image_task)

                download_image_task = [self.download_image(url, session) for url in self.all_images_urls]
                await asyncio.gather(*download_image_task)

    def __call__(self, *args, **kwargs):
        asyncio.run(self.main())
        print(f"Размер всех изображений: {get_folder_size("work/download_imgs")}")

start_page = "https://parsinger.ru/asyncio/aiofile/3/index.html"
schema = "https://parsinger.ru/asyncio/aiofile/3/"
parser = Parser(start_page=start_page, schema=schema)
parser()
