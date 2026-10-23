"""Optional public-text synthetic Persian narration; no API/billing credentials.

Requires edge-tts. The text is the public demo description, not user notes.
"""
import argparse,asyncio,json
from pathlib import Path

async def main(source,output):
    import edge_tts
    output.mkdir(parents=True,exist_ok=True)
    scenes=json.loads(source.read_text());(output/'script.json').write_text(source.read_text())
    sem=asyncio.Semaphore(2)
    async def one(i,item):
        async with sem:
            await asyncio.wait_for(edge_tts.Communicate(item['text'],voice='fa-IR-FaridNeural',rate='-4%').save(str(output/f'{i+1}.mp3')),90)
    await asyncio.gather(*(one(i,x) for i,x in enumerate(scenes)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--online',action='store_true');p.add_argument('--script',type=Path,default=Path('docs/DEMO_NARRATION_FA.json'));p.add_argument('--output',type=Path,default=Path('artifacts/review-voice'));a=p.parse_args()
    if not a.online:p.error('explicit --online required; sends only public narration text to Edge')
    asyncio.run(main(a.script,a.output))
