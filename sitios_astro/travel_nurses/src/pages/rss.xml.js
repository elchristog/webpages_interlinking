import rss from "@astrojs/rss";
import { getCollection } from "astro:content";

export async function GET(context) {
  const posts = await getCollection("posts");
  return rss({
    title: "Lexington Themes",
    description:
      "Free and premium multipage themes and UI Kits For freelancers, developers, businesses, and personal use. Beautifully crafted with Astro.js, and Tailwind CSS — Simple & easy to customise.",
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/blog/posts/${post.id}/`,
    })),
  });
}