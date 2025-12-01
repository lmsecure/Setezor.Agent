import aiodns
import asyncio
import os
from base64 import b64decode



class Domain_brute:

    @classmethod
    async def query(cls, name: str, dict_file: str | None = None, query_type: str = "A") -> list[str]:
        """
            Отправляет запросы на dns сервера с заданным доменом
            по записи 'A'. Возвращает все найденные доменные имена
        """
        async def resolve(resolver: aiodns.DNSResolver, subdomain: str, name: str, query_type: str):
            URL = f"{subdomain}.{name}"
            return URL, await resolver.query(URL,query_type)


        async def resolve_domain(sem: asyncio.Semaphore, resolver: aiodns.DNSResolver, subdomain: str, name: str, query_type: str = "A"):
            async with sem:
                return await resolve(resolver, subdomain, name, query_type)

        subdomains = cls.get_subdomains_from_file(file=dict_file)
        resolver = aiodns.DNSResolver(loop=asyncio.get_event_loop())
        tasks = []
        sem = asyncio.Semaphore(100)
        for subdomain in subdomains:
            task = asyncio.create_task(resolve_domain(sem, resolver, subdomain, name, query_type))
            tasks.append(task)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        result = set()
        for response in responses:
            if not isinstance(response, aiodns.error.DNSError):
                result.add(response[0])
        return list(result)


    @classmethod
    def get_subdomains_from_file(cls, file: str | None) -> set[str]:
        if file:
            data = b64decode(file.split(',')[1]).decode()
            return set(data.splitlines())
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "subdomains.txt")
        with open(file_path,'r') as file:
            return set(file.read().splitlines())
