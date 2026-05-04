import asyncio
import os
from t_tech.invest import AsyncClient, InstrumentStatus
from dotenv import load_dotenv

load_dotenv()

async def main():
    async with AsyncClient(os.getenv("TINVEST_READONLY_TOKEN")) as client:
        status = InstrumentStatus.INSTRUMENT_STATUS_ALL
        resp = await client.instruments.shares(instrument_status=status)
        shares = {s.ticker: s for s in resp.instruments}
        
        resp = await client.instruments.etfs(instrument_status=status)
        etfs = {s.ticker: s for s in resp.instruments}
        
        resp = await client.instruments.indices(instrument_status=status)
        indices = {s.ticker: s for s in resp.instruments}

        for t in ["YNDX", "YDEX", "POLYMETAL", "POLY", "DIVI", "TDIV", "RSTI", "FEES", "IMOEX", "VK", "VKCO"]:
            if t in shares:
                print(f"{t}: Share (name: {shares[t].name})")
            elif t in etfs:
                print(f"{t}: ETF (name: {etfs[t].name})")
            elif t in indices:
                print(f"{t}: Index (name: {indices[t].name})")
            else:
                print(f"{t}: NOT FOUND")

asyncio.run(main())
