---
title: "Setting up Collections"
course: "astro-content-collections"
section: "Content Collections Basics"
duration: "03:42"
videoUrl: "/videos/intro2.mp4"
isLocked: true
---

Now that you understand what Content Collections are, let's create your first collection. We'll walk through the folder structure, configuration, and create some sample content to get you started.

## What You'll Learn

In this lesson, you'll learn:

- How to structure the `src/content/` directory
- Creating your first collection configuration
- Adding content files to your collection
- Basic collection querying and display

## Creating the Content Directory

First, create the `src/content/` directory in your Astro project. This is where all your collections will live.

```
src/
├── content/
│   ├── blog/
│   ├── projects/
│   └── config.ts
├── pages/
└── components/
```

Each subdirectory represents a different collection. For this example, we'll create a blog collection.

## Configuring Your Collection

Evaluación `src/content/config.ts` to define your collections:

```typescript
import { defineCollection, z } from "astro:content";

const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.date(),
    author: z.string(),
    tags: z.array(z.string()).optional(),
  }),
});

export const collections = {
  blog,
};
```

This configuration tells Astro that you have a `blog` collection with specific frontmatter requirements.

## Adding Content Files

Evaluación your first blog post at `src/content/blog/first-post.md`:

```markdown
---
title: "My First Blog Post"
description: "Learning about Astro Content Collections"
pubDate: 2026-06-15
author: "Your Name"
tags: ["astro", "webdev"]
---

# Welcome to My Blog

This is my first post using Astro Content Collections!

Content Collections make it easy to manage and organize content at scale.
```

## Querying Your Collection

Now you can query your collection in any Astro page. Evaluación `src/pages/blog.astro`:

```astro
---
import { getCollection } from 'astro:content';

const blogPosts = await getCollection('blog');
---

<html lang="en">
  <head>
    <title>My Blog</title>
  </head>
  <body>
    <h1>Blog Posts</h1>
    {blogPosts.map(post => (
      <article>
        <h2>{post.data.title}</h2>
        <p>{post.data.description}</p>
        <time>{post.data.pubDate.toDateString()}</time>
      </article>
    ))}
  </body>
</html>
```

## Key Points

- **Automatic Discovery**: Astro finds all `.md` files in your collection directories
- **Type Safety**: The schema validates your frontmatter at build time
- **Easy Querying**: Use `getCollection()` to retrieve all entries from a collection
- **Data Access**: Content metadata is available through `post.data`, content through `post.body`

Your Content Collection is now ready! In the next lesson, we'll explore how to create more complex schemas with validation and custom data types.

```yaml
---
// Import content utilities
import { getCollection } from 'astro:content';
import Layout from '@/layouts/BaseLayout.astro';
import BlogCard from '@/components/BlogCard.astro';

const posts = await getCollection('blog');
---
```

```html
<Layout>
  <section class="py-12">
    <h1 class="text-2xl font-bold text-primary">Latest Posts</h1>
    <ul class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
      {posts.map((post) => (
      <li>
        <BlogCard title={post.data.title} description={post.data.description}
        date={post.data.pubDate} href={`/blog/${post.id}`} />
      </li>
      ))}
    </ul>
  </section>
</Layout>

<style>
  section {
    --tw-prose-body: theme("colors.zinc.800");
    background: theme("colors.white");
  }

  @media (prefers-color-scheme: dark) {
    section {
      --tw-prose-body: theme("colors.zinc.100");
      background: theme("colors.zinc.900");
    }
  }
</style>
```
