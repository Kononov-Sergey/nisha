import asyncio
from app.services.pikabu_parser import PikabuParser


async def main():
    parser = PikabuParser()
    posts = await parser.parse_posts_by_tags(limit_per_tag=5, tags=["Бизнес"])  # можно менять теги
    print("TOTAL_POSTS", len(posts))
    for i, p in enumerate(posts[:3]):
        print("SAMPLE", i, p.get("url"), p.get("pain_keywords"), p.get("pain_intensity"))


if __name__ == "__main__":
    asyncio.run(main())


